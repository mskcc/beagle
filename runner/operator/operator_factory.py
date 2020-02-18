from .tempo_operator import TempoOperator
from .roslin_operator import RoslinOperator
from .access_operator import AccessOperator
from .roslin_qc_operator import RoslinQcOperator

class OperatorFactory(object):

    operators = {
        "TempoOperator": TempoOperator,
        "RoslinOperator": RoslinOperator,
        "AccessOperator": AccessOperator,
        "RoslinQcOperator": RoslinQcOperator
    }

    def get_by_class_name(class_name, request_id):
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
        elif pipeline in ('roslin-qc',):
            return RoslinQcOperator(request_id)
        else:
            raise Exception("Invalid pipeline")
    factory = staticmethod(factory)
    get_by_class_name = staticmethod(get_by_class_name)
