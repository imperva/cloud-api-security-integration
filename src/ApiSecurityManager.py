#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##################################################
## Author: Doron Lehmann
## Email: Doron.Lehmann@imperva.com
##################################################
#

import getopt
import importlib
import json
import logging
import os
import sys
from logging import handlers

import requests

from config.Config import Config
from utils.Status import Status


class ApiSecurityManager:

    def __init__(self, path_to_conf_file, conf_json):
        self.config = None
        self.logger = None
        self.config = self.set_config(path_to_conf_file, conf_json)
        self.logger = self.set_log(self.config.LOG_PATH, self.config.LOG_LEVEL)
        self.existing_apis = dict()
        self.status = Status(self.logger)


    def protect_apis_with_imperva(self):
        self.logger.info("Starting to run the API Security Manager")
        # Check for existing APIs at Imperva
        successfully_read_existing_apis = self.read_apis()
        if not successfully_read_existing_apis:
            # If we fail to read the existing APIs we exit since we can't know which API should be added/updated/deleted
            self.logger.error("Exiting since we failed to read the existing APIs for site ID %s", self.config.SITE_ID)
            sys.exit(1)
        else:
            # Fetch the API specifications from the desired API management platform or filesystem
            fetched_api_specs = self.fetch_api_specs()
            if len(fetched_api_specs) > 0:
                # Upload newly found APIs and update existing APIs
                self.upload_and_update_apis(fetched_api_specs)
            # Check for APIs which are previously added to Imperva but were not fetched this time - therefore they should be deleted now since they no longer exists
            self.delete_apis(fetched_api_specs)
            run_status = self.status.calculate_status()
            self.status.report_status(self.config.STATUS_PATH)
            self.logger.info("Finished updating the API security manager - The status is %s", json.dumps(self.status.get_status()))
            self.logger.info("Successfully finished running the API Security Manager")
            return run_status


    def fetch_api_specs(self):
        self.logger.info("Trying to fetch API specs")
        api_specs = dict()
        for fetcher in self.config.FETCHERS:
            if fetcher["active"]:
                try:
                    Fetcher = getattr(importlib.import_module("fetchers." + fetcher["type"]), fetcher["type"])
                    fetched_apis = Fetcher.fetch(fetcher["settings"], self.logger)
                    if fetched_apis is not None:
                        api_specs.update(fetched_apis)
                except Exception as ex:
                    self.logger.error("Failed to fetch APIs from %s. Error is %s", fetcher["type"], ex)
                    self.status.update_fetcher_error(fetcher["type"])
                self.status.update_fetcher_success(fetcher["type"])
        if len(api_specs) == 0:
            self.logger.error("Failed to fetch API specs")
            sys.exit(1)
        return api_specs


    def read_apis(self):
        self.logger.info("Trying to read the existing APIs from Imperva for site ID %s", self.config.SITE_ID)
        try:
            self.logger.debug("Sending request to Imperva in order to read the current APIs")
            response = requests.get(self.config.MANAGEMENT_URL + ("?api_id=%s&api_key=%s" %(self.config.API_ID, self.config.API_KEY)), timeout=10)
            self.logger.debug("Got a response from Imperva\nResponse code is %d, %s\nInfo is '%s'", response.status_code, response.reason, response.text)
            if response.status_code != 200:
                self.logger.error("Failed to read the APIs for site ID %s\nResponse code is %d, %s\nInfo is '%s'", self.config.SITE_ID, response.status_code, response.reason, response.text)
                return False
            else:
                response_json = json.loads(response.text)
                for api_res in response_json["value"]:
                    self.logger.debug("Found an existing API - %s", api_res)
                    self.existing_apis[api_res["hostName"] + api_res["basePath"]] = api_res["id"]
                self.logger.info("Successfully read the existing APIs for site ID %s - Total existing APIs is %d ", self.config.SITE_ID, len(self.existing_apis))
                return True
        except requests.exceptions.RequestException as re:
            self.logger.error("Error while trying to read the APIs for site ID %s\nError is '%s'" , self.config.SITE_ID, re)
            return False


    def upload_and_update_apis(self, fetched_api_specs):
        self.logger.info("Trying to upload and update the fetched APIs")
        for host_and_base_path, api_spec in fetched_api_specs.items():
            # check if the API spec is already uploaded and if so - update it
            if host_and_base_path in self.existing_apis:
                self.logger.info("API for '%s' exists in the system - Updating it with the latest fetched version", host_and_base_path)
                self.update_api(host_and_base_path, api_spec, self.existing_apis[host_and_base_path])
            else:
                # in case that the API is not yet protected - upload it
                self.logger.info("API for '%s' does not exists in the system - uploading it for the first time", host_and_base_path)
                self.upload_api(host_and_base_path, api_spec)
        self.logger.info("Finished to upload and update the fetched APIs")


    def delete_apis(self, fetched_api_specs):
        apis_to_delete = {k: self.existing_apis[k] for k in set(self.existing_apis) - set(fetched_api_specs)}
        self.logger.info("Found %d APIs which needs to be deleted", len(apis_to_delete))
        for host_and_base_path, api_id in apis_to_delete.items():
            self.logger.info("API ID %d for '%s' was not fetched from the repository and therefore will be deleted from Imperva", api_id, host_and_base_path)
            self.delete_api(host_and_base_path, api_id)


    def update_api(self, host_and_base_path, api_spec, api_spec_id):
        self.logger.debug("Trying to update the API spec %s for '%s'", api_spec_id, host_and_base_path)
        try:
            response = requests.post(self.config.MANAGEMENT_URL + self.config.SITE_ID + "/" + str(api_spec_id) + ("?api_id=%s&api_key=%s" %(self.config.API_ID, self.config.API_KEY)), files=dict(fileContent=json.dumps(api_spec), validateHost=False, specificationViolationAction=self.config.DEFAULT_ACTION), timeout=10)
            if response.status_code != 200:
                self.logger.error("Failed to update the API spec %s for '%s'.\nResponse code is %d, %s\nInfo is '%s'",api_spec_id, host_and_base_path, response.status_code, response.reason, response.text)
                self.status.update_api_error("updated", host_and_base_path)
            else:
                self.logger.debug("Successfully updated the API spec %s for '%s'", api_spec_id, host_and_base_path)
                self.status.update_api_success("updated", host_and_base_path)
        except requests.exceptions.RequestException as re:
            self.logger.error("Error while trying to update the API spec %s for '%s', error is '%s'", api_spec_id, host_and_base_path, re)
            self.status.update_api_error("updated", host_and_base_path)


    def upload_api(self, host_and_base_path, api_spec):
        self.logger.debug("Trying to upload the API spec '%s'", host_and_base_path)
        try:
            response = requests.post(self.config.MANAGEMENT_URL + self.config.SITE_ID + ("?api_id=%s&api_key=%s" %(self.config.API_ID, self.config.API_KEY)), files=dict(fileContent=json.dumps(api_spec), validateHost=False, specificationViolationAction=self.config.DEFAULT_ACTION), timeout=10)
            if response.status_code != 200:
                self.logger.error("Failed to upload the API spec '%s'.\nResponse code is %d, %s\nInfo is '%s'", host_and_base_path, response.status_code, response.reason, response.text)
                self.status.update_api_error("added", host_and_base_path)
            else:
                self.logger.debug("Successfully uploaded the API spec for '%s'", host_and_base_path)
                self.status.update_api_success("added", host_and_base_path)
        except requests.exceptions.RequestException as re:
            self.logger.error("Error while trying to upload the API spec for '%s', error is '%s'" , host_and_base_path, re)
            self.status.update_api_error("added", host_and_base_path)


    def delete_api(self, host_and_base_path, api_spec_id):
        self.logger.debug("Trying to delete the API spec %s for '%s'", api_spec_id, host_and_base_path)
        try:
            response = requests.delete(self.config.MANAGEMENT_URL + self.config.SITE_ID + "/" +str(api_spec_id) + ("?api_id=%s&api_key=%s" %(self.config.API_ID, self.config.API_KEY)), timeout=10)
            if response.status_code != 200:
                self.logger.error("Failed to delete the API spec %s for '%s'.\nResponse code is %d, %s\nInfo is '%s'", api_spec_id, host_and_base_path, response.status_code, response.reason, response.text)
                self.status.update_api_error("deleted", host_and_base_path)
            else:
                self.logger.info("Successfully delete the API spec %s for '%s'", api_spec_id, host_and_base_path)
                self.status.update_api_success("deleted", host_and_base_path)
        except requests.exceptions.RequestException as re:
            self.logger.error("Error while trying to delete the API spec %s for '%s', error is '%s'" , api_spec_id, host_and_base_path, re)
            self.status.update_api_error("deleted", host_and_base_path)


    def set_config(self, path_to_conf_file, conf_json):
        try:
            return Config(path_to_conf_file, conf_json).read()
        except Exception:
            sys.exit(1)


    def set_log(self, system_log_path, log_level):
        # set a log file for the API security manager
        logger = logging.getLogger("apiSecurityManager")
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        if system_log_path is not None and system_log_path:
            # default log directory for the API security manager
            log_dir = system_log_path
            # create the log directory if needed
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            # keep logs history for 7 days
            file_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(log_dir, "api_security_manager.log"), when='midnight', backupCount=7)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        if log_level == "DEBUG":
            logger.setLevel(logging.DEBUG)
        elif log_level == "INFO":
            logger.setLevel(logging.INFO)
        elif log_level == "ERROR":
            logger.setLevel(logging.ERROR)
        return logger


