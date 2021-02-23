import os
import logging
from shutil import copyfile
from django.conf import settings


logger = logging.getLogger(__name__)


class CopyService(object):

    @staticmethod
    def copy(path_from, path_to):
        logger.info('Copy path from {path_from} to {path_to}'.format(path_from=path_from,
                                                                     path_to=path_to))
        dirname = os.path.dirname(path_to)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        copyfile(path_from, path_to)

    @staticmethod
    def remap(recipe, path, mapping=settings.DEFAULT_MAPPING):
        recipe_mapping = mapping.get(recipe, {})
        for prefix, dst in recipe_mapping.items():
            if path.startswith(prefix):
                path = path.replace(prefix, dst)
                break
        logger.info('New path {path}'.format(path=path))
        return path
