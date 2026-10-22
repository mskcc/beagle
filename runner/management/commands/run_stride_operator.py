from django.core.management.base import BaseCommand, CommandError

from runner.models import Operator
from runner.operator.operator_factory import OperatorFactory
from runner.run.objects.run_object_factory import RunObjectFactory

STRIDE_CLASS_NAME = "runner.operator.access.stride.StrideOperator"


class Command(BaseCommand):
    help = (
        "Run the STRiDE operator directly (no Celery/notifications) against an "
        "explicit list of DMP clinical ACCESS tumor sample ids."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--sample-ids",
            type=str,
            nargs="+",
            required=True,
            help="DMP clinical ACCESS tumor sample ids, e.g. P-0109895-T03-XS2",
        )
        parser.add_argument("--operator-version", type=str, default=None)

    def handle(self, *args, **options):
        sample_ids = options["sample_ids"]
        operator_version = options["operator_version"]
        print(f"Running STRiDE operator for {len(sample_ids)} sample(s): {sample_ids}")

        query = {"class_name": STRIDE_CLASS_NAME}
        if operator_version:
            query["version"] = operator_version
        operator_model = Operator.objects.filter(**query).order_by("-version").first()
        if not operator_model:
            raise CommandError(f"No registered Operator found for {query}")

        operator = OperatorFactory.get_by_model(operator_model)
        jobs = operator.get_jobs(sample_ids=sample_ids)
        for job in jobs:
            run = job.create()
            run_obj = RunObjectFactory.from_definition(str(run.id), job.inputs)
            run_obj.ready()
            run_obj.to_db()
            print(f"Created run {run.id}")