if __name__ == "__main__":
    # Default config path
    path_to_config_file = "/etc/imperva/cloud-api-security/config/config.json"
    config_json = None
    try:
        # Read arguments
        opts, args = getopt.getopt(sys.argv[1:], 'p:c:h', ['path=', 'config=', 'help'])
    except getopt.GetoptError:
        print("\nError starting API Security Manager. The following arguments should be provided:\n"
                "'-p' -> path to the configuration JSON file or '-c' -> the configuration JSON itself\n"
                "Or no arguments at all in order to use default paths\n"
                "Run with -h to get more assistance")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print ("\nTo run please the following:\n\n"
                   "ApiSecurityManager.py -p <path_to_config_file> \n\n"
                   "OR\n\n"
                   "ApiSecurityManager.py -c '{'the configuration json'}' with the following structure:\n\n")
            with open('config/config.json', 'r') as handle:
                parsed = json.load(handle)
                print(json.dumps(parsed, indent=4, sort_keys=True))
            sys.exit(2)
        elif opt in ('-p', '--path'):
            path_to_config_file = arg
        elif opt in ('-c', '--config'):
            config_json = arg
    # Init the ApiSecurityManager
    apiSecurityManager = ApiSecurityManager(path_to_config_file, config_json)
    try:
        # Run the API security manager
        status = apiSecurityManager.protect_apis_with_imperva()
        sys.exit(status)
    except Exception as e:
        sys.exit("Error running the ApiSecurityManager - %s" % e)
