import copy
import json
import os.path
import requests
from datetime import datetime
from django.conf import settings
from file_system.models import Request
from file_system.models import FileGroup, FileType, File, FileMetadata
from file_system.repository import FileRepository
from beagle_etl.copy_service.copy_service import CopyService
from beagle_etl.jobs.metadb_jobs import R1_or_R2, create_pooled_normal
from file_system.helper.checksum import sha1
from runner.operator.helper import format_sample_name


DIRECTORY = "/home/voyager/OLD_FILES_COPIED_FROM_LIMS/REQUESTS"

LIMS_URL = "https://igolims.mskcc.org:8443"
LIMS_USERNAME = ""
LIMS_PASSWORD = ""


def get_file_name(diretory, requestId):
    return os.path.join(diretory, f"request_{requestId}.json")


def get_request_smile(directory, requestId):
    response = requests.get(f"http://smile.mskcc.org:3000/request/{requestId}/")
    if response.status_code == 200:
        with open(get_file_name(directory, requestId), "w") as f:
            json.dump(response.json(), f)
    else:
        print(f"Fail to import {requestId}")
        with open(os.path.join(directory, "missing_requests.txt"), "w+") as f:
            f.write(f"{requestId}\n")


def get_request_lims(directory, requestId):
    request_data = get_request_samples(requestId)
    if not request_data:
        print(f"Fail to import request {requestId}")
        with open(os.path.join(directory, "missing_requests.txt"), "a") as f:
            f.write(f"{requestId}\n")
        return
    samples = []
    for sample in request_data.get("samples", []):
        samples.extend(get_sample_manifest(directory, sample["igoSampleId"]))
    request_data["limsSampleManifests"] = samples
    with open(get_file_name(directory, requestId), "w") as f:
        json.dump(request_data, f)


def get_request_samples(request_id):
    sample_ids = requests.get(
        f"{LIMS_URL}/LimsRest/api/getRequestSamples",
        params={"request": request_id},
        auth=(LIMS_USERNAME, LIMS_PASSWORD),
        verify=False,
    )
    if sample_ids.status_code == 200:
        return sample_ids.json()
    print(f"LIMS ERROR {request_id}")
    return {}


def get_sample_manifest(directory, sample_id):
    sample_metadata = requests.get(
        "%s/LimsRest/api/getSampleManifest" % LIMS_URL,
        params={"igoSampleId": sample_id},
        auth=(LIMS_USERNAME, LIMS_PASSWORD),
        verify=False,
    )
    if sample_metadata.status_code == 200:
        try:
            return sample_metadata.json()
        except Exception as e:
            print(f"LIMS ERROR {sample_id}")
            with open(os.path.join(directory, "missing_samples.txt"), "a") as f:
                f.write(f"{sample_id}\n")
            return [{"ERROR_JSON": sample_id}]
    print(f"LIMS ERROR {sample_id}")
    with open(os.path.join(directory, "missing_samples.txt"), "a") as f:
        f.write(f"{sample_id}\n")
    return [{"ERROR": sample_id}]


def import_all_requests(directory, missing_requests):
    count = len(missing_requests)
    curr = 0
    for requestId in missing_requests:
        if not os.path.exists(get_file_name(directory, requestId)):
            get_request_lims(directory, requestId)
        curr += 1
        print(f"STATUS: {curr}/{count}")


def format_metadata(original_metadata):
    metadata = copy.deepcopy(original_metadata)
    sample_name = original_metadata.get("cmoSampleName", None)
    sample_class = original_metadata.get("cmoSampleClass", None)
    # ciTag is the new field which needs to be used for the operators
    metadata["datasource"] = "igo"
    metadata["patientAliases"] = ({"namespace": "cmoId", "value": metadata["cmoPatientId"]},)
    metadata["ciTag"] = format_sample_name(sample_name, sample_class)
    metadata["sequencingCenter"] = "MSKCC"
    metadata["platform"] = "Illumina"
    metadata["sampleType"] = metadata.pop("cmoSampleClass")
    metadata["sampleClass"] = metadata.pop("specimenType")
    metadata["cmoInfoIgoId"] = metadata["primaryId"]
    metadata["sampleAliases"] = [
        {"namespace": "igoId", "value": metadata["primaryId"]},
        {"namespace": "investigatorId", "value": metadata["investigatorSampleId"]},
    ]
    metadata["additionalProperties"] = {"igoRequestId": metadata["igoRequestId"], "isCmoSample": True}
    return metadata


