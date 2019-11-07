from runner.operator.tempo_operator.tempo_operator import TempoOperator


class OperatorFactory(object):

    def factory(pipeline, request_id):
        if pipeline in ('tempo',):
            return TempoOperator(request_id)
        elif pipeline in ('roslin',):
            # TODO: Allan uncoment return statement when you implement RoslinOperator
            #return RoslinOperator(request_id)
            raise Exception("Roslin operator still not implemented")
        else:
            raise Exception("Invalid pipeline")
    factory = staticmethod(factory)
