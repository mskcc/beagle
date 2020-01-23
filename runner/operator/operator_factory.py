from .tempo_operator import TempoOperator
from .roslin_operator import RoslinOperator
from .access_operator import AccessOperator


class OperatorFactory(object):

    operators = [TempoOperator, RoslinOperator, AccessOperator]

    @classmethod
    def get_by_class_name(class_name):
        if class_name not in OperatorFactory.operators:
            raise Exception("Invalid pipeline")

        return OperatorFactory.operators[class_name](request_id)

    def factory(pipeline, request_id):
        if pipeline in ('tempo',):
            return TempoOperator(request_id)
        elif pipeline in ('roslin',):
            return RoslinOperator(request_id)
        elif pipeline in ('access',):
            return AccessOperator(request_id)
        else:
            raise Exception("Invalid pipeline")
    factory = staticmethod(factory)
