# PairsObj contains a list of PairObj
#
# Will generate data clinical, mapping, pairing strings


class PairsObj:
    def __init__(self):
        self.pairs = list()

    def add_pair(self, pair):
        self.pairs.append(pair)

    def get_pairs(self):
        return self.pairs

    def generate_pairing(self):
        sample_pairing = ""
        from pprint import pprint

        for pair in self.pairs:
            tumor_sample_name = pair.tumor.sample_name
            normal_sample_name = pair.normal.sample_name
            sample_pairing += "\t".join([normal_sample_name, tumor_sample_name]) + "\n"
        return sample_pairing
