from runner.operator.tempo_operator.tempo_operator import TempoOperator
from runner.operator.roslin_operator.roslin_operator import RoslinOperator


class OperatorFactory(object):

    def factory(pipeline, request_id):
        if pipeline in ('tempo',):
            return TempoOperator(request_id)
        elif pipeline in ('roslin',):
            return RoslinOperator(request_id)
        else:
            raise Exception("Invalid pipeline")
    factory = staticmethod(factory)
