import json
import os
from collections.abc import Iterable

from django.conf import settings


class SampleMetadata:
    def __init__(self, file_list, file_type):
        self.metadata = dict()  # every field in this dict will be a list
        metadata_list = [i.metadata for i in file_list]
        self.file_type = file_type
        self.file_list = file_list
        for metadata in metadata_list:
            for key in metadata:
                if key not in self.metadata:
                    self.metadata[key] = list()
                self.metadata[key].append(metadata[key])
        self.conflict = False
        self.conflict_fields = list()
        self._set_status()
        self.sample_class = ""
        self.sample_type = ""
        self.bait_set = ""
        self.cmo_sample_name = ""
        self.run_mode = ""
        self.patient_id = ""
        self.flowcell_id = ""
        # _find_conflict_fields() did not discrepancies in fields it checked
        if not self.conflict:
            self.metadata = self.dedupe_metadata_values()
            self.bait_set = self.metadata[settings.BAITSET_METADATA_KEY]
            self.sample_class = self.metadata[settings.SAMPLE_CLASS_METADATA_KEY]
            self.sample_type = self.metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY]
            self.cmo_sample_name = self.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]
            self.patient_id = self.metadata[settings.PATIENT_ID_METADATA_KEY]
            self.run_mode = self.remapped_run_mode.pop()
            self.flowcell_id = self.metadata["flowCellId"]
            self.barcode_index = self._set_barcode_index()

    def _set_barcode_index(self):
        #        if self.metadata.get("barcodeIndex") is not None:
        #           return self.metadata["barcodeIndex"]
        barcode_index = self._spoof_barcode()
        return barcode_index

    def _spoof_barcode(self):
        """
        Spoof barcode by removing R1/R2 or .bam from end of filename, reverse the string.
        Works even with compound extensions like .fastq.gz.

        Barcode is used only for submitting to the cluster; makes sure paired fastqs get
        sent together during job distribution
        """
        # Get just the base name
        filename = os.path.basename(self.file_list[0].file.path)

        # Reverse full filename
        reversed_name = filename[::-1]

        # Remove reversed extensions
        for ext in ["bam", "gz", "fastq", "bz2", "tar"]:
            rev_ext = ext[::-1] + "."  # e.g., 'gz.' to match '.gz'
            if reversed_name.startswith(rev_ext):
                reversed_name = reversed_name[len(rev_ext) :]

        # Remove R1/R2 in reversed form
        reversed_name = reversed_name.replace("1R_", "").replace("2R_", "")

        # Reverse back to get spoofed barcode
        spoofed_barcode = reversed_name[::-1]
        return spoofed_barcode

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
        run_modes = self.metadata["runMode"]
        self.remapped_run_mode = set()

        for i in run_modes:
            if "novaseq" in i.lower():
                if "x" in i.lower():
                    self.remapped_run_mode.add("NovaSeq X")
                else:
                    self.remapped_run_mode.add("NovaSeq")
            elif "hiseq" in i.lower():
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
        """
        fields_to_check = [
            settings.BAITSET_METADATA_KEY,
            settings.PATIENT_ID_METADATA_KEY,
            settings.SAMPLE_CLASS_METADATA_KEY,
            settings.CMO_SAMPLE_CLASS_METADATA_KEY,
            settings.CMO_SAMPLE_TAG_METADATA_KEY,
        ]
        for key in fields_to_check:
            values = self.metadata[key]
            if not self._values_are_list(key):
                values_set = set(tuple(x) for x in values if x != None)
                if len(values_set) > 1:
                    self.conflict_fields.append(key)
                    self.conflict = True

    def dedupe_metadata_values(self):
        """
        Removes duplicates from metadata lists
        Duplicates are necessary because we are storing a copy of each
        metadata associated with a fastq

        Omitting qcReports value because it's got a complicated structure
        that isn't relevant right now
        """
        metadata = dict()
        meta_orig = self.metadata
        for key in self.metadata:
            values = self.metadata[key]
            if isinstance(values, Iterable):
                # expanding sampleAliases/investigatorId to investigatorId for sample
                if key in "sampleAliases":
                    metadata["investigatorId"] = self._get_investigator_id(meta_orig[key])
                elif key not in ["qcReports", "patientAliases"]:
                    if self._values_are_list(key):
                        # remove duplicate list values
                        values_set = set(tuple(x) for x in values)
                        values = [list(x) for x in values_set]
                        metadata[key] = values
                    else:
                        # remove empty strings
                        values = [str(i) for i in values if i]
                        if len(set(values)) == 1:
                            metadata[key] = values[0]
                        else:
                            value = set(values)
                            metadata[key] = ",".join(value)
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
        keys_for_str = [
            settings.CMO_SAMPLE_NAME_METADATA_KEY,
            settings.REQUEST_ID_METADATA_KEY,
            settings.SAMPLE_ID_METADATA_KEY,
            settings.PATIENT_ID_METADATA_KEY,
            settings.SAMPLE_CLASS_METADATA_KEY,
            settings.CMO_SAMPLE_CLASS_METADATA_KEY,
            settings.CMO_SAMPLE_TAG_METADATA_KEY,
        ]
        s = ""
        for key in keys_for_str:
            if not isinstance(self.metadata[key], str):
                data = ",".join(self.metadata[key])
            else:
                data = self.metadata[key]
            s += "%s: %s\n" % (key, data)
        return s

    def _get_investigator_id(self, sample_aliases):
        """
        externalSampleId was deprecated and is no longer
        included in new imports; need to return investigatorId value in sampleAliases
        instead
        """
        for l1 in sample_aliases:
            for l2 in l1:
                v = l2["value"]
                ns = l2["namespace"]
                if ns == "investigatorId":
                    return v
        return None

    def __repr__(self):
        return json.dumps(self.metadata, indent=2, sort_keys=True)
