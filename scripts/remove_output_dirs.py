import logging
from django.conf import settings
from runner.models import Run, RunStatus, Port
from datetime import date
import shutil
import os
import tempfile
import logging
logger = logging.getLogger(__name__)

def clean_directory(path, exclude=[]):
    with tempfile.TemporaryDirectory() as tmpdirname:
        for f in exclude:
            src = os.path.join(path, f)
            if os.path.exists(src):
                shutil.copy(src, tmpdirname)
        try:
            shutil.rmtree(path)
        except Exception as e:
            logger.error("Failed to remove folder: %s\n%s" % (path, str(e)))
            return False
        """
        Return excluded files to previous location
        """
        if exclude:
            os.makedirs(path, exist_ok=True)
            for f in exclude:
                src = os.path.join(tmpdirname, f)
                if os.path.exists(src):
                    shutil.copy(src, path)
        return True

def cleanup_output_dirs(request_ids, target_date, custom_run_query=None):
    # apps = ["access v2 nucleo", "access v2 nucleo qc", "access v2 nucleo qc agg",
    #                     "access v2 legacy SNV", "access v2 legacy CNV", "access v2 legacy SV",
    #                     "access v2 legacy MSI"]
    if request_ids:
        jobs = Run.objects.filter(
            tags__igoRequestId__in=request_ids,
            app__name__in=["access v2 nucleo qc agg"],
            status=RunStatus.COMPLETED,
            created_date__lt=target_date
        )#.values_list('operator_run', flat=True).distinct()
    elif custom_run_query:
        jobs = Run.objects.filter(custom_run_query)
    for job in jobs:
        clean_directory("/juno" + job.output_directory, exclude=[])
cleanup_output_dirs(["16772_B","13715_Q","14927_I","14636_G","13893_T"], date(2025, 4, 1))







