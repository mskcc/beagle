import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from notifier.events import OperatorRequestEvent
from notifier.models import JobGroup
from notifier.tasks import send_notification
from .construct_tempo_pair import construct_tempo_jobs
from .bin.pair_request import compile_pairs
from .bin.make_sample import build_sample
from .bin.create_tempo_files import create_mapping, create_pairing, create_tempo_tracker_example
from notifier.events import UploadAttachmentEvent
import json

from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
notifier = JiraEventHandler()


class TempoMPGenOperator(Operator):
    def get_jobs(self):
        request_id = "09687_N"
        files = self.files.filter(filemetadata__metadata__requestId=request_id, filemetadata__metadata__igocomplete=True).all()

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
        number_of_inputs = len(tempo_inputs)

        s = list()
        for sample in error_samples:
            s.append(sample['metadata']['sampleId'])

        msg = """
        Request ID: {request_id}
        Number of samples: {num_samples}
        Number of valid inputs: {number_valid_inputs}
        Number of samples with error: {number_of_errors}

        Error samples: {error_sample_names}
        """

        msg = msg.format(request_id=request_id,
                num_samples=str(len(samples)),
                number_valid_inputs=str(number_of_inputs),
                number_of_errors=str(len(error_samples)),
                error_sample_names=', '.join(s))

        event = OperatorRequestEvent(self.job_group_id, msg)

        e = event.to_dict()
        send_notification.delay(e)

#        f = open("/home/bolipatc/ops/test_tempo/%s.json" % (request_id), 'w')
#        sample_mapping = json.dump(tempo_inputs, f)
        sample_mapping = create_mapping(tempo_inputs)
        mapping_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_mapping.txt', sample_mapping).to_dict()
        send_notification.delay(mapping_file_event)

        sample_pairing = create_pairing(tempo_inputs)
        pairing_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_pairing.txt', sample_pairing).to_dict()
        send_notification.delay(pairing_file_event)

        sample_tracker = create_tempo_tracker_example(tempo_inputs)
        tracker_file_event = UploadAttachmentEvent(self.job_group_id, 'sample_tracker.txt', sample_tracker).to_dict()
        send_notification.delay(tracker_file_event)

        return [], []
