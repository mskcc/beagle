from runner.operator.tempo_operator.tempo_operator import TempoOperator


class OperatorFactory(object):

    def factory(pipeline, request_id):
        if pipeline in ('tempo'):
            return TempoOperator(request_id)
        else:
            raise Exception("Invalid pipeline")
    factory = staticmethod(factory)
