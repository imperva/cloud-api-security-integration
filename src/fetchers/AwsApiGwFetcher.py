#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##################################################
## Author: Doron Lehmann
## Email: Doron.Lehmann@imperva.com
##################################################
#

import json

import boto3


class AwsApiGwFetcher:

    @staticmethod
    def fetch(settings, logger):
        access_key_id = settings["aws_access_key_id"]
        secret_access_key = settings["aws_secret_access_key"]
        region = settings["aws_region"]
        logger.debug("Trying to fetch API specs from AWS API GW")
        if access_key_id is None or not access_key_id:
            logger.error("Can't fetch APIs from AWS API GW since we are missing the aws_access_key_id")
            return None
        if secret_access_key is None or not secret_access_key:
            logger.error("Can't fetch APIs from AWS API GW since we are missing the aws_secret_access_key")
            return None
        if region is None or not region:
            logger.error("Can't fetch APIs from AWS API GW since we are missing the AWS region")
            return None
        try:
            aws_client = boto3.client('apigateway', aws_access_key_id = access_key_id, aws_secret_access_key = secret_access_key, region_name = region)
            apis = aws_client.get_rest_apis()
            fetched_apis = dict()
            for api in apis["items"]:
                stages = aws_client.get_stages(restApiId = api["id"])
                for stage in stages["item"]:
                    swagger = aws_client.get_export(restApiId=api["id"], stageName=stage["stageName"], exportType="swagger", parameters={'extensions': 'integrations'}, accepts="application/json")
                    api_spec = json.loads((swagger["body"].read()))
                    fetched_apis[api_spec["host"] + api_spec["basePath"]] = api_spec
                    logger.debug("Fetched swagger for API %s for stage %s", api["id"], stage["stageName"])
            logger.info("Successfully fetched %d API specs from AWS API GW", len(fetched_apis))
            return fetched_apis
        except Exception as ex:
            logger.error("Error while trying to fetch API specs from AWS API GW - error is %s", ex)
            return None
