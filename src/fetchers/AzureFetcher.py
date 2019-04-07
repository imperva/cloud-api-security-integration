#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##################################################
## Author: Doron Lehmann
## Email: Doron.Lehmann@imperva.com
##################################################
#

import codecs
import json

import requests


class AzureFetcher:

    @staticmethod
    def fetch(settings, logger):
        subscription_id=settings["subscription_id"]
        resource_group_name=settings["resource_group_name"]
        service_name=settings["service_name"]
        access_token=settings["access_token"]
        logger.debug("Trying to fetch API specs from Azure")
        if subscription_id is None or not subscription_id:
            logger.error("Can't fetch APIs from Azure since we are missing the subscription ID")
            return None
        if resource_group_name is None or not resource_group_name:
            logger.error("Can't fetch APIs from Azure since we are missing the resource group name")
            return None
        if service_name is None or not service_name:
            logger.error("Can't fetch APIs from Azure since we are missing the service name")
            return None
        if access_token is None or not access_token:
            logger.error("Can't fetch APIs from Azure since we are missing the access token")
            return None
        try:
            azure_base_url = "https://%s.management.azure-api.net/subscriptions/%s/resourceGroups/%s/providers/Microsoft.ApiManagement/service/%s/apis?api-version=2018-06-01-preview" % (service_name, subscription_id, resource_group_name, service_name)
            all_apis_response = requests.get(azure_base_url, headers={'Authorization': access_token}, timeout=10)
            if all_apis_response.status_code != 200:
                logger.error("Failed to fetch API specs from Azure. Response code is %d, %s\nInfo is %s", all_apis_response.status_code, all_apis_response.reason, all_apis_response.text )
                return None
            else:
                fetched_apis = dict()
                apis = all_apis_response.json()["value"]
                logger.debug("Found %d APIs in Azure, fetching their details", len(apis))
                for api in apis:
                    logger.debug("Trying to fetch API %s from Azure", api["id"])
                    api_url = "https://%s.management.azure-api.net/subscriptions/%s/resourceGroups/%s/providers/Microsoft.ApiManagement/service/%s/apis/%s?format=swagger-link&export=true&api-version=2018-06-01-preview" % (service_name, subscription_id, resource_group_name, service_name, api["name"])
                    api_response = requests.get(api_url, headers={'Authorization': access_token}, timeout=10)
                    if api_response.status_code != 200:
                        logger.error("Failed to fetch API %s from Azure. Response code is %d, %s\nInfo is %s" ,api["id"], api_response.status_code, api_response.reason, api_response.text)
                    else:
                        api_link = json.loads(codecs.decode(api_response.content, 'utf-8-sig'))["link"]
                        logger.debug("Fetching swagger for API %s from Azure - the URL is %s", api["id"], api_link)
                        swagger_response = requests.get(api_link, timeout=10)
                        if swagger_response.status_code != 200:
                            logger.error("Failed to fetch API %s from Azure. Response code is %d, %s\nInfo is %s", api_link, swagger_response.status_code, swagger_response.reason, swagger_response.text)
                        else:
                            api_spec = swagger_response.json()
                            fetched_apis[api_spec["host"] + api_spec["basePath"]] = api_spec
                            logger.debug("Successfully fetched the API spec for %s from Azure", api["id"])
                logger.info("Successfully fetched %d API specs from Azure", len(fetched_apis))
                return fetched_apis
        except requests.exceptions.RequestException as re:
            logger.error("Error while trying to fetch API specs from Azure - error is %s", re)
            return None
