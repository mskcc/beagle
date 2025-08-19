import os
import venv
import subprocess
from celery import shared_task
from django.conf import settings


@shared_task()
def install_operator(operator_id, operator_github, operator_version):
    github_package_url = f"{operator_github}@{operator_version}"
    python_exec = create_virtualenv(operator_id)
    install_operator_code(python_exec, github_package_url)


def create_virtualenv(operator_id):
    venv_location = os.path.join(settings.SDK_VENV_LOCATION, operator_id)
    venv.create(venv_location, with_pip=True)
    return os.path.join(venv_location, "bin", "python")


def install_operator_code(python_exec, github_package_url):
    subprocess.run([python_exec, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([python_exec, '-m', 'pip', 'install', github_package_url], check=True)


def connect_pipeline_and_operator(operator_id, pipeline_id):
    pass