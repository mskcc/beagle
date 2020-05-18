import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline
from .construct_roslin_pair import construct_roslin_jobs
from .bin.pair_request import compile_pairs
from .bin.make_sample import build_sample
from notifier.events import UploadAttachmentEvent
from notifier.tasks import send_notification
from notifier.helper import generate_sample_data_content_new
from runner.run.processors.file_processor import FileProcessor
from file_system.repository.file_repository import FileRepository


class RoslinOperator(Operator):
    def get_jobs(self):
        # files = self.files.filter(filemetadata__metadata__requestId=self.request_id, filemetadata__metadata__igocomplete=True).all()
        files = FileRepository.filter(queryset=self.files,
                                      metadata={'requestId': self.request_id,
                                                'igocomplete': True})

        roslin_jobs = list()

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

        roslin_inputs, error_samples = construct_roslin_jobs(samples)
        number_of_inputs = len(roslin_inputs)

        sample_pairing = ""
        sample_mapping = ""
        pipeline = self.get_pipeline_id()

        try:
            pipeline_obj = Pipeline.objects.get(id=pipeline)
        except Pipeline.DoesNotExist:
            pass

        for i, job in enumerate(roslin_inputs):
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

            name = "ROSLIN %s, %i of %i" % (self.request_id, i + 1, number_of_inputs)
            assay = job['assay']
            pi = job['pi']
            pi_email = job['pi_email']

            sample_pairing += "\t".join([normal_sample_name, tumor_sample_name]) + "\n"

            roslin_jobs.append((APIRunCreateSerializer(
                data={'app': pipeline, 'inputs': roslin_inputs, 'name': name,
                      'tags': {'requestId': self.request_id,
                          'sampleNameTumor': tumor_sample_name,
                          'sampleNameNormal': normal_sample_name,
                          'labHeadName': pi,
                          'labHeadEmail': pi_email}}), job))

        operator_run_summary = UploadAttachmentEvent(self.job_group_id, 'sample_pairing.txt', sample_pairing).to_dict()
        send_notification.delay(operator_run_summary)

        mapping_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_mapping.txt', sample_mapping).to_dict()
        send_notification.delay(mapping_file_event)

        data_clinical = generate_sample_data_content_new(files, pipeline_name=pipeline_obj.name,
                                                         pipeline_github=pipeline_obj.github,
                                                         pipeline_version=pipeline_obj.version)
        sample_data_clinical_event = UploadAttachmentEvent(self.job_group_id, 'sample_data_clinical.txt',
                                                           data_clinical).to_dict()
        send_notification.delay(sample_data_clinical_event)

        return roslin_jobs
