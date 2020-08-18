from .argos_operator.v1_0_0 import ArgosOperator as argos_operator_v1_0_0
from .copy_outputs_operator.v1_0_0 import CopyOutputsOperator as copy_outputs_operator_v1_0_0
from .argos_qc_operator.v1_0_0 import ArgosQcOperator as argos_qc_operator_v1_0_0
from .tempo_operator.v1_0_0 import TempoOperator as tempo_operator_v1_0_0
from .access_operator.v1_0_0 import AccessOperator as access_operator_v1_0_0
from .helix_filters.v20_07_1 import HelixFiltersOperator as helix_filters_operator_v20_07_1
from .aion.v1_0_0 import AionOperator as aion_operator_v1_0_0
from .access.v1_0_0.fastq_to_bam import AccessFastqToBamOperator as AccessFastqToBamOperator_v1_0_0


class OperatorFactory(object):

    operators = {
        "TempoOperator": [
            {"version": "v1.0.0", "latest": True, "operator": tempo_operator_v1_0_0}
        ],
        "ArgosOperator": [
            {"version": "v1.0.0", "latest": True, "operator": argos_operator_v1_0_0}
        ],
        "AccessOperator": [
            {"version": "v1.0.0", "latest": True, "operator": access_operator_v1_0_0}
        ],
        "ArgosQcOperator": [
            {"version": "v1.0.0", "latest": True, "operator": argos_qc_operator_v1_0_0}
        ],
        "CopyOutputsOperator": [
            {"version": "v1.0.0", "latest": True, "operator": copy_outputs_operator_v1_0_0}
        ],
        "AccessFastqToBamOperator": [
            {"version": "v1.0.0", "latest": True, "operator": AccessFastqToBamOperator_v1_0_0}
        ],
        "HelixFiltersOperator": [
            {"version": "v20.07.1", "latest": True, "operator": helix_filters_operator_v20_07_1}
        ],
        "AionOperator": [
            {"version": "v1.0.0", "latest": True, "operator": aion_operator_v1_0_0}
        ]
    }

    def get_by_model(model, version=None, **kwargs):
        if model.class_name not in OperatorFactory.operators:
            raise Exception("No operator matching {}" % model.class_name)
        operator_list = OperatorFactory.operators[model.class_name]
        latest_operator = None
        version_operator = None
        for single_operator in operator_list:
            if single_operator['version'] == version:
                if not version_operator:
                    version_operator = single_operator['operator']
                else:
                    raise Exception("Cannot have multiple " + str(version) + " version operators for " + str(model.class_name))
            if single_operator['latest']:
                if not latest_operator:
                    latest_operator = single_operator['operator']
                else:
                    raise Exception("Cannot have multiple latest operators for " + str(model.class_name))
        if not latest_operator:
            raise Exception("No latest version specified for " + str(model.class_name))
        if version and not version_operator:
            raise Exception("Could not find version " + str(version) + " of operator " + str(model.class_name))

        if version_operator:
            return version_operator(model, **kwargs)
        if latest_operator:
            return latest_operator(model, **kwargs)

    get_by_model = staticmethod(get_by_model)
