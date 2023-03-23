from rest_framework.test import APITestCase
from study.models import Study
from study.objects import StudyObject
from file_system.models import Request, Sample, FileGroup
from runner.models import Run, RunStatus, ProtocolType, Pipeline


class TestStudy(APITestCase):

    def setUp(self):
        self.request = Request.objects.create(request_id='08944_B',
                                              lab_head_email="labhead@mskcc.org")
        self.sample_t = Sample.objects.create(sample_id='08944_B_1',
                                              sample_name="LTG002_P3_17096_L1",
                                              cmo_sample_name="C-MP76JR-X001-d",
                                              sample_type="Primary",
                                              sample_class="PDX",
                                              tumor_or_normal="Tumor")
        self.sample_n = Sample.objects.create(sample_id='08944_B_2',
                                              sample_name="LTG002_P3_17096_L1",
                                              cmo_sample_name="C-MP76JR-X001-d",
                                              sample_type="Primary",
                                              sample_class="PDX",
                                              tumor_or_normal="Normal")
        self.fg = FileGroup.objects.create(name="test", slug="test")
        self.pipeline = Pipeline.objects.create(name="pipeline",
                                                output_directory="/tmp",
                                                output_file_group=self.fg)
        self.run_1 = Run.objects.create(app=self.pipeline,
                                        run_type=ProtocolType.CWL,
                                        name="Test Run 1",
                                        status=RunStatus.COMPLETED,
                                        notify_for_outputs=[]
                                        )
        self.run_1.samples.add(self.sample_n)
        self.run_1.samples.add(self.sample_t)
        self.study = Study.objects.create(study_id="set_testname")
        self.study.requests.add(self.request)
        self.study.samples.add(self.sample_n)
        self.study.samples.add(self.sample_t)

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
        self.assertEqual(len(study.run_ids), 2)



