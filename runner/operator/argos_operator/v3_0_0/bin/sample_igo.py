import json
import os
from collections.abc import Iterable

from django.conf import settings

from ..utils.barcode_utils import spoof_barcode
from .files_object import FilesObj
from .sample_file_object import SampleFile


class SampleIGO:
    sample_files: list["SampleFile"]

    def __init__(self, sample_name, file_list, file_type):
        self.sample_name = sample_name
        self.data = dict()  # every field in this dict will be a list
        metadata_list = [i.metadata for i in file_list]
        self.file_type = file_type
        self.file_list = file_list
        for metadata in metadata_list:
            for key in metadata:
                if key not in self.data:
                    self.data[key] = list()
                self.data[key].append(metadata[key])
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
        # _find_conflict_fields() did not find discrepancies in fields it checked
        if not self.conflict:
            self.data = self.dedupe_metadata_values()
            self.bait_set = self.data[settings.BAITSET_METADATA_KEY]
            self.sample_class = self.data[settings.SAMPLE_CLASS_METADATA_KEY]
            self.sample_type = self.data[settings.CMO_SAMPLE_CLASS_METADATA_KEY]
            self.cmo_sample_name = self.data[settings.CMO_SAMPLE_TAG_METADATA_KEY]
            self.patient_id = self.data[settings.PATIENT_ID_METADATA_KEY]
            self.run_mode = self.remapped_run_mode.pop()
            self.flowcell_id = self.data["flowCellId"]
            self.run_date = self.data["runDate"]
        self.files_obj = FilesObj(file_list, file_type)
        self.file_type = self.files_obj.file_type
        self.files = self.files_obj.get_files()
        self.sample_files = list()
        if self.file_type == "fastq":
            for r1_fastq in self.files["R1"]:
                metadata = self.data
                if not metadata.get("barcodeIndex"):
                    barcode_index = spoof_barcode(r1_fastq)
                    metadata["barcodeIndex"] = barcode_index
                sample_file = SampleFile(r1_fastq, metadata)
                self.sample_files.append(sample_file)
            for r2_fastq in self.files["R2"]:
                metadata = self.data
                if not metadata.get("barcodeIndex"):
                    barcode_index = spoof_barcode(r2_fastq)
                    metadata["barcodeIndex"] = barcode_index
                sample_file = SampleFile(r2_fastq, metadata)
                self.sample_files.append(sample_file)
        if self.file_type == "bam":
            metadata = self.data
            for f in self.files["bam"]:
                if not metadata.get("barcodeIndex"):
                    barcode_index = spoof_barcode(f)
                    metadata["barcodeIndex"] = barcode_index
                sample_file = SampleFile(f, metadata)
                self.sample_files.append(sample_file)

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
        run_modes = self.data["runMode"]
        self.remapped_run_mode = set()

        # TODO Remap with Machine Class table
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
            values = self.data[key]
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
        meta_orig = self.data
        for key in self.data:
            values = self.data[key]
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
        for ele in self.data[key]:
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
            if not isinstance(self.data[key], str):
                data = ",".join(self.data[key])
            else:
                data = self.data[key]
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

    @property
    def metadata(self):
        """
        Get metadata for all samples from the SampleFile objects assigned to this SampleIGO object

        Note that they are MERGED here. Metadata are assumed to be the same across all SampleFiles
        """
        merged = dict()
        for f in self.sample_files:
            merged.update(f.metadata.metadata)
        return merged

    def __repr__(self):
        return json.dumps(self.data, indent=2, sort_keys=True)
