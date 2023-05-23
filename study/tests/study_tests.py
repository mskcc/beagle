from mock import patch, Mock
from datetime import datetime
from rest_framework.test import APITestCase
from study.models import Study
from study.objects import StudyObject
from file_system.models import Request, Sample, FileGroup
from runner.models import Run, RunStatus, ProtocolType, Pipeline, PipelineName


class TestStudy(APITestCase):
    def setUp(self):
        self.request = Request.objects.create(request_id="08944_B", lab_head_email="labhead@mskcc.org")
        self.sample_t_1 = Sample.objects.create(
            sample_id="08944_B_1",
            sample_name="LTG002_P3_17096_L1",
            cmo_sample_name="C-MP76JR-X001-d",
            sample_type="Primary",
            sample_class="PDX",
            tumor_or_normal="Tumor",
        )
        self.sample_n_1 = Sample.objects.create(
            sample_id="08944_B_2",
            sample_name="LTG002_P3_17096_L1",
            cmo_sample_name="C-MP76JR-X002-d",
            sample_type="Primary",
            sample_class="PDX",
            tumor_or_normal="Normal",
        )
        self.sample_t_2 = Sample.objects.create(
            sample_id="08944_B_3",
            sample_name="LTG002_P3_17096_L1",
            cmo_sample_name="C-MP76JR-X003-d",
            sample_type="Primary",
            sample_class="PDX",
            tumor_or_normal="Tumor",
        )
        self.sample_n_2 = Sample.objects.create(
            sample_id="08944_B_4",
            sample_name="LTG002_P3_17096_L1",
            cmo_sample_name="C-MP76JR-X004-d",
            sample_type="Primary",
            sample_class="PDX",
            tumor_or_normal="Normal",
        )
        self.fg = FileGroup.objects.create(name="test", slug="test")
        self.pipeline_name = PipelineName.objects.create(name="Argos")
        self.pipeline = Pipeline.objects.create(
            name="pipeline", pipeline_name=self.pipeline_name, output_directory="/tmp", output_file_group=self.fg
        )
        old_run_date = datetime(2020, 1, 1, 12, 0, 0)
        with patch("django.utils.timezone.now", Mock(return_value=old_run_date)):
            self.run_1 = Run.objects.create(
                app=self.pipeline,
                run_type=ProtocolType.CWL,
                name="Test Run 1",
                status=RunStatus.COMPLETED,
                notify_for_outputs=[],
            )
        self.run_1.samples.add(self.sample_n_1)
        self.run_1.samples.add(self.sample_t_1)
        new_run_date = datetime(2021, 1, 1, 12, 0, 0)
        with patch("django.utils.timezone.now", Mock(return_value=new_run_date)):
            self.run_2 = Run.objects.create(
                app=self.pipeline,
                run_type=ProtocolType.CWL,
                name="Test Run 1",
                status=RunStatus.COMPLETED,
                notify_for_outputs=[],
            )
        self.run_2.samples.add(self.sample_n_1)
        self.run_2.samples.add(self.sample_t_1)
        with patch("django.utils.timezone.now", Mock(return_value=new_run_date)):
            self.run_2 = Run.objects.create(
                app=self.pipeline,
                run_type=ProtocolType.CWL,
                name="Test Run 1",
                status=RunStatus.COMPLETED,
                notify_for_outputs=[],
            )
        with patch("django.utils.timezone.now", Mock(return_value=new_run_date)):
            self.run_3 = Run.objects.create(
                app=self.pipeline,
                run_type=ProtocolType.CWL,
                name="Test Run 1",
                status=RunStatus.COMPLETED,
                notify_for_outputs=[],
            )
        self.run_3.samples.add(self.sample_n_2)
        self.run_3.samples.add(self.sample_t_2)
        self.study = Study.objects.create(study_id="set_labhead")
        self.study.requests.add(self.request)
        self.study.samples.add(self.sample_n_1)
        self.study.samples.add(self.sample_t_1)
        self.study.samples.add(self.sample_n_2)
        self.study.samples.add(self.sample_t_2)

    def test_get_study_by_request(self):
        study_objects = StudyObject.get_by_request("08944_B")
        self.assertEqual(len(study_objects), 1)
        self.assertEqual(study_objects[0].db_object.id, self.study.id)

    def test_get_study_by_lab_head(self):
        study_objects = StudyObject.get_by_lab_head("labhead@mskcc.org")
        self.assertEqual(len(study_objects), 1)
        self.assertEqual(study_objects[0].db_object.id, self.study.id)

    def test_get_run_ids(self):
        study = StudyObject.from_db(self.study.study_id)
        run_ids = study.run_ids
        self.assertEqual(list(run_ids.keys()), ["Argos"])
        self.assertEqual(len(run_ids["Argos"]), 2)

    def test_project_prefixes(self):
        expected = {"Argos": ["08944_B_1_08944_B_2", "08944_B_3_08944_B_4"]}
        study = StudyObject.from_db(self.study.study_id)
        self.assertDictEqual(study.project_prefixes, expected)
