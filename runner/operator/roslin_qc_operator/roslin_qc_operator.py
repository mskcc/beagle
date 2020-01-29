from runner.operator.operator import Operator

class RoslinQcOperator(Operator):
    """
    Operator for Roslin QC pipeline
    """

    def __init__(self, request_id):
        Operator.__init__(self, 'roslin-qc', request_id)

    def get_pipeline_id(self):
        # TODO: replace this with the hard-coded pipeline id that will be created in database fixture
        return "replace-this-with-pipeline-id"

    def get_jobs(self):
        return([])
