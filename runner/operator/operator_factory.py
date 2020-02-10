from .tempo_operator import TempoOperator
from .roslin_operator import RoslinOperator
from .access_operator import AccessOperator


class OperatorFactory(object):

    operators = {
        "TempoOperator": TempoOperator,
        "RoslinOperator": RoslinOperator,
        "AccessOperator": AccessOperator,
    }

    def get_by_model(model, request_id):
        if class_name not in OperatorFactory.operators:
            raise Exception("Invalid pipeline")

        return OperatorFactory.operators[model.class_name](model, request_id)

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
    get_by_model = staticmethod(get_by_model)
