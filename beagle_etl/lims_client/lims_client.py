import requests
from django.conf import settings
from beagle_etl.exceptions import FailedToFetchSampleException


class LIMSClient(object):

    @staticmethod
    def get_deliveries(timestamp):
        requestIds = requests.get('%s/LimsRest/api/getDeliveries' % settings.LIMS_URL,
                                  params={"timestamp": timestamp},
                                  auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
        if requestIds.status_code != 200:
            raise FailedToFetchSampleException("Failed to fetch new requests, status_code: %s" % requestIds.status_code)
        return requestIds.json()

    @staticmethod
    def get_request_samples(request_id):
        sample_ids = requests.get('%s/LimsRest/api/getRequestSamples' % settings.LIMS_URL,
                                  params={"request": request_id},
                                  auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
        if sample_ids.status_code != 200:
            raise FailedToFetchSampleException("Failed to fetch sampleIds for request %s, status_code: %s" % (request_id, sample_ids.status_code))
        return sample_ids.json()

    @staticmethod
    def get_sample_manifest(sample_id):
        sample_metadata = requests.get('%s/LimsRest/api/getSampleManifest' % settings.LIMS_URL,
                                      params={"igoSampleId": sample_id},
                                      auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
        if sample_metadata.status_code != 200:
            raise FailedToFetchSampleException("Failed to fetch SampleManifest for sampleId:%s, status_code: %s" % (sample_id, sample_metadata.status_code))
        return sample_metadata.json()

