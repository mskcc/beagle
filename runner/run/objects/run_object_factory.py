from runner.models import Run, ProtocolType
from runner.exceptions import RunCreateException
from runner.run.objects.cwl import CWLRunObject
from runner.run.objects.nextflow import NextflowRunObject


class RunObjectFactory(object):

    @staticmethod
    def from_definition(run_id, inputs):
        try:
            run = Run.objects.get(id=run_id)
        except Run.DoesNotExist:
            raise RunCreateException("Failed to create run. Run with id: %s doesn't exist" % str(run_id))
        if run.run_type == ProtocolType.NEXTFLOW:
            return NextflowRunObject.from_definition(run_id, inputs)
        elif run.run_type == ProtocolType.CWL:
            return CWLRunObject.from_definition(run_id, inputs)
        raise RunCreateException("Failed to create run. Unknown protocol %s" % str(run.run_type))

    @staticmethod
    def from_db(run_id):
        try:
            run = Run.objects.get(id=run_id)
        except Run.DoesNotExist:
            raise RunCreateException("Failed to create run. Run with id: %s doesn't exist" % str(run_id))
        if run.run_type == ProtocolType.NEXTFLOW:
            return NextflowRunObject.from_db(run_id)
        elif run.run_type == ProtocolType.CWL:
            return CWLRunObject.from_db(run_id)
        raise RunCreateException("Failed to create run. Unknown protocol %s" % str(run.run_type))
