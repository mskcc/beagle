import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from .construct_argos_pair import construct_argos_jobs
from runner.models import Pipeline
from .bin.pair_request import compile_pairs
from .bin.make_sample import build_sample
from notifier.events import UploadAttachmentEvent, OperatorRequestEvent
from notifier.tasks import send_notification
from notifier.helper import generate_sample_data_content
from runner.run.processors.file_processor import FileProcessor
from file_system.repository.file_repository import FileRepository


class ArgosOperator(Operator):
    def get_jobs(self):
        files = FileRepository.filter(queryset=self.files,
                                      metadata={'requestId': self.request_id,
                                                'igocomplete': True})
        argos_jobs = list()

        data = list()
        for f in files:
            sample = dict()
            sample['id'] = f.file.id
            sample['path'] = f.file.path
            sample['file_name'] = f.file.file_name
            sample['metadata'] = f.metadata
            data.append(sample)

        files = list()
        samples = list()
        # group by igoId
        igo_id_group = dict()
        for sample in data:
            igo_id = sample['metadata']['sampleId']
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            samples.append(build_sample(igo_id_group[igo_id]))

        argos_inputs, error_samples = construct_argos_jobs(samples)
        number_of_inputs = len(argos_inputs)

        sample_pairing = ""
        sample_mapping = ""
        pipeline = self.get_pipeline_id()

        try:
            pipeline_obj = Pipeline.objects.get(id=pipeline)
        except Pipeline.DoesNotExist:
            pass

        for i, job in enumerate(argos_inputs):
            tumor_sample_name = job['pair'][0]['ID']
            for p in job['pair'][0]['R1']:
                sample_mapping += "\t".join(
                    [tumor_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))
            for p in job['pair'][0]['R2']:
                sample_mapping += "\t".join(
                    [tumor_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))
            for p in job['pair'][0]['zR1']:
                sample_mapping += "\t".join(
                    [tumor_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))
            for p in job['pair'][0]['zR2']:
                sample_mapping += "\t".join(
                    [tumor_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))

            normal_sample_name = job['pair'][1]['ID']
            for p in job['pair'][1]['R1']:
                sample_mapping += "\t".join(
                    [normal_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))
            for p in job['pair'][1]['R2']:
                sample_mapping += "\t".join(
                    [normal_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))
            for p in job['pair'][1]['zR1']:
                sample_mapping += "\t".join(
                    [normal_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))
            for p in job['pair'][1]['zR2']:
                sample_mapping += "\t".join(
                    [normal_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))

            for p in job['pair'][1]['bam']:
                sample_mapping += "\t".join(
                    [normal_sample_name, FileProcessor.parse_path_from_uri(p['location'])]) + "\n"
                files.append(FileProcessor.parse_path_from_uri(p['location']))

            name = "ARGOS %s, %i of %i" % (self.request_id, i + 1, number_of_inputs)
            assay = job['assay']
            pi = job['pi']
            pi_email = job['pi_email']

            sample_pairing += "\t".join([normal_sample_name, tumor_sample_name]) + "\n"

            argos_jobs.append((APIRunCreateSerializer(
                data={'app': pipeline, 'inputs': argos_inputs, 'name': name,
                      'tags': {'requestId': self.request_id,
                          'sampleNameTumor': tumor_sample_name,
                          'sampleNameNormal': normal_sample_name,
                          'labHeadName': pi,
                          'labHeadEmail': pi_email}}), job))

        operator_run_summary = UploadAttachmentEvent(self.job_group_id, 'sample_pairing.txt', sample_pairing).to_dict()
        send_notification.delay(operator_run_summary)

        mapping_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_mapping.txt', sample_mapping).to_dict()
        send_notification.delay(mapping_file_event)

        data_clinical = generate_sample_data_content(files, pipeline_name=pipeline_obj.name,
                                                     pipeline_github=pipeline_obj.github,
                                                     pipeline_version=pipeline_obj.version)
        sample_data_clinical_event = UploadAttachmentEvent(self.job_group_id, 'sample_data_clinical.txt',
                                                           data_clinical).to_dict()
        send_notification.delay(sample_data_clinical_event)

        self.evaluate_sample_errors(error_samples)
        self.summarize_pairing_info(argos_inputs)

        return argos_jobs

    def summarize_pairing_info(self, argos_inputs):
        num_pairs = len(argos_inputs['pair'])
        num_dmp_normals = 0
        num_pooled_normals = 0
        num_outside_req = 0
        num_within_req = 0
        other_requests_matched = list()
        for i, job in enumerate(argos_inputs):
            tumor = job['pair'][0]
            normal = job['pair'][1]
            req_t = tumor['request_id']
            req_n = normal['request_id']
            specimen_type_n = normal['specimen_type']
            if specimen_type_n.lower() in "DMP Normal".lower():
                num_dmp_normals += 1
            elif specimen_type_n.lower() in "Pooled Normal".lower():
                num_pooled_normals += 1
            elif req_t.strip() != req_n.strip():
                num_outside_req += 1
                data = dict()
                data['sample_name'] = tumor['SM']
                data['matched_sample_name'] = normal['SM']
                data['normal_request'] = req_n
                other_requests_matched.append(data)
            else:
                num_within_req += 1
        s = "Number of pairs: %i\n\n" % num_pairs
        s += "%i samples matched with DMP Normal\n" % num_dmp_normals
        s += "%i samples matched with pooled normals\n" % num_pooled_normals
        s += "%i samples matched with normal from different request" % num_outside_req

        if num_outside_req > 0:
            s += "\n\nMatched samples fom different request\n"
            s += "| Sample Name | Matched Normal | Request Normal |\n"
            for i in other_requests_matched:
                sample_name = i['sample_name']
                matched_sample = i['matched_sample_name']
                normal_request = i['normal_request']
                s += "| %s | %s | %s |\n" % (sample_name, matched_sample, normal_request)

        self.send_message(s)


    def send_message(self, msg):
        event = OperatorRequestEvent(self.job_group_id, msg)
        e = event.to_dict()
        send_notification.delay(e)


    def evaluate_sample_errors(self, error_samples):
        s = list()
        unformatted_s = list()
        unformatted_s.append("IGO Sample ID\tSample Name / Error\tPatient ID\tSpecimen Type\n")
        for sample in error_samples:
            s.append("| " + sample['sample_id']  + " | " + sample['sample_name'] + " |" + sample['patient_id'] + " |" + sample['specimen_type'] + " |")
            unformatted_s.append(sample['sample_id']  + "\t" + sample['sample_name'] + "\t" + sample['patient_id'] + "\t" + sample['specimen_type'] + "\n")

        msg = """
        Number of samples with error: {number_of_errors}

        Error samples (also see error_sample_formatting.txt):
        | IGO Sample ID | Sample Name / Error | Patient ID | Specimen Type |
        {error_sample_names}
        """

        msg = msg.format(
                number_of_errors=str(len(error_samples)),
                error_sample_names='\n'.join(s))

        self.send_message(msg)

        sample_errors_event = UploadAttachmentEvent(self.job_group_id, 'error_sample_formatting.txt', "".join(unformatted_s)).to_dict()
        send_notification.delay(sample_errors_event)
