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
                if len(barcodeIndex) > 1:
                    index2 = barcodeIndex[1]

            for lane in f.metadata["flowCellLanes"]:
                samples.append({
                    "lane": lane,
                    "sample_id": f.metadata["sampleId"],
                    "sample_plate": f.metadata["tumorOrNormal"],
                    "sample_well": f.metadata["recipe"],
                    "17_index_id": f.metadata["barcodeId"],
                    "index": index1,
                    "index2": index2,
                    "sample_project": "Project_" + self.request_id,
                    "description": f.metadata["dataAnalystName"]
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
