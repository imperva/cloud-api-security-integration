#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##################################################
## Author: Doron Lehmann
## Email: Doron.Lehmann@imperva.com
##################################################
#

import json
import os

import yaml


class FileSystemFetcher:

    @staticmethod
    def fetch(settings, logger):
        path = settings["filesystem_path"]
        logger.debug("Trying to fetch API specs from a local path '%s'", path)
        if path is None or not path:
            logger.error("Can't fetch APIs from local path since the path is missing or empty")
            return None
        if not os.path.exists(path):
            logger.error("Can't read APIs from local path since the path '%s' does not exists", path)
            return None
        else:
            fetched_apis = dict()
            for file_name in os.listdir(path):
                file_path = os.path.join(path, file_name)
                valid_json = False
                valid_yaml = False
                logger.debug("Found the '%s' file - trying to open and parse it", file_path)
                with open(file_path) as api_spec_file:
                    file_content = api_spec_file.read()
                    # since swagger can be either JSON or YAML, we need to support both use cases
                    try:
                        api_spec = json.loads(file_content)
                        valid_json = True
                    except Exception as ex:
                        logger.debug("couldn't parse '%s' as JSON", file_path)
                    if not valid_json:
                        try:
                            api_spec = yaml.safe_load(file_content)
                            valid_yaml = True
                        except Exception as ex:
                            logger.debug("couldn't parse '%s' as YAML", file_path)
                    if not valid_json and not valid_yaml:
                        logger.error("Failed to parse %s as JSON and as YAML", file_path)
                    else:
                        logger.debug("Successfully opened and parsed the '%s' file", file_path)
                        fetched_apis[api_spec["host"] + api_spec["basePath"]] = api_spec
            logger.info("Fetched %d APIs from the filesystem", len(fetched_apis))
            return fetched_apis
