from datetime import datetime as dt
from django.conf import settings
import runner.operator.tempo_mpgen_operator.bin.tempo_sample as tempo_sample


class Patient:
    def __init__(self, patient_id, file_list, pairing={}):
        self.tumor_samples = dict()
        self.normal_samples = dict()
        self.conflict_samples = dict()
        self.sample_pairing = list()
        self.unpaired_samples = list()
        self.pre_pairing = pairing
        self.all_samples = self._get_samples(file_list)
        self._characterize_samples()
        self._pair_samples()

    def _get_samples(self, file_list):
        data = dict()
        for f in file_list:
            metadata = f.metadata
            sample_name = metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]
            if sample_name not in data:
                data[sample_name] = list()
            data[sample_name].append(f)

        samples = dict()
        for sample_name in data:
            sample = data[sample_name]
            samples[sample_name] = tempo_sample.TempoSample(sample_name, sample)
        return samples

    def _characterize_samples(self):
        for sample_name in self.all_samples:
            sample = self.all_samples[sample_name]
            sample_class = sample.sample_class
            if not sample_class:
                self.conflict_samples[sample_name] = sample
            elif isinstance(sample_class, list):
                self.conflict_samples[sample_name] = sample
            elif not sample_name:  # sample name empty
                self.conflict_samples[sample_name] = sample
            elif "sampleNameMalformed" in sample.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]:  # ci tag is no good
                self.conflict_samples[sample_name] = sample
            else:
                if "normal" in sample_class.lower():
                    self.normal_samples[sample_name] = sample
                else:
                    self.tumor_samples[sample_name] = sample

    def _pair_samples(self):
        for tumor_sample_name in self.tumor_samples:
            tumor_sample = self.tumor_samples[tumor_sample_name]
            tumor_cmo_sample_name = tumor_sample.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY][
                0
            ]  # they should all be the same
            tumor_baits = tumor_sample.bait_set
            tumor_run_mode = tumor_sample.run_mode
            expected_normal_cmo_sample_name = ""
            if tumor_cmo_sample_name in self.pre_pairing:
                expected_normal_cmo_sample_name = self.pre_pairing[tumor_cmo_sample_name]
            normal = self._get_normal(tumor_baits, tumor_run_mode, expected_normal_cmo_sample_name)
            if normal:
                self.sample_pairing.append([tumor_sample, normal])
            else:
                self.unpaired_samples.append(tumor_sample)

    def _get_normal(self, bait_set, run_mode, expected_normal_cmo_sample_name=""):
        normal = None
        for normal_sample_name in self.normal_samples:
            normal_sample = self.normal_samples[normal_sample_name]
            normal_baits = normal_sample.bait_set
            normal_run_mode = normal_sample.run_mode
            if expected_normal_cmo_sample_name:  # if this is True, we're using historical pairing info
                normal_cmo_sample_name = normal_sample.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY][
                    0
                ]  # they should all be the same for this sample
                if normal_cmo_sample_name == expected_normal_cmo_sample_name:
                    normal = normal_sample
                    return normal
            # make sure hiseq pairs with hiseq, novaseq with novaseq
            elif normal_baits.lower() == bait_set.lower() and normal_run_mode.lower() == run_mode.lower():
                if not normal:
                    normal = normal_sample
                else:
                    normal = self._return_more_recent_normal(normal_sample, normal)
        return normal

    def _return_more_recent_normal(self, n1, n2):
        n1_run_date = self._most_recent_date(n1.metadata["runDate"])
        n2_run_date = self._most_recent_date(n2.metadata["runDate"])
        recent_normal = n1
        if n2_run_date > n1_run_date:
            recent_normal = n2
        return recent_normal

    def _most_recent_date(self, dates):
        date = None
        for d in dates:
            current_date = None
            try:
                current_date = dt.strptime(d, "%y-%m-%d")
            except ValueError:
                current_date = dt.strptime(d, "%Y-%m-%d")
            if current_date:
                if not date:
                    date = current_date
                else:
                    if current_date > date:
                        date = current_date
        return date

    def create_mapping_json(self):
        """
        TODO: Remove it when you confirm it is not needed anymore
        """
        mapping = []
        seen = set()
        for pair in self.sample_pairing:
            tumor_sample = pair[0]
            normal_sample = pair[1]
            mapping.extend(self.get_mapping_for_sample(tumor_sample))
            if normal_sample not in seen:
                mapping.extend(self.get_mapping_for_sample(normal_sample))
                seen.add(normal_sample)
        return mapping

    def create_mapping_json_all_samples_included(self):
        mapping = []
        for sample in self.all_samples:
            mapping.extend(self.get_mapping_for_sample(self.all_samples[sample]))
        return mapping

    def create_unpaired_mapping_json(self):
        mapping = []
        seen = set()
        for sample in self.unpaired_samples:
            tumor_sample = sample
            mapping.extend(self.get_mapping_for_sample(tumor_sample))
        return mapping

    def get_mapping_for_sample(self, sample):
        target = sample.bait_set
        fastqs = sample.fastqs
        cmo_sample_name = sample.cmo_sample_name
        mapping_sample = []
        if fastqs.paired:
            num_fq_pairs = len(fastqs.r1)
            for i in range(0, num_fq_pairs):
                mapping_sample.append(
                    {
                        "sample": cmo_sample_name,
                        "target": target,
                        "fastq_pe1": {"class": "File", "location": f"juno://{fastqs.r1[i].path}"},
                        "fastq_pe2": {"class": "File", "location": f"juno://{fastqs.r2[i].path}"},
                        "num_fq_pairs": num_fq_pairs,
                    }
                )
        return mapping_sample

    def create_pairing_json(self):
        pairing = []
        if self.sample_pairing:
            for pair in self.sample_pairing:
                tumor = pair[0].cmo_sample_name
                normal = pair[1].cmo_sample_name
                pairing.append({"tumor": tumor, "normal": normal})
        return pairing

    def create_unpaired_string(self, fields):
        s = ""
        for sample in self.unpaired_samples:
            data = [
                ";".join(list(set(sample.metadata[field]))).strip() for field in fields
            ]  # hack; probably need better way to map fields to unpaired txt file
            possible_reason = self._get_possible_reason(sample)
            s += "\n" + "\t".join(data) + "\t" + possible_reason
        return s

    def _get_possible_reason(self, sample):
        num_normals = len(self.normal_samples)
        if num_normals == 0:
            return "No normals for patient"
        matching_baits = False
        matching_run_modes = False
        for sample_name in self.normal_samples:
            normal = self.normal_samples[sample_name]
            if normal.bait_set.lower() == sample.bait_set.lower():
                matching_baits = True
            if normal.run_mode.lower() == sample.run_mode.lower():
                matching_run_modes = True
        if not matching_baits:
            return "No normal sample has same bait set as tumor in patient"
        if not matching_run_modes:
            return "No normal sample has same bait set and run mode (HiSeq/NovaSeq) as tumor in patient"
        first_half_of_2017 = False
        run_dates = sample.metadata["runDate"]
        if run_dates and isinstance(run_dates, str):
            run_dates = run_dates.split(";")
            for run_date in run_dates:
                if run_date:
                    try:
                        current_date = dt.strptime(d, "%y-%m-%d")
                    except ValueError:
                        current_date = dt.strptime(d, "%Y-%m-%d")
                    if current_date < dt(2017, 6, 1):
                        first_half_of_2017 = True
            if first_half_of_2017:
                return "Sample run date first half of 2017; normal may have been sequenced in 2016?"
        return ""

    def create_conflict_string(self, fields):
        s = ""
        for sample_name in self.conflict_samples:
            sample = self.conflict_samples[sample_name]
            data = [
                ";".join(list(set(sample.metadata[field]))).strip() for field in fields
            ]  # hack; probably need better way to map fields to unpaired txt file
            conflicts = []
            if "sampleNameMalformed" in sample.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]:
                conflicts.append("incorrect CMO Sample Name")
            if not "".join(sample.metadata[settings.SAMPLE_CLASS_METADATA_KEY]):
                conflicts.append("no sample class")
            multiple_values = [
                "" + field + "[" + ";".join(list(set(sample.metadata[field]))).strip() + "]"
                for field in sample.conflict_fields
            ]
            conflicts = conflicts + multiple_values
            s += "\n" + "\t".join(data) + "\t" + ";".join(conflicts)
        return s
