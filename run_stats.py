from file_system.models import File, FileExtension, FileGroup, FileGroupMetadata, FileMetadata, FileRunMap, FileType, Storage
from beagle_etl.models import Assay, Job, Operator
from django.db.models import Q
from runner.models import RunStatus
from file_system.repository.file_repository import FileRepository
from datetime import datetime, date, timedelta

def build_files_recipe_query(recipes):
    q = Q()
    for recipe in recipes:
        q |= Q(metadata__recipe=recipe)
    return q

def build_runs_recipe_query(recipes):
    q = Q()
    for recipe in recipes:
        q |= Q(args__request_metadata__recipe=recipe)
    return q


def get_sample_counts(files, recipes):
    results = dict()
    for recipe in recipes:
        results[recipe] = len(set(files.filter(Q(metadata__recipe=recipe)).values_list('metadata__sampleId')))
    return results

LIMS_FILE_GROUP='b54d035d-f63c-4ea8-86fb-9dbc976bb7fe'
DMP_BAMS_FILE_GROUP='d4775633-f53f-412f-afa5-46e9a86b654b'
POOLED_NORMALS_FILE_GROUP='083a6e12-9b9f-4461-bde3-fdab6752b54b'

print("Calculating number of files per file group of interest...")
files = FileRepository.all()
lims_files = files.filter(Q(file__file_group=LIMS_FILE_GROUP))
pooled_normals=files.filter(Q(file__file_group=POOLED_NORMALS_FILE_GROUP))
dmp_bams_files = files.filter(Q(file__file_group=DMP_BAMS_FILE_GROUP))

num_dmp_bams = len(set(dmp_bams_files))
num_pooled_normals = len(set(pooled_normals.values_list('metadata__runId', 'metadata__recipe', 'metadata__preservation')))

num_requests = len(set(lims_files.values_list('metadata__requestId')))
num_samples = len(set(lims_files.values_list('metadata__sampleId')))

### ARGOS stuff
print("Getting ARGOS-specific info...")
argos_recipes = [ 'IMPACT341', 'IMPACT+ (341 genes plus custom content)', 'IMPACT410', 'IMPACT468', 'HemePACT_v4' ]
argos_recipe_query = build_files_recipe_query(argos_recipes)
argos_files = lims_files.filter(argos_recipe_query)
num_argos_requests = len(set(argos_files.values_list('metadata__requestId')))
num_argos_samples = get_sample_counts(argos_files, argos_recipes)

# Get Runs info

argos_run_recipe_query = build_runs_recipe_query(argos_recipes)
argos_imports = Job.objects.filter(argos_run_recipe_query, run='beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata', created_date__gt=datetime(2020,6,5))
num_imports = len(set(argos_imports))

#start_delta = timedelta(days=date.today().weekday(), weeks=1)
argos_runs = Run.objects.filter(app__name='argos', created_date__gt=datetime(2020,6,5))#date.today() - start_delta)
argos_status = dict()

for i in RunStatus:
    argos_status[str(i).replace("RunStatus.", "")] = len(set(argos_runs.filter(status=i)))

print("Overview")
print("Number of requests: %i" % num_requests)
print("Number of samples: %i" % num_samples)
print("Number of pooled normals: %i" % num_pooled_normals)
print("Number of DMP Bams: %i" % num_dmp_bams)
print()
print("Total number of ARGOS samples")
for key in num_argos_samples:
    print(key, '\t', num_argos_samples[key])
print()
print("Changes since 2020-Jun-5")
print("Number of samples imported: %i" % num_imports)
print()
print("Current ARGOS Run Status (in T/N pairs)")
for key in argos_status:
    print(key, "\t", argos_status[key])
