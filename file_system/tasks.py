import logging
from celery import task


logger = logging.getLogger(__name__)


@task
def fetch_requests_lims():
    logger.info("Fetching requestIDs")
    pass
