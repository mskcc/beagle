"""
Tests for Roslin QC Operator class
"""
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from runner.operator.roslin_qc_operator.roslin_qc_operator import RoslinQcOperator
class TestOperatorFactory(TestCase):
    def test_true(self):
        self.assertTrue(True)

    def test_operator_factory_roslin_qc1(self):
        """
        Test that a Roslin QC operator instance can be created
        """
        pipeline_type = "roslin-qc"
        request_id = "bar"
        operator = OperatorFactory.factory(pipeline_type, request_id)
        self.assertTrue(isinstance(operator, RoslinQcOperator))
        self.assertTrue( operator.pipeline_id == "replace-this-with-pipeline-id")
        self.assertTrue( operator.operator == "roslin-qc")
        self.assertTrue( operator.request_id == "bar")
        self.assertTrue( operator._jobs == [])
        self.assertTrue( len(operator.files) == 0)
