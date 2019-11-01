from runner.operator.tempo_operator.tempo_operator import TempoOperator


class OperatorFactory(object):

    def factory(pipeline, request_id):
        if pipeline:
            return TempoOperator(request_id)
        else:
            raise Exception("Invalid job")
    factory = staticmethod(factory)
