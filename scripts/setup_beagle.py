from beagle_etl.models import SMILEMessage, SmileMessageStatus, Operator
from file_system.models import FileGroup, Storage, StorageType, File, FileType, FileMetadata
from runner.models import Pipeline, TriggerRunType, TriggerAggregateConditionType, OperatorTrigger, PipelineName
from notifier.models import Notifier
import os
import requests
import json
from requests.auth import HTTPBasicAuth
import time
from operator import itemgetter
from django.utils.text import slugify
from django.conf import settings

SMILE_URL = os.environ["SMILE_URL"]
DMP2CMO_URL = os.environ["DMP2CMO_URL"]
DMP2CMO_TOKEN = os.environ["DMP2CMO_TOKEN"]
STORAGE_NAME = "iris"
STORAGE_TYPE = StorageType.LOCAL
OPERATOR_TRIGGER_RUN_TYPE = {"aggregate": TriggerRunType.AGGREGATE, "individual": TriggerRunType.INDIVIDUAL}
OPERATOR_TRIGGER_AGGREGATE_CONDITION = {
    "ninty_percent_succeeded": TriggerAggregateConditionType.NINTY_PERCENT_SUCCEEDED,
    "all_runs_succeeded": TriggerAggregateConditionType.ALL_RUNS_SUCCEEDED,
}
DMP_BAMS_FILE_GROUP = {"slug": "dmp-bams", "name": "DMP BAMs", "id": settings.DMP_BAM_FILE_GROUP}
POOLED_NORMAL_FILE_GROUP = {"slug": "pooled-normals", "name": "Pooled Normals", "id": settings.POOLED_NORMAL_FILE_GROUP}
IMPORT_FILE_GROUP = {"slug": "lims", "name": "LIMS", "id": settings.IMPORT_FILE_GROUP}

FILE_TYPES = [
    "rsa",
    "rds",
    "rpac",
    "rbwt",
    "maf",
    "csv",
    "idx",
    "sh",
    "unknown",
    "tbi",
    "sa",
    "pac",
    "fai",
    "dict",
    "bwt",
    "ann",
    "amb",
    "vcf",
    "txt",
    "tsv",
    "intervals",
    "interval_list",
    "ilist",
    "bedtools_genome",
    "bed",
    "bam",
    "fasta",
    "fastq",
]
DMP_MUTATION_EXTENDED_FILE_GROUP = {"slug": "dmp-data-mutations-extended", "name": "DMP Data Mutations Extended"}
FILES_ROUTE = "/v0/fs/files/"
BEAGLE_URL = os.environ["BEAGLE_URL"]
BEAGLE_USERNAME = os.environ["BEAGLE_USERNAME"]
BEAGLE_PASSWORD = os.environ["BEAGLE_PASSWORD"]
JIRA_BOARD = os.environ["JIRA_PROJECT"]
LOG_DIR = os.environ["LOG_DIR"]
basic_auth = HTTPBasicAuth(BEAGLE_USERNAME, BEAGLE_PASSWORD)


def set_requests(smile_requests_list):
    for single_request in smile_requests_list:
        if not SMILEMessage.objects.filter(request_id=single_request).exists():
            request_url = SMILE_URL + single_request
            smile_request = requests.get(request_url)
            if smile_request.ok:
                request_data = smile_request.json()
                request_data_str = json.dumps(request_data)
                new_smile_message = SMILEMessage(
                    topic=settings.METADB_NATS_NEW_REQUEST, message=request_data_str, request_id=single_request
                )
                new_smile_message.save()
            else:
                raise Exception("Could not load SMILE request " + str(single_request))
        all_loaded = False
        count = 0
        while not all_loaded:
            smile_requests = SMILEMessage.objects.filter(request_id__in=smile_requests_list)
            request_statuses = smile_requests.values_list("status", flat=True).distinct()
            if len(request_statuses) == 1 and request_statuses[0] == SmileMessageStatus.COMPLETED:
                all_loaded = True
            else:
                if count < 20:
                    print("Waiting for SMILE requests to load, sleeping for 1 minute")
                    time.sleep(60)
                    count += 1
                else:
                    raise Exception("Not all SMILE requests loaded within 10 minutes")


