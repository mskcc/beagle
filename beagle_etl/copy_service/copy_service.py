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
            os.makedirs(dirname, mode=settings.COPY_DIR_PERMISSION)
        copyfile(path_from, path_to)
        os.chmod(path_to, settings.COPY_FILE_PERMISSION)

    @staticmethod
    def remap(recipe, path, mapping=settings.DEFAULT_MAPPING):
        prefix, dst = CopyService.get_mapping(recipe, path, mapping)
        if prefix and dst:
            path = path.replace(prefix, dst)
        logger.info('New path {path}'.format(path=path))
        return path

    @staticmethod
    def get_mapping(recipe, path, mapping=settings.DEFAULT_MAPPING):
        recipe_mapping = mapping.get(recipe, {})
        for prefix, dst in recipe_mapping.items():
            if path.startswith(prefix):
                return prefix, dst
        return None, None
