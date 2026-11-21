import logging
from celery import shared_task
from slugify import slugify
from voyager_sdk.configuration import OperatorConfiguration
from voyager_sdk.operator.operator_runner import OperatorRunner
from voyager_sdk.protocols.github_cache import GithubCache
from operator_manager.models import Operator, OperatorStatus

logger = logging.getLogger(__name__)


def image_tag(name, version):
    return "{}:{}".format(slugify(name), slugify(version))


def fetch_operator_repository(github_url, version):
    """Return the local checkout of github_url@version, cloning it through the voyager-sdk cache if needed."""
    return GithubCache.get(github_url, version) or GithubCache.add(github_url, version)


@shared_task
def build_operator_image(operator_id):
    operator = Operator.objects.get(id=operator_id)
    operator.status = OperatorStatus.INSTALLING
    operator.save(update_fields=["status"])
    version = operator.version or "main"
    try:
        repo_path = fetch_operator_repository(operator.github_url, version)
        runner = OperatorRunner(repo_path, configuration_path=OperatorConfiguration.config_path(repo_path))
        image_id, tag = runner.build(tag=image_tag(operator.name, version))
    except Exception:
        logger.exception("Failed to build image for operator %s", operator_id)
        operator.status = OperatorStatus.FAILED
        operator.save(update_fields=["status"])
        return
    logger.info("Built image %s (%s) from %s@%s", tag, image_id, operator.github_url, version)
    operator.ready(tag, image_id)
