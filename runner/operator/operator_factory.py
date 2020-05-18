from .tempo_operator import TempoOperator
from .argos_operator import ArgosOperator
from .access_operator import AccessOperator
from .argos_qc_operator import ArgosQcOperator
from .copy_outputs_operator import CopyOutputsOperator
from .helix_filters import HelixFiltersOperator


class OperatorFactory(object):

    operators = {
        "TempoOperator": TempoOperator,
        "ArgosOperator": ArgosOperator,
        "AccessOperator": AccessOperator,
        "ArgosQcOperator": ArgosQcOperator,
        "CopyOutputsOperator": CopyOutputsOperator,
        "HelixFiltersOperator": HelixFiltersOperator
    }

    def get_by_model(model, **kwargs):
        if model.class_name not in OperatorFactory.operators:
            raise Exception("No operator matching {}" % model.class_name)

        return OperatorFactory.operators[model.class_name](model, **kwargs)

    get_by_model = staticmethod(get_by_model)
