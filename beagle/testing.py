import os
import requests


def _resolve_secondary_file(filename, sufix):
    while sufix.startswith('^'):
        sufix = sufix[1:]
        filename = os.path.splitext(filename)[0]
    return filename + sufix


if __name__ == '__main__':
    print('filename')
    requestIds = requests.get('https://igolims.mskcc.org:8443/LimsRest/getRecentDeliveries',
                              params={"time": 5, "units": "d"},
                              auth=('pms', 'tiagostarbuckslightbike'), verify=False)
    print(requestIds.json())
    for req in requestIds.json()[0].get('samples'):
        sampleIds = requests.get('https://igolims.mskcc.org:8443/LimsRest/api/getRequestSamples',
                                 params={"request": req['project']},
                                 auth=('accessbot', 'egretonapond'), verify=False)
        print(sampleIds.json())
        for sam in sampleIds.json().get('samples', []):
            sampleMetadata = requests.get('https://igolims.mskcc.org:8443/LimsRest/api/getSampleManifest',
                                          params={"igoSampleId": sam['igoSampleId']},
                                          auth=('accessbot', 'egretonapond'), verify=False)
            print(sampleMetadata.json())
