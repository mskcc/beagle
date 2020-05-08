import uuid
from django.db.models import Q
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from notifier.events import OperatorRequestEvent
from notifier.models import JobGroup
from notifier.tasks import send_notification
from .construct_tempo_pair import construct_tempo_jobs
from .bin.pair_request import compile_pairs
from .bin.make_sample import build_sample, is_cmo_sample_name_format
from .bin.create_tempo_files import create_mapping, create_pairing, create_tempo_tracker_example
from notifier.events import UploadAttachmentEvent
import json

from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
notifier = JiraEventHandler()


class TempoMPGenOperator(Operator):
    def build_recipe_query(self):
        """
        Build complex Q object assay query from given data
        Only does OR queries, as seen in line
           query |= item
        Very similar to build_assay_query, but "filemetadata__metadata__recipe"
        can't be sent as a value, so had to make a semi-redundant function
        """
        data = self.get_recipes()
        data_query_set = [Q(filemetadata__metadata__recipe=value) for value in set(data)]
        query = data_query_set.pop()
        for item in data_query_set:
            query |= item
        return query


    def build_assay_query(self):
        """
        Build complex Q object assay query from given data
        Only does OR queries, as seen in line
           query |= item
        Very similar to build_recipe_query, but "filemetadata__metadata__baitSet"
        can't be sent as a value, so had to make a semi-redundant function
        """
        data = self.get_assays()
        data_query_set = [Q(filemetadata__metadata__baitSet=value) for value in set(data)]
        query = data_query_set.pop()
        for item in data_query_set:
            query |= item
        return query


    def get_jobs(self):
        recipe_query = self.build_recipe_query()
        assay_query = self.build_assay_query()
        igocomplete_query = Q(filemetadata__metadata__igocomplete=True)
        files = self.files.filter(recipe_query & assay_query & igocomplete_query).all()

        self.send_message("""
            Querying database for the following recipes:
                {recipes}

            Querying database for the following assays/bait sets:
                {assays}
            """.format(recipes="\t\n".join(self.get_recipes()),
                       assays="\t\n".join(self.get_assays()))
                      )

        data = list()
        for file in files:
            sample = dict()
            sample['id'] = file.id
            sample['path'] = file.path
            sample['file_name'] = file.file_name
            sample['metadata'] = file.filemetadata_set.first().metadata
            data.append(sample)

        samples = list()
        # group by igoId
        sample_id_group = dict()
        for sample in data:
            sample_id = sample['metadata']['sampleId']
            if sample_id not in sample_id_group:
                sample_id_group[sample_id] = list()
            sample_id_group[sample_id].append(sample)

        for sample_id in sample_id_group:
            samples.append(build_sample(sample_id_group[sample_id]))

        tempo_inputs, error_samples = construct_tempo_jobs(samples)

        self.create_tracker_file(tempo_inputs)
        self.generate_sample_formatting_errors_file(tempo_inputs, samples, error_samples)
        self.create_mapping_file(tempo_inputs, error_samples)
        self.create_pairing_file(tempo_inputs, error_samples)

        return [], []


    def create_pairing_file(self, tempo_inputs, error_samples):
        """
        Outputs valid paired samples and errors associated with those that couldn't be paired
        """
        pairing, unpaired_errors = create_pairing(tempo_inputs)
        pairing_errors = list()
        pairing_errors_unformatted = list()

        for pair in unpaired_errors:
                error_sample = pair['normal_sample']
                error_msg = error_sample['sample_name']
                tumor_sample = pair['tumor_sample']
                tumor_sample_name = tumor_sample['sample_name']
                tumor_patient_id = tumor_sample['patient_id']
                igo_sample_id = tumor_sample['sample_id']
                line = "%s\t%s\t%s\t%s\n" % (tumor_sample_name, igo_sample_id, tumor_patient_id, error_msg)
                pairing_errors.append( "|" + line.replace("\t", "|") + "|")
                pairing_errors_unformatted.append(line)

        self.send_message("""
        Number of samples with pairing errors: {num_pairing_errors}

        Samples with pairing errors (also see file error_unpaired_samples.txt):

        | Sample Name | IGO Sample ID | Patient ID | Error Message |
        {pairing_errors}
        """.format(
            num_pairing_errors=str(len(pairing_errors)),
            pairing_errors="\n".join(pairing_errors)
            )
        )

        sample_pairing_errors_event = UploadAttachmentEvent(self.job_group_id, 'error_unpaired_samples.txt', "".join(pairing_errors_unformatted)).to_dict()
        send_notification.delay(sample_pairing_errors_event)
 
        header = "NORMAL_ID\tTUMOR_ID\n"
        sample_pairing = header + pairing

        pairing_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_pairing.txt', sample_pairing).to_dict()
        send_notification.delay(pairing_file_event)


    def create_mapping_file(self, tempo_inputs, error_samples):
        cleaned_inputs = self.clean_inputs(tempo_inputs, error_samples)
        header = "SAMPLE\tTARGET\tFASTQ_PE1\tFASTQ_PE2\tNUM_OF_PAIRS\n"
        sample_mapping = header + create_mapping(cleaned_inputs)
        mapping_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_mapping.txt', sample_mapping).to_dict()
        send_notification.delay(mapping_file_event)


    def clean_inputs(self, tempo_inputs, error_samples):
        """
        Removes samples that don't have valid cmo sample names

        Goes for both sample types (tumor or normal)
        """
        clean_pair = list()
        for pair in tempo_inputs:
            normal = pair["normal_sample"]
            tumor = pair["tumor_sample"]            
            if is_cmo_sample_name_format(normal['sample_name'], normal['specimen_type']) and is_cmo_sample_name_format(tumor['sample_name'], tumor['specimen_type']):
                clean_pair.append(pair)
        return clean_pair


    def generate_sample_formatting_errors_file(self, tempo_inputs, samples, error_samples):
        number_of_inputs = len(tempo_inputs)
        s = list()
        unformatted_s = list()
        for sample in error_samples:
            s.append("| " + sample['sample_id']  + " | " + sample['sample_name'] + " |")
            unformatted_s.append(sample['sample_id']  + "\t" + sample['sample_name'] + "\n")

        msg = """
        Number of samples (both tumor and normal): {num_samples}
        Number of samples with error: {number_of_errors}

        Error samples (also see error_sample_formatting.txt):
        | IGO Sample ID | Sample Name / Error |
        {error_sample_names}
        """

        msg = msg.format(num_samples=str(len(samples)),
                number_valid_inputs=str(number_of_inputs),
                number_of_errors=str(len(error_samples)),
                error_sample_names='\n'.join(s))

        self.send_message(msg)

        sample_errors_event = UploadAttachmentEvent(self.job_group_id, 'error_sample_formatting.txt', "".join(unformatted_s)).to_dict()
        send_notification.delay(sample_errors_event)


    def create_tracker_file(self, tempo_inputs):
        sample_tracker = create_tempo_tracker_example(tempo_inputs)
        tracker_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_tracker.txt', sample_tracker).to_dict()
        send_notification.delay(tracker_file_event)


    def send_message(self, msg):
        event = OperatorRequestEvent(self.job_group_id, msg)
        e = event.to_dict()
        send_notification.delay(e)


    def get_recipes(self):
        recipe = [ 
            "Agilent_v4_51MB_Human",
            "IDT_Exome_v1_FP",
            "WholeExomeSequencing",
        ]
        return recipe


    def get_assays(self):
        assays = [
        "Agilent_v4_51MB_Human_hg19_BAITS",
        "IDT_Exome_v1_FP_b37_baits",
        "IDT_Exome_v1_FP_BAITS",
        "SureSelect-All-Exon-V4-hg19"
        ]
        return assays
