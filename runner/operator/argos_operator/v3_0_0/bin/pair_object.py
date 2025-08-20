# PairObj contain one tumor/normal pair
#
# tumor and normal are sample objects, either
#   SampleIGO, SamplePooledNormal, or SampleDMP


class PairObj:
    def __init__(self, tumor, normal):
        self.tumor = tumor
        self.normal = normal

    def __repr__(self):
        s = f"Pair Obj: Tumor {self.tumor.sample_name}, Normal {self.normal.sample_name}"
        return s
