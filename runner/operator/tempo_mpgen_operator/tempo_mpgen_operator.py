import uuid
import re
import os
from django.db.models import Q
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from notifier.events import OperatorRequestEvent
from notifier.models import JobGroup
from notifier.tasks import send_notification
from file_system.repository.file_repository import FileRepository
from .construct_tempo_pair import construct_tempo_jobs
from .bin.pair_request import compile_pairs
from .bin.make_sample import build_sample
from .bin.create_tempo_files import create_mapping, create_pairing, create_tempo_tracker_example, get_abnormal_pairing
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
        Very similar to build_assay_query, but "metadata__recipe"
        can't be sent as a value, so had to make a semi-redundant function
        """
        data = self.get_recipes()
        data_query_set = [Q(metadata__recipe=value) for value in set(data)]
        query = data_query_set.pop()
        for item in data_query_set:
            query |= item
        return query


    def build_assay_query(self):
        """
        Build complex Q object assay query from given data
        Only does OR queries, as seen in line
           query |= item
        Very similar to build_recipe_query, but "metadata__baitSet"
        can't be sent as a value, so had to make a semi-redundant function
        """
        data = self.get_assays()
        data_query_set = [Q(metadata__baitSet=value) for value in set(data)]
        query = data_query_set.pop()
        for item in data_query_set:
            query |= item
        return query


    def get_jobs(self):
        recipe_query = self.build_recipe_query()
        assay_query = self.build_assay_query()
        igocomplete_query = Q(metadata__igocomplete=True)
        q = recipe_query & assay_query & igocomplete_query
        files = FileRepository.all()
        files = FileRepository.filter(queryset=files, q=q)

        data = list()
        for f in files:
            sample = dict()
            sample['id'] = f.file.id
            sample['path'] = f.file.path
            sample['file_name'] = f.file.file_name
            sample['metadata'] = f.metadata
            data.append(sample)

        self.send_message("""
            Querying database for the following recipes:
                {recipes}

            Querying database for the following assays/bait sets:
                {assays}
            """.format(recipes="\t\n".join(self.get_recipes()),
                       assays="\t\n".join(self.get_assays()))
                      )

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
        # tempo_inputs is a paired list, error_samples are just samples that were processed
        # through remove_with_caveats()

        self.create_tracker_file(tempo_inputs)
        self.generate_sample_formatting_errors_file(tempo_inputs, samples, error_samples)
        self.create_mapping_file(tempo_inputs, error_samples)
        self.create_pairing_file(tempo_inputs, error_samples)

        return [], []


    def create_pairing_file(self, tempo_inputs, error_samples):
        """
        Outputs valid paired samples and errors associated with those that couldn't be paired
        """
        cleaned_inputs, duped_pairs = self.clean_inputs(tempo_inputs, error_samples)
        self.report_unpaired_samples_with_error(tempo_inputs)
        self.report_duplicated_pairing(duped_pairs)
        pairing = create_pairing(cleaned_inputs)

        header = "NORMAL_ID\tTUMOR_ID\n"
        sample_pairing = header + pairing

        pairing_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_pairing.txt', sample_pairing).to_dict()
        send_notification.delay(pairing_file_event)

        self.write_to_file("sample_pairing.txt", sample_pairing)


    def write_to_file(self,fname,s):
        OUTPUT_DIR = "/juno/work/tempo/voyager/"
        output = os.path.join(OUTPUT_DIR, fname)
        open(output,"w").write(s)


    def report_duplicated_pairing(self, duped_pairs):
        dupe_errors = list()
        dupe_errors_unformatted = list()
        dupe_errors_unformatted.append("Tumor Sample Name\tTumor IGO Sample ID\tNormal Sample Name\tNormal Sample ID\n") # header

        for pair in duped_pairs:
                normal_sample = pair['normal_sample']
                normal_sample_name = normal_sample['sample_name']
                normal_igo_id = normal_sample['sample_id']
                tumor_sample = pair['tumor_sample']
                tumor_sample_name = tumor_sample['sample_name']
                tumor_igo_id = tumor_sample['sample_id']
                line = "%s\t%s\t%s\t%s\n" % (tumor_sample_name, tumor_igo_id, normal_sample_name, normal_igo_id)
                dupe_errors.append( "|" + line.replace("\t", "|") + " |")
                dupe_errors_unformatted.append(line)

        self.send_message("""
        Number of samples with duplication pairing: {num_dupe_errors}

        Samples with pairing errors (also see file error_pairing_dupes.txt):

        | Tumor Sample Name | Tumor IGO Sample ID | Normal Sample Name | Normal Sample ID |
        {dupe_errors}
        """.format(
            num_dupe_errors=str(len(dupe_errors)),
            dupe_errors="\n".join(dupe_errors)
            )
        )

        sample_dupe_errors_event = UploadAttachmentEvent(self.job_group_id, 'error_pairing_dupes.txt', "".join(dupe_errors_unformatted)).to_dict()
        send_notification.delay(sample_dupe_errors_event)

        self.write_to_file("error_pairing_dupes.txt", "".join(dupe_errors_unformatted))


    def report_unpaired_samples_with_error(self, data):
        pair_with_errors = get_abnormal_pairing(data)
        pairing = pair_with_errors.split("\n")
        pairing_errors = list()
        pairing_errors_unformatted = list()

        for line in pairing:
            if "noNormal" in line:
                pairing_errors.append("| " + line.replace("\t"," | ") + " |")
                pairing_errors_unformatted.append(line + "\n")

        self.send_message("""
        Number of samples with pairing errors: {num_pairing_errors}
        Samples with pairing errors (also see file error_unpaired_samples.txt):
        | Error | CMO Sample Name |
        {pairing_errors}
        """.format(num_pairing_errors=str(len(pairing_errors)),
            pairing_errors="\n".join(pairing_errors)))

        sample_pairing_errors_event = UploadAttachmentEvent(self.job_group_id, 'error_unpaired_samples.txt', "".join(pairing_errors_unformatted)).to_dict()
        send_notification.delay(sample_pairing_errors_event)

        self.write_to_file("error_unpaired_samples.txt", "".join(pairing_errors_unformatted))


    def create_mapping_file(self, tempo_inputs, error_samples):
        cleaned_inputs, duped_pairs = self.clean_inputs(tempo_inputs, error_samples)
        header = "SAMPLE\tTARGET\tFASTQ_PE1\tFASTQ_PE2\tNUM_OF_PAIRS\n"
        sample_mapping = header + create_mapping(cleaned_inputs)
        mapping_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_mapping.txt', sample_mapping).to_dict()
        send_notification.delay(mapping_file_event)
        self.write_to_file("sample_mapping.txt", sample_mapping)


    def clean_inputs(self, tempo_inputs, error_samples):
        """
        Removes samples that don't have valid cmo sample names

        Goes for both sample types (tumor or normal)
        """
        error_sample_set = set()
        for sample in error_samples:
            error_sample_set.add(sample['sample_name'])

        dupe_pairs = list()

        clean_pair = list()
        for pair in tempo_inputs:
            normal = pair["normal_sample"]
            tumor = pair["tumor_sample"]
            if normal['sample_name'] not in error_sample_set or tumor['sample_name'] not in error_sample_set:
                if normal['sample_name'] == tumor['sample_name']:
                    dupe_pairs.append(pair)
                elif self.is_cleaned_cmo_sample_name_format(normal['sample_name'], normal['specimen_type']) and self.is_cleaned_cmo_sample_name_format(tumor['sample_name'], tumor['specimen_type']):
                    clean_pair.append(pair)
        return clean_pair, dupe_pairs


    def generate_sample_formatting_errors_file(self, tempo_inputs, samples, error_samples):
        number_of_inputs = len(tempo_inputs)
        s = list()
        unformatted_s = list()
        unformatted_s.append("IGO Sample ID\tSample Name / Error\tPatient ID\tSpecimen Type\n")
        for sample in error_samples:
            s.append("| " + sample['sample_id']  + " | " + sample['sample_name'] + " |" + sample['patient_id'] + " |" + sample['specimen_type'] + " |")
            unformatted_s.append(sample['sample_id']  + "\t" + sample['sample_name'] + "\t" + sample['patient_id'] + "\t" + sample['specimen_type'] + "\n")

        msg = """
        Number of samples (both tumor and normal): {num_samples}
        Number of samples with error: {number_of_errors}

        Error samples (also see error_sample_formatting.txt):
        | IGO Sample ID | Sample Name / Error | Patient ID | Specimen Type |
        {error_sample_names}
        """

        msg = msg.format(num_samples=str(len(samples)),
                number_valid_inputs=str(number_of_inputs),
                number_of_errors=str(len(error_samples)),
                error_sample_names='\n'.join(s))

        self.send_message(msg)

        sample_errors_event = UploadAttachmentEvent(self.job_group_id, 'error_sample_formatting.txt', "".join(unformatted_s)).to_dict()
        send_notification.delay(sample_errors_event)

        self.write_to_file("error_sample_formatting.txt", "".join(unformatted_s))


    def is_cleaned_cmo_sample_name_format(self, sample_name, specimen_type):
        """
        This needs to be refactored
    
        A similar function exists in bin/make_sample.py, but the sample pattern is different
        In that one, it is still the old C-* format; this one checks cleaned, already built
        sample format s_C-*

        This is because of changing requirements an wasn't in the original plan
        """
        sample_pattern = re.compile(r's_C_\w{6}_\w{4}_\w')
        if "cellline" in specimen_type.lower() or bool(sample_pattern.match(sample_name)):
            return True
        return False


    def create_tracker_file(self, tempo_inputs):
        sample_tracker = create_tempo_tracker_example(tempo_inputs)
        tracker_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_tracker.txt', sample_tracker).to_dict()
        send_notification.delay(tracker_file_event)
        self.write_to_file("sample_tracker.txt", sample_tracker)


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
