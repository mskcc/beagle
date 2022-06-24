import copy
from file_system.repository.file_repository import FileRepository


def remap_metadata(metadata):
    new_metadata = copy.deepcopy(metadata)
    new_metadata["igoComplete"] = new_metadata.pop("igocomplete")
    return new_metadata


files = FileRepository.filter(file_group=("1a1b29cf-3bc2-4f6c-b376-d4c5d701166a")).all()

for f in files:
    try:
        if "igocomplete" in f.metadata::
            new_metadata = remap_metadata(f.metadata)
            f.metadata = new_metadata
            f.save()
    except Exception as e:
        print(e)
        print(f)
