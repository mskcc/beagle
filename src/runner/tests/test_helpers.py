from django.test import TestCase
from runner.operator.helper import format_sample_name


class TestHelper(TestCase):
    def test_format_sample_name(self):
        """
        Test that format sample name works as expected
        """
        sample_name_malformed = None
        sample_name_ci_tag = "s_C_12345H_T"
        sample_name_old = "C-12345H-T"
        sample_name_random = "ABCDEFGHIJKLMN"

        self.assertEqual(format_sample_name(sample_name_malformed, "Primary"), "sampleNameMalformed")
        self.assertEqual(
            format_sample_name(sample_name_random, "Primary"), "s_" + sample_name_random
        )  # should be prefixed with 's_'
        self.assertEqual(format_sample_name(sample_name_ci_tag, "Primary"), sample_name_ci_tag)  # should be unchanged
        self.assertEqual(format_sample_name(sample_name_old, "Primary"), sample_name_ci_tag)  # should be converted
