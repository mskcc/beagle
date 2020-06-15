"""
Tests for Assay API View
"""
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from beagle_etl.models import Assay



class TestAssayAPIView(APITestCase):

    """
    Tests the Assay API View
    """

    def setUp(self):
        """
        Setup the test case
        """
        admin_user = User.objects.create_superuser('admin', 'sample_email', 'password')
        self.client.force_authenticate(user=admin_user)
        assay = Assay.objects.first()
        assay.all = ['IMPACT468',
                     'HemePACT',
                     'HemePACT_v4',
                     'DisabledAssay',
                     'HoldAssay']
        assay.disabled = ['DisabledAssay']
        assay.hold = ['HoldAssay']
        assay.save()
        self.api_root = '/v0/etl/assay'

    def test_get_assays(self):
        """
        Test getting the assay object
        """
        response = self.client.get(self.api_root)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

#    def test_get_multipled_assays(self):
#        """
#        Test case where multiple assay objects exists
#        """
#        new_assay = Assay(all=['IMPACT468'])
#        new_assay.save()
#        response = self.client.get(self.api_root)
#        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update(self):
        """
        Test updating the assay object
        """
        extra_assay = 'ExtraAssay'
        new_assay_request = {'all':['IMPACT468',
                                    'HemePACT',
                                    'HemePACT_v4',
                                    'DisabledAssay',
                                    'HoldAssay',
                                    extra_assay]}
        response = self.client.post(self.api_root, new_assay_request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assay = Assay.objects.first()
        self.assertTrue(extra_assay in assay.all)

    def test_all_truncate(self):
        """
        Test attempt to truncate all in the assay object
        """
        new_assay_request = {'all':['IMPACT468']}
        response = self.client.post(self.api_root, new_assay_request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_disabled_does_not_exist(self):
        """
        Test attempt to add a disabled assay not in all
        """
        extra_assay = 'ExtraAssay'
        new_assay_request = {'disabled':[extra_assay]}
        response = self.client.post(self.api_root, new_assay_request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hold_does_not_exist(self):
        """
        Test attempt to add hold assay not in all
        """
        extra_assay = 'ExtraAssay'
        new_assay_request = {'hold':[extra_assay]}
        response = self.client.post(self.api_root, new_assay_request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assay_in_hold_and_disabled(self):
        """
        Test attempt to add an assay in disabled thats already in hold
        """
        extra_assay = 'HoldAssay'
        new_assay_request = {'disabled': [extra_assay]}
        response = self.client.post(self.api_root, new_assay_request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
