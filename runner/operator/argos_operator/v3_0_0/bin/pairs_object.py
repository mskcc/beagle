# PairsObj contains a list of PairObj


class PairsObj:
    def __init__(self):
        self.pairs = list()

    def add_pair(self, pair):
        self.pairs.append(pair)

    def get_pairs(self):
        return self.pairs
