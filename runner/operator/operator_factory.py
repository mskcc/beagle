from .tempo_operator import TempoOperator
from .roslin_operator import RoslinOperator
from .access_operator import AccessOperator
from .roslin_qc_operator import RoslinQcOperator
from .copy_outputs_operator import CopyOutputsOperator

class OperatorFactory(object):

    operators = {
        "TempoOperator": TempoOperator,
        "RoslinOperator": RoslinOperator,
        "AccessOperator": AccessOperator,
        "RoslinQcOperator": RoslinQcOperator,
        "CopyOutputsOperator": CopyOutputsOperator
    }

    def get_by_model(model, **kwargs):
        if model.class_name not in OperatorFactory.operators:
            raise Exception("No operator matching {}" % model.class_name)

        return OperatorFactory.operators[model.class_name](model, **kwargs)

    get_by_model = staticmethod(get_by_model)
