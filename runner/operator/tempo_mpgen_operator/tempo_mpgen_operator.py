import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from notifier.events import TempoMPGenEvent
from notifier.models import JobGroup
from notifier.tasks import send_notification
from .construct_tempo_pair import construct_tempo_jobs
from .bin.pair_request import compile_pairs
from .bin.make_sample import build_sample
import json

from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
notifier = JiraEventHandler()


class TempoMPGenOperator(Operator):
    def get_jobs(self):
        files = self.files.filter(filemetadata__metadata__requestId=self.request_id, filemetadata__metadata__igocomplete=True).all()
        tempo_jobs = list()
        operator_run_id = "TMPPB_Run_Fake"

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

        msg = msg.format(request_id=self.request_id,
                num_samples=str(len(samples)),
                number_valid_inputs=str(number_of_inputs),
                number_of_errors=str(len(error_samples)),
                error_sample_names=', '.join(s))

        event = TempoMPGenEvent(self.job_group_id, msg)

        e = event.to_dict()
        send_notification.delay(e)

        f = open("/home/bolipatc/ops/test_tempo/%s.json" % (self.request_id), 'w')
        json.dump(tempo_inputs, f)

        return tempo_jobs
