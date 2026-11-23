from django.contrib.auth.models import User
from django.test import TestCase
from operator_manager.models import Operator, OperatorRun, OperatorTrigger
from runner.models import Pipeline, Run, RunStatus, TriggerAggregateConditionType, TriggerRunType


class OperatorTriggerAdminTest(TestCase):
    fixtures = [
        "file_system.filegroup.json",
        "file_system.storage.json",
        "operator_manager.operator.json",
        "runner.pipeline.json",
    ]

    def setUp(self):
        self.client.force_login(User.objects.create_superuser("admin", "admin@example.com", "password"))
        self.from_operator, self.to_operator = Operator.objects.order_by("id")[:2]
        self.trigger = OperatorTrigger.objects.create(
            from_operator=self.from_operator,
            to_operator=self.to_operator,
            run_type=TriggerRunType.AGGREGATE,
            aggregate_condition=TriggerAggregateConditionType.ALL_RUNS_SUCCEEDED,
        )
        template = Pipeline.objects.filter(operator=self.from_operator).first() or Pipeline.objects.first()
        template.operator = self.from_operator
        template.save()
        self.pipeline = Pipeline.objects.get(pk=template.pk)
        # A second pipeline on the same operator
        template.pk = None
        template.name = "second pipeline"
        template.default = False
        template.save()

    def test_changelist_renders_graph(self):
        response = self.client.get("/admin/operator_manager/operatortrigger/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("admin/operator_manager/operatortrigger/change_list.html", [t.name for t in response.templates])
        graph = response.context["trigger_graph"]
        nodes = {n["id"]: n for n in graph["nodes"]}
        self.assertEqual(set(nodes), {str(self.from_operator.id), str(self.to_operator.id)})
        pipelines = nodes[str(self.from_operator.id)]["pipelines"]
        self.assertEqual(len(pipelines), Pipeline.objects.filter(operator=self.from_operator).count())
        self.assertGreaterEqual(len(pipelines), 2)
        self.assertEqual(
            graph["edges"],
            [
                {
                    "id": str(self.trigger.id),
                    "source": str(self.from_operator.id),
                    "target": str(self.to_operator.id),
                    "run_type": "AGGREGATE",
                    "condition": "ALL_RUNS_SUCCEEDED",
                    "url": f"/admin/operator_manager/operatortrigger/{self.trigger.id}/change/",
                }
            ],
        )
        self.assertContains(response, 'id="trigger-graph-data"')
        self.assertContains(response, f'data-operator="{self.from_operator.id}"')

    def test_operator_run_changelist_links_runs(self):
        operator_run = OperatorRun.objects.create(operator=self.from_operator, num_total_runs=1)
        run = Run.objects.create(
            name="run", status=RunStatus.RUNNING, operator_run=operator_run, app=self.pipeline, notify_for_outputs=[]
        )
        response = self.client.get("/admin/operator_manager/operatorrun/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"/admin/runner/run/{run.id}/change/")
