from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from file_system.models import File, FileGroup, FileType, Storage, StorageType
from file_manager.models import (
    FileProviderStatus,
    FileProviderJob,
    SampleProviderJob,
)
from file_manager.dashboard import build_dashboard_payload


class DashboardPayloadTest(TestCase):
    def setUp(self):
        self.storage = Storage.objects.create(name="test_storage", type=StorageType.LOCAL)
        self.file_group = FileGroup.objects.create(name="test_group", storage=self.storage)
        self.file_type = FileType.objects.create(name="fastq")

    def _make_file(self, name):
        return File.objects.create(
            file_name=name,
            path=f"/original/{name}",
            file_type=self.file_type,
            file_group=self.file_group,
        )

    def _make_file_job(self, sample_job, name, status):
        f = self._make_file(name)
        return FileProviderJob.objects.create(
            file_object=f,
            original_path=f"/original/{name}",
            staged_path=f"/staged/{name}",
            status=status,
            sample_job=sample_job,
        )

    def test_only_active_samples_included(self):
        SampleProviderJob.objects.create(
            sample_id="S_active", status=FileProviderStatus.IN_PROGRESS, total_files=2, completed_files=1
        )
        SampleProviderJob.objects.create(
            sample_id="S_scheduled", status=FileProviderStatus.SCHEDULED, total_files=2, completed_files=0
        )
        SampleProviderJob.objects.create(
            sample_id="S_done", status=FileProviderStatus.COMPLETED, total_files=1, completed_files=1
        )

        payload = build_dashboard_payload()
        ids = {s["sample_id"] for s in payload["samples"]}

        self.assertIn("S_active", ids)
        self.assertIn("S_scheduled", ids)
        self.assertNotIn("S_done", ids)

    def test_files_bucketed_by_status(self):
        sample = SampleProviderJob.objects.create(
            sample_id="S1", status=FileProviderStatus.IN_PROGRESS, total_files=5, completed_files=2
        )
        self._make_file_job(sample, "sched1.fastq", FileProviderStatus.SCHEDULED)
        self._make_file_job(sample, "copy1.fastq", FileProviderStatus.IN_PROGRESS)
        self._make_file_job(sample, "done1.fastq", FileProviderStatus.COMPLETED)
        self._make_file_job(sample, "done2.fastq", FileProviderStatus.COMPLETED)
        self._make_file_job(sample, "fail1.fastq", FileProviderStatus.FAILED)

        payload = build_dashboard_payload()
        s = next(s for s in payload["samples"] if s["sample_id"] == "S1")

        self.assertEqual(s["status"], "IN_PROGRESS")
        self.assertEqual(s["completed"], 2)
        self.assertEqual(s["total"], 5)
        self.assertEqual(s["files"]["scheduled"], ["sched1.fastq"])
        self.assertEqual(s["files"]["copying"], ["copy1.fastq"])
        self.assertEqual(s["files"]["done_count"], 2)
        self.assertEqual(s["files"]["failed"], ["fail1.fastq"])

    def test_payload_has_generated_at(self):
        payload = build_dashboard_payload()
        self.assertIn("generated_at", payload)
        self.assertIn("samples", payload)


class DashboardViewTest(TestCase):
    def test_status_endpoint_requires_login(self):
        url = reverse("admin:file_manager_dashboard_status")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_status_endpoint_returns_json_for_admin(self):
        User = get_user_model()
        admin = User.objects.create_superuser("dash_admin", "a@b.com", "pass")
        self.client.force_login(admin)

        url = reverse("admin:file_manager_dashboard_status")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        data = resp.json()
        self.assertIn("samples", data)

    def test_dashboard_page_renders_for_admin(self):
        User = get_user_model()
        admin = User.objects.create_superuser("dash_admin2", "a@b.com", "pass")
        self.client.force_login(admin)

        url = reverse("admin:file_manager_dashboard")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
