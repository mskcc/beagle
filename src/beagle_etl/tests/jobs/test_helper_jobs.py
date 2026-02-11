from mock import patch
from django.test import TestCase
from django.conf import settings
from beagle_etl.jobs.helper_jobs import locate_file
from beagle_etl.exceptions import FailedToLocateTheFileException


class TestHelperJobs(TestCase):
    def setUp(self):
        settings.MAPPING = {"/igo/delivery/FASTQ/": ["/juno/archive/msk/cmo/FASTQ/", "/juno/cmo/ccs/archive/FASTQs/"]}

    @patch("os.path.exists")
    def test_locate_file_argos_dir(self, exists):
        def side_effect(arg):
            if (
                arg
                == "/juno/archive/msk/cmo/FASTQ/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz"
            ):
                return True
            else:
                return False

        exists.side_effect = side_effect
        filepath = "/igo/delivery/FASTQ/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz"
        new_path = locate_file(filepath)
        self.assertEqual(
            new_path,
            "/juno/archive/msk/cmo/FASTQ/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz",
        )

    @patch("os.path.exists")
    def test_locate_file_tempo_dir(self, exists):
        def side_effect(arg):
            if (
                arg
                == "/juno/cmo/ccs/archive/FASTQs/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz"
            ):
                return True
            else:
                return False

        exists.side_effect = side_effect
        filepath = "/igo/delivery/FASTQ/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz"
        new_path = locate_file(filepath)
        self.assertEqual(
            new_path,
            "/juno/cmo/ccs/archive/FASTQs/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz",
        )

    @patch("os.path.exists")
    def test_locate_file_igo_dir(self, exists):
        def side_effect(arg):
            if (
                arg
                == "/igo/delivery/FASTQ/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz"
            ):
                return True
            else:
                return False

        exists.side_effect = side_effect
        filepath = "/igo/delivery/FASTQ/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz"
        new_path = locate_file(filepath)
        self.assertEqual(
            new_path,
            "/igo/delivery/FASTQ/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz",
        )

    @patch("os.path.exists")
    def test_locate_file_not_found(self, exists):
        exists.return_value = False
        filepath = "/igo/delivery/FASTQ/PITT_0319_BH3MV7BBXY/Project_08944_B/Sample_LTG002_P3_17096_L1_IGO_08944_B_1/LTG002_P3_17096_L1_IGO_08944_B_1_S82_R1_001.fastq.gz"
        with self.assertRaises(FailedToLocateTheFileException) as context:
            locate_file(filepath)
        self.assertTrue(f"Unable to locate file: {filepath} on file system" in context.exception.args)
