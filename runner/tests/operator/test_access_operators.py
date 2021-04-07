from django.test import TestCase

from file_system.models import File, FileMetadata, FileGroup
from runner.models import Run, Port, PortType, Pipeline, RunStatus
from runner.operator.access import get_unfiltered_matched_normal, DMP_IMPACT_ASSAYS, ACCESS_ASSAY


TEST_PATIENT_ID = 'C-000884'
REQUEST_ID = 'access_legacy_test_request'


class TestMatchedNormalSearch(TestCase):

    def test_matched_igo_normal_same_request(self):
        """
        Test a matching unfiltered normal, same request ID
        """
        file_name = 'C-000884-N001-d_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam'
        file_path = '/test/' + file_name

        fg = FileGroup.objects.create(name='test', slug='test')
        pipeline = Pipeline.objects.create(name='pipeline', output_directory='/tmp', output_file_group=fg)

        run = Run.objects.create(
            tags={'requestId': REQUEST_ID},
            app=pipeline,
            output_directory='/test',
            status=RunStatus.FAILED,
            notify_for_outputs=[],
        )
        file = File.objects.create(path=file_path, file_name=file_name, file_group=fg)
        port = Port.objects.create(run=run, port_type=PortType.OUTPUT)
        port.files.add(file)

        normal, sample_id = get_unfiltered_matched_normal(TEST_PATIENT_ID, REQUEST_ID)
        self.assertEqual(normal.file_name, file_name)

    def test_matched_igo_normal_different_request(self):
        """
        Test a matching unfiltered normal, different request ID
        """
        file_name = 'C-000884-N001-d_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam'
        file_path = '/test/' + file_name

        fg = FileGroup.objects.create(name='test', slug='test')
        pipeline = Pipeline.objects.create(name='pipeline', output_directory='/tmp', output_file_group=fg)

        run = Run.objects.create(
            tags={'requestId': REQUEST_ID},
            app=pipeline,
            output_directory='/test',
            status=RunStatus.FAILED,
            notify_for_outputs=[],
        )
        file = File.objects.create(path=file_path, file_name=file_name, file_group=fg)
        port = Port.objects.create(run=run, port_type=PortType.OUTPUT)
        port.files.add(file)

        normal, sample_id = get_unfiltered_matched_normal(TEST_PATIENT_ID, REQUEST_ID)
        self.assertEqual(normal.file_name, file_name)

    def test_matched_dmp_normal_access(self):
        """
        Test matching unfiltered normal DMP ACCESS
        """
        file_name = '000884-unfilter.bam'
        file_path = '/test/' + file_name

        fg = FileGroup.objects.create(name='test', slug='test')
        file = File.objects.create(
            path=file_path,
            file_name=file_name,
            file_group=fg
        )

        FileMetadata.objects.create(
            file=file,
            metadata={
                'cmo_assay': ACCESS_ASSAY,
                'type': 'N',
                'patient': {
                    'cmo': TEST_PATIENT_ID.lstrip('C-')
                }
            }
        )

        normal, sample_id = get_unfiltered_matched_normal(TEST_PATIENT_ID, REQUEST_ID)
        self.assertEqual(normal.file_name, file_name)

    def test_matched_dmp_normal_impact(self):
        """
        Test matching unfiltered normal DMP IMPACT
        """
        file_name = 'C-000884.bam'
        file_path = '/test/' + file_name

        fg = FileGroup.objects.create(name='test', slug='test')
        file = File.objects.create(
            path=file_path,
            file_name=file_name,
            file_group=fg
        )

        FileMetadata.objects.create(
            file=file,
            metadata={
                'cmo_assay': DMP_IMPACT_ASSAYS[0],
                'type': 'N',
                'patient': {
                    'cmo': TEST_PATIENT_ID.lstrip('C-')
                }
            }
        )

        normal, sample_id = get_unfiltered_matched_normal('C-000884', REQUEST_ID)
        self.assertEqual(normal.file_name, file_name)

    def test_empty_genotyping_result(self):
        """
        Test no matching normal found
        """
        normal, sample_id = get_unfiltered_matched_normal('C-000884', REQUEST_ID)
        self.assertIsNone(normal)
        self.assertEqual(sample_id, '')
