import json
import os
import git
import uuid
import shutil
import logging
from django.conf import settings
from file_system.repository import FileRepository
from runner.cache.github_cache import GithubCache
from runner.run.processors.file_processor import FileProcessor


class PipelineResolver(object):
    logger = logging.getLogger(__name__)

    def __init__(self, github, entrypoint, version=None):
        self.github = github
        self.entrypoint = entrypoint
        self.version = version

    def _git_clone(self, location):
        dirname = os.path.join(location, self._extract_dirname_from_github_link())
        cached = GithubCache.get(self.github, self.version)
        if cached:
            self.logger.info("App found in cache %s" % cached)
            os.symlink(cached, dirname)
        else:
            git.Git(location).clone(self.github, "--branch", self.version, "--recurse-submodules")
        return dirname

    def _dir_name(self):
        dirname = "/tmp/" + str(uuid.uuid4())
        os.mkdir(dirname)
        return dirname

    def _extract_dirname_from_github_link(self):
        dirname = self.github.rsplit("/", 2)[1] if self.github.endswith("/") else self.github.rsplit("/", 1)[1]
        if dirname.endswith(".git"):
            dirname = dirname[:-4]
        return dirname

    def _cleanup(self, location):
        if os.path.islink(location):
            os.unlink(location)
        else:
            shutil.rmtree(location)

    def import_reference_files(self):
        dir_name = self._dir_name()
        pipeline_path = self._git_clone(dir_name)
        absolute_path = os.path.join(pipeline_path, settings.APP_REFERENCE_FILES_PATH)
        logging.info(f"Locating reference file in {absolute_path}")
        if os.path.exists(absolute_path):
            with open(absolute_path, "r") as f:
                files = json.load(f)
                for f in files:
                    if not FileRepository.filter(
                        path=f["location"], file_group=settings.REFERENCE_FILE_GROUP_ID
                    ).first():
                        logging.info(f"Registering {f}")
                        FileProcessor.create_file_obj(
                            f["location"],
                            f["size"],
                            f["checksum"],
                            settings.REFERENCE_FILE_GROUP_ID,
                        )
        else:
            logging.info(f"Pipeline doesn't have reference file in {absolute_path}")
        logging.info(f"Cleanup pipeline directory {dir_name}")
        self._cleanup(dir_name)

    def load(self):
        pass

    def resolve(self):
        pass
