from mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from notifier.models import Notifier
from operator_manager.models import Operator, OperatorStatus, OperatorVersion
from operator_manager.tasks import build_operator_image, image_tag


class BuildOperatorImageTaskTest(TestCase):
    def setUp(self):
        self.operator = Operator.objects.create(
            name="Demo",
            github_url="https://github.com/x/y.git",
            version="v1",
            class_name="Demo",
            type=OperatorVersion.V2,
        )

    def test_image_tag(self):
        self.assertEqual(image_tag("Demo Operator", "v0.1.0"), "demo-operator:v0-1-0")

    @patch("operator_manager.tasks.OperatorRunner")
    @patch("operator_manager.tasks.GithubCache")
    def test_success(self, github_cache, operator_runner):
        github_cache.get.return_value = "/cache/y"
        operator_runner.return_value.build.return_value = ("sha256:abc", "demo:v1")
        build_operator_image(self.operator.id)
        github_cache.get.assert_called_once_with("https://github.com/x/y.git", "v1")
        github_cache.add.assert_not_called()
        operator_runner.assert_called_once_with("/cache/y", configuration_path="/cache/y/.voyager/config.json")
        operator_runner.return_value.build.assert_called_once_with(tag="demo:v1")
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.docker_image_tag, "demo:v1")
        self.assertEqual(self.operator.docker_image_id, "sha256:abc")
        self.assertEqual(self.operator.status, OperatorStatus.READY)

    @patch("operator_manager.tasks.OperatorRunner")
    @patch("operator_manager.tasks.GithubCache")
    def test_clones_when_not_cached(self, github_cache, operator_runner):
        github_cache.get.return_value = None
        github_cache.add.return_value = "/cache/y"
        operator_runner.return_value.build.return_value = ("sha256:abc", "demo:v1")
        build_operator_image(self.operator.id)
        github_cache.add.assert_called_once_with("https://github.com/x/y.git", "v1")

    @patch("operator_manager.tasks.OperatorRunner")
    @patch("operator_manager.tasks.GithubCache")
    def test_failure(self, github_cache, operator_runner):
        github_cache.get.return_value = "/cache/y"
        operator_runner.return_value.build.side_effect = RuntimeError("boom")
        build_operator_image(self.operator.id)
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.status, OperatorStatus.FAILED)
        self.assertIsNone(self.operator.docker_image_id)


class OperatorAPITest(APITestCase):
    url = "/v0/operator-manager/operators/"

    def setUp(self):
        self.user = User.objects.create_user(username="username", password="password", email="admin@gmail.com")
        self.client.force_authenticate(user=self.user)
        self.notifier = Notifier.objects.create(notifier_type="JIRA", default=True, board="TEST")
        # Migration 0002 copies the operators that beagle_etl data migrations create into the test DB
        Operator.objects.all().delete()
        self.v1 = Operator.objects.create(
            name="Legacy", type=OperatorVersion.V1, class_name="LegacyOperator", trigger=["IMPACT505"], active=True
        )
        self.v2 = Operator.objects.create(
            name="Demo",
            type=OperatorVersion.V2,
            class_name="DemoOperator",
            github_url="https://github.com/x/y.git",
            version="v1",
            status=OperatorStatus.READY,
            trigger=["WES"],
        )

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 2)

    def test_list_filters(self):
        for params, expected in (
            ({"type": "V2"}, [self.v2.id]),
            ({"status": "READY"}, [self.v2.id]),
            ({"active": "true"}, [self.v1.id]),
            ({"active": "false"}, [self.v2.id]),
            ({"name": "Legacy"}, [self.v1.id]),
            ({"trigger": "WES"}, [self.v2.id]),
        ):
            response = self.client.get(self.url, params)
            self.assertEqual(response.status_code, status.HTTP_200_OK, params)
            self.assertEqual([o["id"] for o in response.json()["results"]], expected, params)

    def test_list_invalid_filter(self):
        response = self.client.get(self.url, {"status": "BOGUS"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve(self):
        response = self.client.get("{}{}/".format(self.url, self.v2.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "Demo")
        self.assertEqual(data["type"], "V2")
        self.assertEqual(data["status"], "READY")
        self.assertEqual(data["trigger"], ["WES"])

    def test_retrieve_not_found(self):
        response = self.client.get("{}{}/".format(self.url, 9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("operator_manager.views.build_operator_image.delay")
    def test_create(self, build_delay):
        payload = {
            "name": "New",
            "type": "V2",
            "class_name": "NewOperator",
            "github_url": "https://github.com/x/new.git",
            "version": "v2",
            "trigger": ["IMPACT468"],
            "notifier": self.notifier.id,
            # read-only fields are ignored
            "status": "READY",
            "docker_image_tag": "evil:latest",
        }
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        operator = Operator.objects.get(id=response.json()["id"])
        build_delay.assert_called_once_with(operator.id)
        self.assertEqual(operator.type, OperatorVersion.V2)
        self.assertEqual(operator.status, OperatorStatus.INSTALLING)
        self.assertIsNone(operator.docker_image_tag)
        self.assertEqual(operator.notifier, self.notifier)
        self.assertFalse(operator.active)

    @patch("operator_manager.views.build_operator_image.delay")
    def test_create_v1_does_not_build(self, build_delay):
        payload = {"name": "Legacy New", "type": "V1", "class_name": "LegacyNewOperator"}
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        build_delay.assert_not_called()
        self.assertEqual(Operator.objects.get(id=response.json()["id"]).status, OperatorStatus.READY)

    def test_create_invalid(self):
        response = self.client.post(self.url, {"name": "Bad", "type": "V3", "trigger": "WES"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.json())
        self.assertIn("class_name", response.json())
        self.assertIn("trigger", response.json())

    @patch("operator_manager.views.build_operator_image.delay")
    def test_partial_update(self, build_delay):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                "{}{}/".format(self.url, self.v2.id), {"active": True, "trigger": ["WES", "IMPACT505"]}, format="json"
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        build_delay.assert_not_called()
        self.v2.refresh_from_db()
        self.assertTrue(self.v2.active)
        self.assertEqual(self.v2.trigger, ["WES", "IMPACT505"])
        self.assertEqual(self.v2.status, OperatorStatus.READY)

    @patch("operator_manager.views.build_operator_image.delay")
    def test_version_change_rebuilds(self, build_delay):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch("{}{}/".format(self.url, self.v2.id), {"version": "v2"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        build_delay.assert_called_once_with(self.v2.id)
        self.v2.refresh_from_db()
        self.assertEqual(self.v2.status, OperatorStatus.INSTALLING)

    def test_update(self):
        payload = {"name": "Legacy2", "type": "V1", "class_name": "LegacyOperator2", "trigger": []}
        response = self.client.put("{}{}/".format(self.url, self.v1.id), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.v1.refresh_from_db()
        self.assertEqual(self.v1.name, "Legacy2")
        self.assertEqual(self.v1.class_name, "LegacyOperator2")

    def test_delete_not_allowed(self):
        response = self.client.delete("{}{}/".format(self.url, self.v1.id))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Operator.objects.filter(id=self.v1.id).exists())
