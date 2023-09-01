"""
Test cases for Demo Operator
"""
import os
from django.test import TestCase
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata, FileGroup
from runner.models import Run, Pipeline, OperatorRun, Port
from runner.operator.operator_factory import OperatorFactory
from runner.operator.demo_operator.demo_operator import DemoOperator
from runner.tasks import check_jobs_status, process_triggers
from tempfile import mkdtemp
import shutil
from mock import patch
from django.conf import settings
import time
import requests
from pprint import pprint

# Run Celery tasks synchronously for testing, no async
import beagle_etl.celery

if beagle_etl.celery.app.conf["task_always_eager"] == False:
    beagle_etl.celery.app.conf["task_always_eager"] = True

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class MockRequest(object):
    """
    empty object to simulate a 'request' object; apply a 'data' attribute to this later
    """

    pass


def get_job(id):
    """get job details from Ridgeback"""
    url = settings.RIDGEBACK_URL + "/v0/jobs/{}/".format(id)
    res = requests.get(url)
    status_code = res.status_code
    data = res.json()
    return (res, status_code, data)


def wait_on_runs(run_instance, operator_run_instance, interval=5):
    """wait on the runs to finish"""
    count = 0
    while True:
        count += 1
        # check on the status of the job and reload the Run and OperatorRun entries from the db
        print(">>> ~~~~~ Checking Job Status ({}) ~~~~~".format(count))
        check_jobs_status()
        run_instance.refresh_from_db()
        operator_run_instance.refresh_from_db()

        job_id = run_instance.execution_id

        # check for Ridgeback job
        if job_id:
            res, status_code, data = get_job(job_id)
            job_status = data["status"]
            print(">>> Ridgeback job:")
            pprint(data, indent=4)

        print(">>> Run:")
        pprint(run_instance.__dict__, indent=4)

        print(">>> OperatorRun:")
        pprint(operator_run_instance.__dict__, indent=4)

        run_status = run_instance.status
        operator_run_status = operator_run_instance.status

        # check if it finished
        # TODO: This never finishes because Run status never changes to complete even though Ridgeback job finishes
        if run_status == 3:  # or job_status == 'COMPLETED'
            print(">>> its done")
            check_jobs_status()
            break
        elif run_status == 4:  #  or job_status == 'FAILED'
            print(">>> it broke")
            check_jobs_status()
            break
        else:
            time.sleep(interval)


class TestDemoOperator(TestCase):
    def setUp(self):
        self.preserve = False  # save the tmpdir
        settings.NOTIFIER_ACTIVE = False

        # needed for making File entries in the db
        self.filegroup = FileGroup.objects.create(name="demo_filegroup", slug="demo_filegroup")

        # db entry for the Operator we want to test
        self.operator = Operator.objects.create(
            slug="DemoOperator",
            class_name="runner.operator.demo_operator.demo_operator.DemoOperator",
            version="1",
            active=True,
            recipes=[],
        )

        # make a tmpdir and put a file in it
        # use this local dir so that its accessible across the HPC
        os.umask(0o000)  # make sure newly created files and dirs are accessible
        self.tmpdir = mkdtemp(dir=THIS_DIR)
        os.chmod(self.tmpdir, 0o770)  # need permissions for voyager user to access
        self.tmp_path = os.path.join(self.tmpdir, "foo.txt")
        self.output_dir = os.path.join(self.tmpdir, "output")
        os.mkdir(self.output_dir)
        os.chmod(self.output_dir, 0o770)
        with open(self.tmp_path, "w") as f:
            f.write("some data\n")

        # add the file to the db
        self.file1 = File.objects.create(
            file_name=os.path.basename(self.tmp_path), path=self.tmp_path, file_group=self.filegroup
        )
        self.fileMetadata1 = FileMetadata.objects.create(
            file=self.file1, metadata={settings.REQUEST_ID_METADATA_KEY: "1"}
        )

        # add a second file to the db
        self.tmp_path2 = os.path.join(self.tmpdir, "bar.txt")
        with open(self.tmp_path2, "w") as f:
            f.write("some more data\n")
        self.file2 = File.objects.create(
            file_name=os.path.basename(self.tmp_path2), path=self.tmp_path2, file_group=self.filegroup
        )
        self.fileMetadata2 = FileMetadata.objects.create(
            file=self.file2, metadata={settings.REQUEST_ID_METADATA_KEY: "2"}
        )

        # Pipeline entry for the Operator
        self.pipeline = Pipeline.objects.create(
            name=DemoOperator._pipeline_name,
            github="https://github.com/stevekm/copy-cwl",
            version="master",
            entrypoint="copy.cwl",
            output_file_group=self.filegroup,
            output_directory=self.output_dir,
            operator=self.operator,
        )

    def tearDown(self):
        if not self.preserve:
            # remove the tmpdir upon test completion
            shutil.rmtree(self.tmpdir)

    def test_get_demo_operator(self):
        """
        Test that DemoOperator can be initialized
        """
        operator_instance = self.operator
        operator = OperatorFactory.get_by_model(operator_instance)
        self.assertEqual(str(operator.model), "DemoOperator")

    def test_demo_operator_input(self):
        """
        Test that input data can be generated from Demo Operator
        """
        request_id = "1"
        operator_instance = self.operator
        operator = OperatorFactory.get_by_model(operator_instance, request_id=request_id)
        run_input = operator.create_input()
        expected_input = {"input_file": {"class": "File", "location": "juno://" + self.file1.path}}
        self.assertDictEqual(run_input, expected_input)

    def test_get_demo_operator_jobs(self):
        """
        Test case for getting jobs from Demo Operator
        """
        request_id = "1"
        operator_instance = self.operator
        operator = OperatorFactory.get_by_model(operator_instance, request_id=request_id)
        pipeline_instance = Pipeline.objects.get(id=operator.get_pipeline_id())

        jobs = operator.get_jobs()
        self.assertEqual(len(jobs), 1)

        job = jobs[0]
        input_data = job.inputs

        expected_input = {"input_file": {"class": "File", "location": "juno://" + self.file1.path}}

        self.assertDictEqual(input_data, expected_input)
