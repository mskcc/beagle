from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from file_system.models import File, FileGroup, Sample, Storage, StorageType
from operator_manager.models import OperatorRun
from runner.models import Pipeline, Port, PortType, ProtocolType, Run, RunStatus


def bid(file):
    return {"class": "File", "location": f"bid://{file.id}"}


class SDKRunViewTest(APITestCase):
    def setUp(self):
        self.client.force_authenticate(user=User.objects.create_user("user", "user@example.com", "password"))
        self.url = reverse("sdk-runs-list")
        storage = Storage.objects.create(name="local", type=StorageType.LOCAL)
        self.file_group = FileGroup.objects.create(name="group", slug="group", storage=storage)
        self.fastq = self._file("/data/input/sample_R1.fastq.gz")
        self.bam = self._file("/data/output/sample.bam")
        self.bai = self._file("/data/output/sample.bai")
        self.maf = self._file("/data/output/sample.maf")
        self.nf_csv = self._file("/data/output/nf/summary.csv")
        self.nf_html = self._file("/data/output/nf/report.html")
        self.operator_run = OperatorRun.objects.create(num_total_runs=2)

        cwl = self._pipeline("cwl pipeline", ProtocolType.CWL)
        self.cwl_run = self._run(cwl, RunStatus.COMPLETED)
        self.cwl_run.samples.add(Sample.objects.create(sample_id="sample-1"))
        self._port(self.cwl_run, "fastqs", PortType.INPUT, [bid(self.fastq)])
        self._port(self.cwl_run, "assay", PortType.INPUT, "WES")
        self._port(self.cwl_run, "bam", PortType.OUTPUT, {**bid(self.bam), "secondaryFiles": [bid(self.bai)]})
        self._port(self.cwl_run, "maf", PortType.OUTPUT, bid(self.maf))

        nextflow = self._pipeline("nextflow pipeline", ProtocolType.NEXTFLOW)
        self.nf_run = self._run(nextflow, RunStatus.FAILED)
        # Nextflow inputs keep File objects in db_value; value holds the rendered samplesheet
        self._port(
            self.nf_run,
            "samplesheet",
            PortType.INPUT,
            [{"sample": "sample-1", "fastq": bid(self.fastq)}],
            value="sample\tfastq\nsample-1\t/data/input/sample_R1.fastq.gz\n",
        )
        # Ridgeback returns every published Nextflow file in a single "outputs" port
        self._port(self.nf_run, "outputs", PortType.OUTPUT, [bid(self.nf_csv), bid(self.nf_html)])

        other = self._run(cwl, RunStatus.COMPLETED, operator_run=None)
        self._port(other, "maf", PortType.OUTPUT, bid(self.maf))

    def _file(self, path):
        return File.objects.create(
            file_name=path.rsplit("/", 1)[-1], path=path, size=10, checksum="sha1$abc", file_group=self.file_group
        )

    def _pipeline(self, name, pipeline_type):
        return Pipeline.objects.create(
            name=name,
            version="1.0.0",
            github="https://github.com/x/y.git",
            entrypoint="main",
            pipeline_type=pipeline_type,
            output_file_group=self.file_group,
            output_directory="/data/output",
        )

    def _run(self, pipeline, run_status, operator_run="default"):
        return Run.objects.create(
            name=pipeline.name,
            app=pipeline,
            status=run_status,
            operator_run=self.operator_run if operator_run == "default" else operator_run,
            tags={"igoRequestId": "request-1"},
            output_metadata={"assay": "WES"},
            notify_for_outputs=[],
        )

    def _port(self, run, name, port_type, db_value, value=None):
        Port.objects.create(
            run=run, name=name, port_type=port_type, db_value=db_value, value=db_value if value is None else value
        )

    def _cwl_file(self, file, **extra):
        return {
            "class": "File",
            "id": str(file.id),
            "path": file.path,
            "basename": file.file_name,
            "nameext": "." + file.file_name.rsplit(".", 1)[-1],
            "nameroot": file.file_name.rsplit(".", 1)[0],
            "size": 10,
            "checksum": "sha1$abc",
            **extra,
        }

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {"run_ids": str(self.cwl_run.id)})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_requires_a_filter(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cwl_run(self):
        response = self.client.get(self.url, {"run_ids": str(self.cwl_run.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)
        run = response.json()["results"][0]
        self.assertEqual(run["status"], "COMPLETED")
        self.assertEqual(
            run["pipeline"],
            {"id": str(self.cwl_run.app.id), "name": "cwl pipeline", "version": "1.0.0", "pipeline_type": "CWL"},
        )
        self.assertEqual(run["samples"], ["sample-1"])
        self.assertEqual(run["tags"], {"igoRequestId": "request-1"})
        self.assertEqual(run["output_metadata"], {"assay": "WES"})
        self.assertEqual(run["operator_run"], str(self.operator_run.id))
        self.assertEqual(run["inputs"], {"assay": "WES", "fastqs": [self._cwl_file(self.fastq)]})
        self.assertEqual(
            run["outputs"],
            {
                "bam": self._cwl_file(self.bam, secondaryFiles=[self._cwl_file(self.bai)]),
                "maf": self._cwl_file(self.maf),
            },
        )

    def test_nextflow_run(self):
        response = self.client.get(self.url, {"run_ids": str(self.nf_run.id)})
        run = response.json()["results"][0]
        self.assertEqual(run["pipeline"]["pipeline_type"], "NEXTFLOW")
        self.assertEqual(run["inputs"], {"samplesheet": [{"sample": "sample-1", "fastq": self._cwl_file(self.fastq)}]})
        self.assertEqual(run["outputs"], {"outputs": [self._cwl_file(self.nf_csv), self._cwl_file(self.nf_html)]})

    def test_filters(self):
        cwl, nf = str(self.cwl_run.id), str(self.nf_run.id)
        for params, expected in (
            ({"run_ids": f"{cwl},{nf}"}, [cwl, nf]),
            ({"run_ids": [cwl, nf], "status": "COMPLETED"}, [cwl]),
            ({"operator_run": str(self.operator_run.id)}, [cwl, nf]),
            ({"operator_run": str(self.operator_run.id), "status": "FAILED"}, [nf]),
        ):
            response = self.client.get(self.url, params)
            self.assertEqual(response.status_code, status.HTTP_200_OK, params)
            self.assertEqual([r["id"] for r in response.json()["results"]], expected, params)

    def test_invalid_status(self):
        response = self.client.get(self.url, {"run_ids": str(self.cwl_run.id), "status": "BOGUS"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve(self):
        response = self.client.get(reverse("sdk-runs-detail", args=[self.nf_run.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], str(self.nf_run.id))
        self.assertIn("outputs", response.json()["outputs"])
