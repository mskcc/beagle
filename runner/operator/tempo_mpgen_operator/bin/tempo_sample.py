from runner.operator.tempo_mpgen_operator.bin.sample_object import Sample


class TempoSample(Sample):
    def __init__(self, sample_name, file_list):
        self.sample_name = sample_name
        super().__init__(sample_name, file_list)
        self.metadata = dict() # every field in this dict will be a list
        metadata_list = [ i.metadata for i in file_list ]
        for metadata in metadata_list:
            for key in metadata:
                if key not in self.metadata:
                    self.metadata[key] = list()
                self.metadata[key].append(metadata[key])
        self.metadata.pop("R")
        self.conflict = False
        self.conflict_fields = list()
        self._set_status()
        self.specimen_type = ""
        self.sample_class = ""
        self.bait_set = ""
        self.cmo_sample_name = ""
        self.run_mode = ""
        self.patient_id = ""
        # _find_conflict_fields() did not discrepancies in fields it checked
        if not self.conflict: 
            self.bait_set = self._get_bait_sets().pop()
            self.specimen_type = self.metadata['specimenType'][0]
            self.sample_class = self.metadata['sampleClass'][0]
            self.cmo_sample_name = self.metadata['cmoSampleName'][0]
            self.run_mode = self.remapped_run_mode.pop()
            self.patient_id = self.metadata['patientId'][0]

    def _resolve_target(self, bait_set):
        """
        """
        target_assay = bait_set.lower()
        if "agilent" in target_assay:
            return "agilent"
        if "idt" in target_assay:
            return "idt"
        if "sureselect" in target_assay:
            return "agilent"
        return None

    def _set_status(self):
        """
        Set status of sample. Status in this case is "does sample have good data"

        If some predefined fields contain multiple, different values, set conflict to True
        If some information is missing, set conflict to True

        Run modes get grouped by similarity in _map_run_modes()
        """
        self._map_run_modes()
        self._find_conflict_fields()


    def _map_run_modes(self):
        run_modes = self.metadata['runMode']
        self.remapped_run_mode = set()

        for i in run_modes:
            if 'novaseq' in i.lower():
                self.remapped_run_mode.add("NovaSeq")
            elif 'hiseq' in i.lower():
                self.remapped_run_mode.add("HiSeq")
            else:
                self.remapped_run_mode.add(i)
        if len(self.remapped_run_mode) > 1:
            self.conflict = True


    def _find_conflict_fields(self):
        """
        Check if some fields have more than one value.

        Important because some values are required for pairing and if there are discrepancies
        in some fields it would directly affect that logic

        Currently even if there are conflicting fields, this TempoSample object will still
        be runnable, as the fastqs are still paired in the Sample object
        """
        fields_to_check = [ 'patientId', 'specimenType',
                    'sampleClass', 'cmoSampleName' ]
        for key in fields_to_check:
            values = self.metadata[key]
            if not self._values_are_list(key):
                values_set = set(tuple(x) for x in values if x != None)
                if len(values_set) > 1:
                    self.conflict_fields.append(key)
                    self.conflict = True
        bait_sets = self._get_bait_sets()
        if len(bait_sets) > 1 or len(bait_sets) == 0:
            self.conflict_fields.append('baitSet')
            self.conflict = True


    def _get_bait_sets(self):
        bait_sets = set()
        for value in self.metadata['baitSet']:
            bait_set = self._resolve_target(value)
            bait_sets.add(bait_set)
        return bait_sets

    def dedupe_metadata_values(self):
        """
        Removes duplicates from metadata lists
        Duplicates are necessary because we are storing a copy of each
        metadata associated with a fastq

        Omitting qcReports value because it's got a complicated structure
        that isn't relevant right now
        """
        metadata = dict()
        for key in self.metadata:
            values = self.metadata[key]
            # Removing qcReports, which is a list containing a dictionary
            if key not in "qcReports":
                if self._values_are_list(key):
                    # remove duplicate list values
                    values_set = set(tuple(x) for x in values)
                    values = [ list(x) for x in values_set ]
                    metadata[key] = values
                else:
                    # remove empty strings
                    values = [str(i) for i in values if i]
                    if len(set(values)) == 1:
                        metadata[key] = values[0]
                    else:
                        value = set(values)
                        metadata[key] = ','.join(value)
        return metadata


    def _values_are_list(self, key):
        """
        Checks if the values within a list are also lists
        """
        for ele in self.metadata[key]:
            if not isinstance(ele, list):
                return False
        return True


    def __str__(self):
        keys_for_str = [ 'sampleName', 'requestId', 'sampleId',
                'patientId', 'specimenType', 'sampleClass',
                'cmoSampleName']
        s = ""
        metadata = self.dedupe_metadata_values()
        for key in keys_for_str:
            if not isinstance(metadata[key], str):
                data = ",".join(metadata[key])
            else:
                data = metadata[key]
            s += "%s: %s\n" % (key, data)
        return s
