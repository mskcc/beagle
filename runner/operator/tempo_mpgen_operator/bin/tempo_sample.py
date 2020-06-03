from runner.operator.tempo_mpgen_operator.bin.sample_object import Sample


class TempoSample(Sample):
    def __init__(self, sample_name, file_list):
        self.sample_name = sample_name
        super().__init__(sample_name, file_list)
        self._metadata = dict()
        metadata_list = [ i.metadata for i in file_list ]
        for metadata in metadata_list:
            for key in metadata:
                if key not in self._metadata:
                    self._metadata[key] = list()
                self._metadata[key].append(metadata[key])
        self._metadata.pop("R")
        self.conflict = False
        self.conflict_fields = list()
        self._set_status()


    def _set_status(self):
        """
        Set status of sample. Status in this case is "does sample have good data"

        If some predefined fields contain multiple, different values, set conflict to True
        If some information is missing, set conflict to True
        """
        self._find_conflict_fields()


    def _find_conflict_fields(self):
        """
        Check if some fields have more than one value.

        Important because some values are required for pairing and if there are discrepancies
        in some fields it would directly affect that logic

        Currently even if there are conflicting fields, this TempoSample object will still
        be runnable, as the fastqs are still paired in the Sample object
        """
        fields_to_check = [ 'patientId', 'requestId', 'sampleId', 'specimenType', 'runMode' ]
        for key in fields_to_check:
            values = self._metadata[key]
            if not self._values_are_list(key):
                values_set = set(tuple(x) for x in values if x != None)
                if len(values_set) > 1:
                    self.conflict_fields.append(key)
                    self.conflict = True


    def _dedupe_metadata_values(self):
        metadata = dict()
        for key in self._metadata:
            values = self._metadata[key]
            if not self._values_are_list(key):
                # remove empty strings
                values = [i for i in values if i]
                if len(set(values)) == 1:
                    metadata[key] = values[0]
                else:
                    value = set(values)
                    metadata[key] = ','.join(value)
            else:
                # remove duplicate list values
                values_set = set(tuple(x) for x in values)
                values = [ list(x) for x in values_set ]
                metadata[key] = values
        return metadata


    def _values_are_list(self, key):
        for ele in self._metadata[key]:
            if not isinstance(ele, list):
                return False
        return True


    def __str__(self):
        keys_for_str = [ 'sampleName', 'requestId', 'sampleId', 'patientId', 'specimenType' ]
        s = ""
        metadata = self._dedupe_metadata_values()
        for key in keys_for_str:
            if not isinstance(metadata[key], str):
                data = ",".join(metadata[key])
            else:
                data = metadata[key]
            s += "%s: %s\n" % (key, data)
        return s
