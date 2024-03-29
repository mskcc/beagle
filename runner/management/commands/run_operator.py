from runner.models import Operator
from django.core.management.base import BaseCommand
from runner.operator.operator_factory import OperatorFactory
from runner.run.objects.run_object_factory import RunObjectFactory


class Command(BaseCommand):
    help = "Run Operator"

    def add_arguments(self, parser):
        parser.add_argument("--operator", type=str)
        parser.add_argument("--operator-version", type=str)
        parser.add_argument("--request-id", type=str)

    def handle(self, *args, **options):
        request_id = options["request_id"]
        operator_path = options["operator"]
        operator_version = options["operator_version"]
        print(f"Running {request_id} with operator {operator_path} version {operator_version}")

        operator = OperatorFactory.get_by_model(
            Operator.objects.get(class_name=operator_path, version=operator_version)
        )
        operator.request_id = request_id

        jobs = operator.get_jobs()
        runs = []
        results = []
        for job in jobs:
            run = job.create()
            runs.append(run)
            run_obj = RunObjectFactory.from_definition(str(run.id), job.inputs)
            run_obj.ready()
            run_obj.to_db()
            results.append(run_obj.dump_job())
            print(results)
