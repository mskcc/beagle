"""
Tests for Operator class
"""
import os
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from beagle_etl.models import Operator

class TestOperatorFactory(TestCase):
    def test_operator_factory_invalid_pipeline1(self):
        """
        Test that invalid pipelines raise an exception
        """
        pipeline_type = "foo"
        request_id = "bar"
        self.assertRaises(Exception, OperatorFactory.get_by_model, pipeline_type, request_id=request_id)

    def test_operator_factory_call(self):
    	"""
    	Test operator call from factory
    	"""
    	first_operator = OperatorFactory.get_by_model(Operator.objects.first())
    	self.assertTrue(first_operator != None)

    def test_operator_invalid_version(self):
        """
        Test that invalid pipelines raise an exception
        """
        self.assertRaises(Exception, OperatorFactory.get_by_model, Operator.objects.first(), version='vDoes_not_exist')

