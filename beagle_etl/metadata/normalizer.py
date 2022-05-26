class Normalizer(object):
    def __init__(self, condition, normalizer):
        """
        :param condition: {recipe: IMPACT341, baitSet: IMPACT341}
        :param normalizer: {baitSet: IMPACT341_BAITS}
        """
        self.condition = condition
        self.normalizer = normalizer

    def normalize(self, metadata):
        if self._condition_satisfied(metadata):
            for k, v in self.normalizer.items():
                metadata[k] = v
        return metadata

    def _condition_satisfied(self, metadata):
        for k, v in self.condition.items():
            if metadata.get(k) != v:
                return False
        return True
