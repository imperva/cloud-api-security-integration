#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##################################################
## Author: Doron Lehmann
## Email: Doron.Lehmann@imperva.com
##################################################
#

import json

import requests


class ThreeScaleFetcher:

    @staticmethod
    def fetch(settings, logger):
        url = settings["three_scale_url"]
        access_token = settings["three_scale_access_token"]
        logger.debug("Trying to fetch API specs from 3Scale")
        if url is None or not url:
            logger.error("Can't fetch APIs from 3Scale since we are missing the URL")
            return None
        if access_token is None or not access_token:
            logger.error("Can't fetch APIs from 3Scale since we are missing the Access Token")
            return None
        params = { 'access_token': access_token }
        try:
            response = requests.get("https://%s/admin/api/active_docs.json" % url, params, timeout=10)
            if response.status_code != 200:
                logger.error("Failed to fetch API specs from 3Scale. Response code is %d, %s\nInfo is %s", response.status_code, response.reason, response.text )
                return None
            else:
                fetched_apis = dict()
                apis = response.json()["api_docs"]
                logger.info("Successfully fetched %d API specs from 3Scale", len(apis))
                for api in apis:
                    api_spec = json.loads(api["api_doc"]["body"].replace("\r","").replace("\n","").strip())
                    fetched_apis[api_spec["host"] + api_spec["basePath"]] = api_spec
                logger.info("Fetched %d APIs from the 3Scale", len(fetched_apis))
                return fetched_apis
        except requests.exceptions.RequestException as re:
            logger.error("Error while trying to fetch API specs from 3Scale - error is %s", re)
            return None