def set_pipelines(notifier, operators, pipelines):
    current_index = 0
    storage, _ = Storage.objects.get_or_create(name=STORAGE_NAME, type=STORAGE_TYPE)
    while current_index < len(pipelines) and current_index < len(operators):
        operator_dict = operators[current_index]
        pipeline_dict = pipelines[current_index]
        class_name, version, slug = itemgetter("class_name", "version", "slug")(operator_dict)
        file_group, name, entrypoint, output_directory, github, pipeline_version = itemgetter(
            "file_group", "name", "entrypoint", "output_directory", "github", "version"
        )(pipeline_dict)
        output_file_group, _ = FileGroup.objects.get_or_create(
            name=file_group, slug=slugify(file_group), storage=storage
        )
        operator, _ = Operator.objects.get_or_create(
            slug=slug, class_name=class_name, version=version, active=True, recipes=[""], notifier=notifier
        )
        pipeline, _ = Pipeline.objects.get_or_create(
            name=name,
            github=github,
            version=pipeline_version,
            entrypoint=entrypoint,
            output_file_group=output_file_group,
            output_directory=output_directory,
            log_directory=LOG_DIR,
            operator=operator,
            default=True,
        )
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        output_permission = pipeline_dict.get("output_permission", None)
        memlimit = pipeline_dict.get("memlimit", None)
        walltime = pipeline_dict.get("walltime", None)
        pipeline_name_str = pipeline_dict.get("pipeline_name", None)
        if pipeline_name_str:
            pipeline_name, _ = PipelineName.objects.get_or_create(name=pipeline_name_str)
            pipeline.pipeline_name = pipeline_name
        if output_permission:
            pipeline.output_permission = int(output_permission)
        if memlimit:
            pipeline.memlimit = memlimit
        if walltime:
            pipeline.walltime = int(walltime)
        pipeline.save()
        current_index += 1


def set_operator_triggers(operator_triggers):
    for single_operator_trigger in operator_triggers:
        (
            from_operator_slug,
            from_operator_version,
            to_operator_slug,
            to_operator_version,
            run_type,
            aggregate_condition,
        ) = itemgetter(
            "from_operator_slug",
            "from_operator_version",
            "to_operator_slug",
            "to_operator_version",
            "run_type",
            "aggregate_condition",
        )(
            single_operator_trigger
        )
        from_operator = Operator.objects.get(slug=from_operator_slug, version=from_operator_version)
        to_operator = Operator.objects.get(slug=to_operator_slug, version=to_operator_version)
        if run_type not in OPERATOR_TRIGGER_RUN_TYPE:
            raise Exception(
                str(run_type)
                + " not a valid key for run type please use either "
                + ", ".join(OPERATOR_TRIGGER_RUN_TYPE.keys())
            )
        if aggregate_condition not in OPERATOR_TRIGGER_AGGREGATE_CONDITION:
            raise Exception(
                str(run_type)
                + " not a valid key for aggregate condition please use either "
                + ", ".join(OPERATOR_TRIGGER_AGGREGATE_CONDITION.keys())
            )
        OperatorTrigger.objects.get_or_create(
            from_operator=from_operator,
            to_operator=to_operator,
            aggregate_condition=OPERATOR_TRIGGER_AGGREGATE_CONDITION[aggregate_condition],
            run_type=OPERATOR_TRIGGER_RUN_TYPE[run_type],
        )


