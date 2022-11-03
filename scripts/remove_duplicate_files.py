from file_system.repository.file_repository import FileRepository
from django.conf import settings
import argparse
import itertools

#
# Example usage:
#
# python3 manage.py runscript remove_duplicate_files --script-args "-r [request_id]"
#
#


def remove_old_files(file_list):
    file_list.sort(key=lambda file: max(file.file.modified_date, file.file.created_date), reverse=True)
    for single_file in file_list[1::]:
        single_file.file.delete()
        single_file.delete()


def remove_files(request_id):
    req_fastq = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, file_type="fastq"
    ).order_by("file__file_name")
    if not req_fastq:
        print("No files matching this query for request: {}".format(request_id))
    else:
        file_groups = itertools.groupby(req_fastq, lambda fileObj: fileObj.file.file_name)
        for _, group in file_groups:
            group_list = list(group)
            if len(group_list) > 1:
                remove_old_files(group_list)


def run(*args):
    parser = argparse.ArgumentParser(description="Delete duplicate files")
    parser.add_argument("-r", "--request_id")
    arg_obj = parser.parse_args(args)
    remove_files(arg_obj.request_id.strip())
