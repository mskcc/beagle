import os
import logging

from file_system.repository.file_repository import FileRepository
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer

logger = logging.getLogger(__name__)

class AccessSampleSheetOperator(Operator):
    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        files = FileRepository.filter(queryset=self.files,
                                      metadata={'requestId': self.request_id,
                                                'igocomplete': True})

        samples = []
        for f in files:
            if f.metadata["barcodeIndex"]:
                barcodeIndex = f.metadata["barcodeIndex"].split("-")
                index1 = barcodeIndex[0]

            for lane in f.metadata["flowCellLanes"]:
                samples.append({
                    "Lane": lane,
                    "SampleID": f.metadata["sampleName"],
                    "SampleRef": f.metadata["species"],
                    "Index": index1,
                    "Description": f.metadata["tumorOrNormal"],
                    "Control": "N",
                    "Recipe": f.metadata["recipe"],
                    "Operator": "|".join(["AR", "-;-", f.metadata["sampleId"], f.metadata["sex"], "NOVASEQ"]),
                    "SampleProject": "Project_" + self.request_id,
                    "DnaInputNg": f.metadata["dnaInputNg"],
                    "CaptureInputNg": f.metadata["captureInputNg"],
                    "LibraryVolume": f.metadata["libraryVolume"],
                    "PatientID": f.metadata["patientId"],
                    "IgoID": f.metadata["sampleId"],
                })

        inputs = [{
            "samples": samples
        }]

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "Sample Sheet: %s, %i of %i" % (self.request_id, i + 1, len(inputs)),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'tags': {
                            'requestId': self.request_id
                        }
                    }
                ),
                job
             )
            for i, job in enumerate(inputs)
        ]
