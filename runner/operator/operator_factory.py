import importlib
from beagle_etl.models import Operator


class OperatorFactory(object):

    @classmethod
    def get_operators(cls):
        operators = Operator.objects.all()
        all_operators = dict()
        for operator in operators:
            if operator.slug not in all_operators:
                all_operators[operator.slug] = []
            mod_name, func_name = operator.class_name.rsplit('.', 1)
            mod = importlib.import_module(mod_name)
            func = getattr(mod, func_name)
            operator_value = {
                "version": operator.version,
                "operator": func
            }
            all_operators[operator.slug].append(operator_value)
        return all_operators

    @staticmethod
    def get_by_model(model, **kwargs):
        mod_name, func_name = model.class_name.rsplit('.', 1)
        mod = importlib.import_module(mod_name)
        operator_class = getattr(mod, func_name)
        return operator_class(model, **kwargs)