def create_file(path, request_id, file_group_id, file_type, igocomplete, data, library, run, request_metadata, r):
    try:
        file_group_obj = FileGroup.objects.get(id=file_group_id)
        file_type_obj = FileType.objects.filter(name=file_type).first()
        lims_metadata = copy.deepcopy(data)
        library_copy = copy.deepcopy(library)
        lims_metadata[settings.REQUEST_ID_METADATA_KEY] = request_id
        lims_metadata["igoComplete"] = igocomplete
        lims_metadata["R"] = r
        for k, v in library_copy.items():
            lims_metadata[k] = v
        for k, v in run.items():
            lims_metadata[k] = v
        for k, v in request_metadata.items():
            lims_metadata[k] = v
        metadata = format_metadata(lims_metadata)
    except Exception as e:
        print("Failed to parse metadata for file %s path" % path)
        raise
    recipe = metadata.get(settings.RECIPE_METADATA_KEY, "")
    new_path = CopyService.remap(recipe, path)  # Get copied file path
    f = FileRepository.filter(path=new_path).first()
    if not f:
        try:
            checksum = sha1(new_path)
            f = File.objects.create(
                file_name=os.path.basename(new_path),
                path=new_path,
                file_group=file_group_obj,
                file_type=file_type_obj,
                checksum=checksum,
            )
            f.save()
            fm = FileMetadata(file=f, metadata=metadata)
            fm.save()
        except Exception as e:
            print(e)
    else:
        print(f"Already imported {new_path}")


def import_request(data):
    request_id = data.get("requestId")
    if data.get("deliveryDate"):
        delivery_date = datetime.fromtimestamp(data["deliveryDate"] / 1000)
    else:
        delivery_date = datetime.now()
    Request.objects.get_or_create(request_id=request_id, defaults={"delivery_date": delivery_date})

    project_id = request_id.split("_")[0]
    recipe = data.get("recipe")

    project_manager_name = data.get("projectManagerName")
    pi_email = data.get("piEmail")
    lab_head_name = data.get("labHeadName")
    lab_head_email = data.get("labHeadEmail")
    investigator_name = data.get("investigatorName")
    investigator_email = data.get("investigatorEmail")
    data_analyst_name = data.get("dataAnalystName")
    data_analyst_email = data.get("dataAnalystEmail")
    other_contact_emails = data.get("otherContactEmails")
    data_access_email = data.get("dataAccessEmails")
    qc_access_email = data.get("qcAccessEmails")

    request_metadata = {
        "igoRequestId": request_id,
        "igoProjectId": project_id,
        "genePanel": recipe,
        "projectManagerName": project_manager_name,
        "piEmail": pi_email,
        "labHeadName": lab_head_name,
        "labHeadEmail": lab_head_email,
        "investigatorName": investigator_name,
        "investigatorEmail": investigator_email,
        "dataAnalystName": data_analyst_name,
        "dataAnalystEmail": data_analyst_email,
        "otherContactEmails": other_contact_emails,
        "dataAccessEmails": data_access_email,
        "qcAccessEmails": qc_access_email,
    }

    samples = data.get("samples")
    sampleManifests = data.get("limsSampleManifests")
    for idx, sample in enumerate(samples):
        igocomplete = sample.get("igoComplete")
        sample_data = sampleManifests[idx]
        sample_id = sample_data.pop("igoId")
        sample_data["primaryId"] = sample_id
        sample_data["oncotreeCode"] = sample_data.pop("oncoTreeCode")
        libraries = sample_data.pop("libraries")
        for library in libraries:
            runs = library.pop("runs")
            for run in runs:
                fastqs = run.pop("fastqs")
                for fastq in fastqs:
                    create_file(
                        fastq,
                        request_id,
                        settings.IMPORT_FILE_GROUP,
                        "fastq",
                        igocomplete,
                        sample_data,
                        library,
                        run,
                        request_metadata,
                        R1_or_R2(fastq),
                    )

    pooled_normal = data.get("pooledNormals", [])
    for pn in pooled_normal:
        try:
            create_pooled_normal(pn, str(settings.POOLED_NORMAL_FILE_GROUP))
        except Exception as e:
            print(e)


def format_request(req):
    if "_" in req:
        f, s = req.split("_")
        pre = ""
        if len(f) < 5:
            pre = "0" * (5 - len(f))
        return f"{pre}{f}_{s}"
    else:
        pre = ""
        if len(req) < 5:
            pre = "0" * (5 - len(req))
        return f"{pre}{req}"


def check_is_cmo(directory, missing):
    expected_files = []
    for request in missing:
        req = format_request(request)
        data = get_request_samples(req)
        if data.get("isCmoRequest", False):
            filename = f"request_{req}.json"
            print(filename)
            if not os.path.exists(os.path.join(directory, filename)):
                print(f"Missing {filename}")
                expected_files.append(os.path.join(directory, filename))
    return expected_files