def set_resource_files(resource_files):
    storage, _ = Storage.objects.get_or_create(name=STORAGE_NAME, type=STORAGE_TYPE)
    file_paths = list(File.objects.values_list("path", flat=True))
    for single_file_path in resource_files:
        new_file_list = []
        new_metadata_list = []
        updated_file_list = []
        updated_metadata_list = []
        with open(single_file_path, "r") as response_file:
            response_data = json.load(response_file)
            for single_file in response_data["results"]:
                file_name = single_file["file_name"]
                path = single_file["path"]
                file_group, _ = FileGroup.objects.get_or_create(
                    name=single_file["file_group"]["name"], slug=single_file["file_group"]["slug"], storage=storage
                )
                file_type, _ = FileType.objects.get_or_create(name=single_file["file_type"])
                new_metadata_obj = None
                new_file_obj = File(
                    file_name=file_name,
                    file_type=file_type,
                    path=path,
                    size=single_file["size"],
                    file_group=file_group,
                )
                if single_file["metadata"]:
                    new_metadata_obj = FileMetadata(
                        file=new_file_obj, metadata=single_file["metadata"], version=0, latest=True
                    )
                if path in file_paths:
                    updated_file_list.append(new_file_obj)
                    if new_metadata_obj:
                        updated_metadata_list.append(new_metadata_obj)
                else:
                    new_file_list.append(new_file_obj)
                    if new_metadata_obj:
                        new_metadata_list.append(new_metadata_obj)
                    file_paths.append(path)
            File.objects.bulk_create(new_file_list, ignore_conflicts=True)
            FileMetadata.objects.bulk_create(new_metadata_list, ignore_conflicts=True)
            if updated_file_list:
                File.objects.bulk_update(updated_file_list, ["file_name", "file_type", "path", "size", "file_group"])
            if updated_metadata_list:
                FileMetadata.objects.bulk_update(updated_metadata_list, ["file", "metadata"])


def set_dmp2cmo_files(patient_ids):
    headers = {"Authorization": "Token " + str(DMP2CMO_TOKEN)}
    file_url = BEAGLE_URL + FILES_ROUTE
    storage, _ = Storage.objects.get_or_create(name=STORAGE_NAME, type=STORAGE_TYPE)
    dmp_bam_file_group, _ = FileGroup.objects.get_or_create(
        name=DMP_BAMS_FILE_GROUP["name"], slug=DMP_BAMS_FILE_GROUP["slug"]
    )
    dmp_data_mutations_file_group, _ = FileGroup.objects.get_or_create(
        name=DMP_MUTATION_EXTENDED_FILE_GROUP["name"], slug=DMP_MUTATION_EXTENDED_FILE_GROUP["slug"]
    )
    for single_patient in patient_ids:
        dmp2cmo_data = requests.get(DMP2CMO_URL + single_patient, headers=headers, verify=False)
        if dmp2cmo_data.ok:
            results = dmp2cmo_data.json()["results"]
            for single_file in results:
                path = single_file["path"]
                file_group = None
                _, file_ext = os.path.splitext(path)
                file_type = file_ext.replace(".", "")
                metadata = single_file["sample"]
                if file_type == "bam":
                    file_group = str(dmp_bam_file_group.id)
                if file_type == "txt":
                    file_group = str(dmp_data_mutations_file_group.id)
                file_payload = {"path": path, "metadata": metadata, "file_group": file_group, "file_type": file_type}
                response = requests.post(file_url, json=file_payload, auth=basic_auth)


def create_file_groups(file_groups):
    storage, _ = Storage.objects.get_or_create(name=STORAGE_NAME, type=STORAGE_TYPE)
    file_groups_to_create = [DMP_BAMS_FILE_GROUP, POOLED_NORMAL_FILE_GROUP, IMPORT_FILE_GROUP] + file_groups
    for single_file_group in file_groups_to_create:
        if "id" in single_file_group and single_file_group["id"]:
            FileGroup.objects.get_or_create(
                name=single_file_group["name"],
                slug=single_file_group["slug"],
                id=single_file_group["id"],
                storage=storage,
            )
        else:
            FileGroup.objects.get_or_create(
                name=single_file_group["name"], slug=single_file_group["slug"], storage=storage
            )


def create_file_types():
    for single_file_type in FILE_TYPES:
        file_type, _ = FileType.objects.get_or_create(name=single_file_type)


def create_notifier():
    notifier, _ = Notifier.objects.get_or_create(default=True, notifier_type="JIRA", board=JIRA_BOARD)
    return notifier


def run(*args):
    config_data = {}
    with open(args[0], "r") as config_file:
        config_data = json.load(config_file)
    create_file_groups(config_data["file_groups"])
    create_file_types()
    notifier = create_notifier()
    set_requests(config_data["requests"])
    set_pipelines(notifier, config_data["operators"], config_data["pipelines"])
    set_operator_triggers(config_data["operarator_triggers"])
    set_resource_files(config_data["resource_files"])
    set_dmp2cmo_files(config_data["dmp2cmo_patients"])
