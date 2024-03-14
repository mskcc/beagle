import os
import json
from runner.models import Operator
from runner.models import Pipeline
from django.core.management.base import BaseCommand
from runner.operator.operator_factory import OperatorFactory
from runner.run.objects.run_object_factory import RunObjectFactory


class Command(BaseCommand):
    help = "Run Operator"

    WORK_DIRECTORY = "/rtsess01/compute/juno/bic/ROOT/work/voyager/"
    RES_DIRECTORY = "/rtsess01/compute/juno/bic/ROOT/res/voyager/"

    def add_arguments(self, parser):
        parser.add_argument("--operator", type=str)
        parser.add_argument("--operator-version", type=str)
        parser.add_argument("--request-id", type=str)
        parser.add_argument("--job-name", type=str)
        parser.add_argument("--run-ids", type=str)
        parser.add_argument("--pairing", type=bool)

    def handle(self, *args, **options):
        request_id = options["request_id"]
        run_ids = options["run_ids"]
        operator_path = options["operator"]
        operator_version = options["operator_version"]
        job_name = options["job_name"]

        print(f"Running {request_id} with operator {operator_path} version {operator_version}")

        if run_ids:
            run_ids = run_ids.split(',')
            operator = OperatorFactory.get_by_model(
                Operator.objects.get(class_name=operator_path, version=operator_version)
            )
            operator.run_ids = run_ids
            pipeline_id = operator.get_pipeline_id()
            jobs = operator.get_jobs()

        elif request_id:
            operator = OperatorFactory.get_by_model(
                Operator.objects.get(class_name=operator_path, version=operator_version)
            )
            operator.request_id = request_id
            pipeline_id = operator.get_pipeline_id()
            jobs = operator.get_jobs()
        else:
            print("Either request-id or run-ids needs to be specified")

        pipeline = Pipeline.objects.get(id=pipeline_id)
        runs = []
        for job in jobs:
            run = job.create()
            runs.append(run)
            run_obj = RunObjectFactory.from_definition(str(run.id), job.inputs)
            run_obj.ready()
            run_obj.to_db()

            inputs = run_obj.dump_job()["inputs"]
            print(f"Creating job for tumor {job_name}")
            work_dir = os.path.join(self.WORK_DIRECTORY, request_id, job_name)
            res_dir = os.path.join(self.RES_DIRECTORY, request_id, job_name)
            with open(f"{job_name}.json", "w") as f:
                print(f"Dumping input file into {job_name}.json")
                json.dump(inputs, f)
            with open(f"{job_name}.cmd", "w") as f:
                print(f"Dumping cmd line into file {job_name}.cmd")
                cmd = f"toil-cwl-runner --singularity --logFile output.log --retryCount 3 --disable-user-provenance --disable-host-provenance --stats --debug --disableCaching --defaultMemory 8G --maxCores 16 --maxDisk 128G --maxMemory 256G --not-strict --realTimeLogging --jobStore job-stores/ --tmpdir-prefix tmp/ --workDir work/ --maxLocalJobs 500 --outdir {res_dir} {pipeline.entrypoint} inputs.json > output.json"
                f.write(cmd)
            print("Copy input file")
            print(f"scp {job_name}.json ivkovic@pyr:/home/ivkovic/")
            print(f"scp {job_name}.cmd ivkovic@pyr:/home/ivkovic/")
            print(f"cd {work_dir}")
            print(f"cp /home/ivkovic/{job_name}.json ./inputs.json")
            print(f"cp /home/ivkovic/{job_name}.json ./cmd.sh")
            print("Run command")
