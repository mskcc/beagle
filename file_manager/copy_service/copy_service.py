import os
import logging
from shutil import copyfile
from django.conf import settings


logger = logging.getLogger(__name__)


class CopyService(object):
    @staticmethod
    def copy(path_from, path_to):
        logger.info("Copy path from {path_from} to {path_to}".format(path_from=path_from, path_to=path_to))

        dirname = os.path.dirname(path_to)
        splitted_path = dirname.split("/")
        subpaths = ["/".join(splitted_path[:i]) for i in range(2, len(splitted_path) + 1)]
        subpaths_iter = iter(subpaths)
        for subpath in subpaths_iter:
            if not os.path.exists(subpath):
                os.makedirs(dirname, mode=settings.COPY_DIR_PERMISSION)
                break

        copyfile(path_from, path_to)
        os.chmod(path_to, settings.COPY_FILE_PERMISSION)

    @staticmethod
    def remap(gene_panel, path, mapping=settings.DEFAULT_MAPPING):
        prefix, dst = CopyService._get_mapping(gene_panel, path, mapping)
        if prefix and dst:
            path = path.replace(prefix, dst)
        logger.info("New path {path}".format(path=path))
        return path

    @staticmethod
    def _get_mapping(gene_panel, path, mapping=settings.DEFAULT_MAPPING):
        recipe_mapping = mapping.get(gene_panel, {})
        for prefix, dst in recipe_mapping.items():
            if path.startswith(prefix):
                return prefix, dst
        return None, None

    @staticmethod
    def get_reverse_mapping(gene_panel, path, mapping=settings.DEFAULT_MAPPING):
        recipe_mapping = mapping.get(gene_panel, {})
        for prefix, dst in recipe_mapping.items():
            if path.startswith(dst):
                return dst, prefix
