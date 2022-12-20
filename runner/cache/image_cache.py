import os
import logging
from django.conf import settings
from runner.cache.github_cache import GithubCache
import subprocess


class ImageCache(object):
    logger = logging.getLogger(__name__)

    @staticmethod
    def get(pipeline):
        full_path = ImageCache._generate_directory_name(pipeline)
        if os.path.exists(full_path):
            ImageCache.logger.info("Image cache found : %s" % full_path)
            return full_path
        ImageCache.logger.info("Image cache not found")
        return None

    @staticmethod
    def add(pipeline):
        expected_path = ImageCache._generate_directory_name(pipeline)
        ImageCache.logger.info("Expected path %s" % expected_path)
        if not os.path.exists(expected_path):
            pipeline_cache_path = GithubCache.get(pipeline.github, pipeline.version)
            cwl_path = os.path.join(pipeline_cache_path, pipeline.entrypoint)
            if not os.path.exists(cwl_path):
                ImageCache.logger.error("Pipeline cache not found: %s" % cwl_path)
            ImageCache.logger.info("Creating image cache %s" % expected_path)
            os.makedirs(expected_path)
            update_cache_cmd = settings.UPDATE_CACHE_CMD.split(" ")
            command = update_cache_cmd + ["-s", expected_path, "-c", cwl_path]
            subprocess.run(command)
            return expected_path
        return None

    @staticmethod
    def _generate_directory_name(pipeline):
        name = pipeline.name.replace(" ", "_")
        version = pipeline.version.replace(" ", "_")
        path = os.path.join(settings.IMAGE_CACHE, name, version)
        return path
