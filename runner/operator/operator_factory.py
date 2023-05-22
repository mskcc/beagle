import importlib
from beagle_etl.models import Operator
from runner.models import Pipeline


class OperatorFactory(object):
    @classmethod
    def get_operators(cls):
        operators = Operator.objects.all()
        all_operators = dict()
        for operator in operators:
            if operator.slug not in all_operators:
                all_operators[operator.slug] = []
            mod_name, func_name = operator.class_name.rsplit(".", 1)
            mod = importlib.import_module(mod_name)
            func = getattr(mod, func_name)
            operator_value = {"version": operator.version, "operator": func}
            all_operators[operator.slug].append(operator_value)
        return all_operators

    @staticmethod
    def get_by_model(model, **kwargs):
        mod_name, func_name = model.class_name.rsplit(".", 1)
        mod = importlib.import_module(mod_name)
        operator_class = getattr(mod, func_name)

        from pprint import pprint
        for operator_pipeline in model.pipeline_set.all():
            pprint("pipeline_version is " + operator_pipeline.version)
        if "pipeline_version" in kwargs:
            pipeline_version = kwargs.get("pipeline_version")
            pipeline_exists = any([
                p_version_bool in operator_pipeline.version for operator_pipeline in model.pipeline_set.all()
            ])
            if not pipeline_exists:
                raise PipelineNotFoundError(
                    "Version {pipeline_version} is not found for Pipelines associated with Operator {model_name}"
                .format(pipeline_version=pipeline_version, model_name=mod_name))
        return operator_class(model, **kwargs)
