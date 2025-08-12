class Bam:
    """
    Bam class to hold list of bam files
    """

    def __init__(self, file_list):
        self.bams = list()
        for f in file_list:
            self.bams.append(f)


class Fastqs:
    """
    Fastqs class to hold pairs of fastqs

    Does the pairing from a list of files

    The paired bool is True if all of the R1s in file list find a matching R2
    """

    def __init__(self, file_list):
        self.r1 = list()
        self.r2 = list()
        self.paired = True
        self._set_R(file_list)

    def _set_R(self, file_list):
        """
        From the file list, retrieve R1 and R2 fastq files

        Uses _get_fastq_from_list() to find R2 pair.
        """
        r1s = list()
        r2s = list()
        for i in file_list:
            f = i.file
            r = i.metadata["R"]
            if r == "R1":
                r1s.append(f)
            if r == "R2":
                r2s.append(f)
        for f in r1s:
            self.r1.append(f)
            fastq1 = f.path
            expected_r2 = "R2".join(fastq1.rsplit("R1", 1))
            fastq2 = self._get_fastq_from_list(expected_r2, r2s)
            if fastq2:
                self.r2.append(fastq2)
            else:
                print("No fastq R2 found for %s" % f.path)
                self.paired = False

    def __str__(self):
        s = "R1:\n"
        for i in self.r1:
            s += i.path + "\n"
        s += "\nR2:\n"
        for i in self.r2:
            s += i.path + "\n"
        return s

    def _get_fastq_from_list(self, fastq_path, fastq_files):
        """
        Given fastq_path, find it in the list of fastq_files and return
        that File object
        """
        for f in fastq_files:
            fpath = f.path
            if fastq_path == fpath:
                return f
        return None


class FilesObj:
    """
    FilesObj class
    It takes a queryset object containing a list of files, file_list,
    which itself contains File Objects.

    From Files metadata, remove duplicates from fields with best knowledge
    available.

    Sample class contains paired fastqs
    """

    def __init__(self, file_list, file_type):
        if file_type == "bam":
            self.file_type = "bam"
            self.bams = Bam(file_list)
        else:
            self.file_type = "fastq"
            self.fastqs = Fastqs(file_list)

    def get_files(self):
        if self.file_type == "bam":
            d = dict()
            d["bams"] = self.bams
            return d
        else:
            fastqs = dict()
            fastqs["R1"] = list()
            fastqs["R2"] = list()
            for i in self.fastqs.r1:
                fastqs["R1"].append(i.path)
            for i in self.fastqs.r2:
                fastqs["R2"].append(i.path)
            return fastqs
