import os
import pwd
import logging
from shutil import copyfile, chown
from django.conf import settings


logger = logging.getLogger(__name__)


class CopyService(object):
    @staticmethod
    def copy(path_from, path_to):
        logger.info(
            "Copy path from {path_from} to {path_to}".format(
                path_from=path_from, path_to=path_to
            )
        )

        dirname = os.path.dirname(path_to)
        splitted_path = dirname.split("/")
        subpaths = [
            "/".join(splitted_path[:i]) for i in range(2, len(splitted_path) + 1)
        ]
        subpaths_iter = iter(subpaths)
        newly_created = []
        for subpath in subpaths_iter:
            if not os.path.exists(subpath):
                newly_created = [subpath] + list(subpaths_iter)
                os.makedirs(dirname, mode=settings.COPY_DIR_PERMISSION)
                break

        copyfile(path_from, path_to)
        os.chmod(path_to, settings.COPY_FILE_PERMISSION)

        if settings.COPY_GROUP_OWNERSHIP:
            uid = os.getuid()
            gid = grp.getgrnam(settings.COPY_GROUP_OWNERSHIP).gr_gid
            for dirpath in newly_created:
                chown(dirpath, group=gid)
            os.chown(path_to, uid=uid, gid=gid)

    @staticmethod
    def remap(recipe, path, mapping=settings.DEFAULT_MAPPING):
        prefix, dst = CopyService.get_mapping(recipe, path, mapping)
        if prefix and dst:
            path = path.replace(prefix, dst)
        logger.info("New path {path}".format(path=path))
        return path

    @staticmethod
    def get_mapping(recipe, path, mapping=settings.DEFAULT_MAPPING):
        recipe_mapping = mapping.get(recipe, {})
        for prefix, dst in recipe_mapping.items():
            if path.startswith(prefix):
                return prefix, dst
        return None, None
