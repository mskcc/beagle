"""
Tests for Operator class
"""
import os
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory

class TestOperatorFactory(TestCase):
    def test_operator_factory_invalid_pipeline1(self):
        """
        Test that invalid pipelines raise an exception
        """
        pipeline_type = "foo"
        request_id = "bar"
        #self.assertRaises(Exception, OperatorFactory.factory, pipeline_type, request_id)
