"""
Tests for Operator class
"""
from django.test import TestCase
from runner.operator.operator import Operator

class TestOperator(TestCase):
    def test_operator_instance(self):
        """
        Test that an Operator instance can be created and it has the correct attributes

        The base Operator currently lacks implementation for instantiation without the OperatorFactory
        """
        operator_name = "foo"
        request_id = "bar"
        self.assertRaises(Exception, Operator, operator_name, request_id)
