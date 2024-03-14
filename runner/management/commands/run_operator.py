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
        parser.add_argument("--output-dir", type=str)

    def handle(self, *args, **options):
        request_id = options["request_id"]
        run_ids = options["run_ids"]
        operator_path = options["operator"]
        operator_version = options["operator_version"]
        job_name = options["job_name"]
        output_dir = options["output_dir"]

        print(f"Running {request_id} with operator {operator_path} version {operator_version}")

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

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

        job_name_tumor_sample = False
        if not job_name:
            job_name_tumor_sample = True

        for job in jobs:
            run = job.create()
            runs.append(run)
            run_obj = RunObjectFactory.from_definition(str(run.id), job.inputs)
            run_obj.ready()
            run_obj.to_db()

            inputs = run_obj.dump_job()["inputs"]
            if job_name_tumor_sample:
                job_name = inputs['tumor']['ID']
            print(f"Creating job for tumor {job_name}")
            work_dir = os.path.join(self.WORK_DIRECTORY, request_id, job_name)
            res_dir = os.path.join(self.RES_DIRECTORY, request_id, job_name)
            with open(f"{output_dir}/{job_name}_inputs.json", "w") as f:
                print(f"Dumping input file into {job_name}.json")
                json.dump(inputs, f)
            with open(f"{output_dir}/{job_name}.cmd", "w") as f:
                print(f"Dumping cmd line into file {job_name}.sh")
                f.write("#!/bin/bash\n")
                prepare_workdir_cmd = f"mkdir {work_dir}\n"
                f.write(prepare_workdir_cmd)
                prepare_resdir_cmd = f"mkdir {res_dir}\n"
                f.write(prepare_resdir_cmd)
                copy_argos = f"cp -R /rtsess01/compute/juno/bic/ROOT/work/voyager/argos-cmd-template {work_dir}/argos-cmd\n"
                f.write(copy_argos)
                move_input_json = f"cp /rtsess01/compute/juno/bic/ROOT/work/voyager/jobs/{output_dir}/{job_name}_inputs.json {work_dir}/argos-cmd/inputs.json\n"
                f.write(move_input_json)
                cd_to_workdir = f"cd {work_dir}/argos-cmd\n"
                f.write(cd_to_workdir)
                source_env = "source set_env.sh\n"
                f.write(source_env)
                run_cmd = f"toil-cwl-runner --singularity --logFile output.log --retryCount 3 --disable-user-provenance --disable-host-provenance --stats --debug --disableCaching --defaultMemory 8G --maxCores 16 --maxDisk 128G --maxMemory 256G --not-strict --realTimeLogging --jobStore job-stores/ --tmpdir-prefix tmp/ --workDir work/ --maxLocalJobs 500 --outdir {res_dir} argos-cwl/{pipeline.entrypoint} inputs.json > output.json\n"
                f.write(run_cmd)
            with open("tasks.sh", "a") as f:
                f.write(f"/rtsess01/compute/juno/bic/ROOT/work/voyager/jobs/{output_dir}/{job_name}.cmd\n")
        print(f"scp -r {output_dir} ivkovic@pyr:/home/ivkovic/")
