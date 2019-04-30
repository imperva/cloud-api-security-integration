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

class Config:

    def __init__(self, config_file_path, config_json):
            self.config_json = config_json
            self.config_file_path = config_file_path

    def read(self):
        try:
            if self.config_json is None:
                self.config_json = self.read_conf_from_file()
            self.config_json = json.loads(self.config_json)
            config = Config(None, self.config_json)
            config.LOG_PATH = self.config_json["logging"]["log_path"]
            config.LOG_LEVEL = self.config_json["logging"]["level"]
            config.STATUS_PATH = self.config_json["logging"]["status_path"]
            config.API_ID = self.config_json["api_id"]
            if not config.API_ID:
                raise Exception("api_id should not be empty")
            config.API_KEY = self.config_json["api_key"]
            if not config.API_KEY:
                raise Exception("api_key should not be empty")
            config.SITE_ID = self.config_json["site_id"]
            if not config.SITE_ID:
                raise Exception("site_id should not be empty")
            config.MANAGEMENT_URL = self.config_json["management_url"]
            if not config.MANAGEMENT_URL:
                raise Exception("management_url should not be empty")
            config.DEFAULT_ACTION = self.config_json["default_action"]
            if not config.DEFAULT_ACTION:
                raise Exception("default_action should not be empty")
            supported_actions = {"ALERT_ONLY", "BLOCK_REQUEST", "BLOCK_USER", "BLOCK_IP", "IGNORE"}
            if config.DEFAULT_ACTION not in supported_actions:
                raise Exception("default_action should be set to one of the following values - " + str(supported_actions))
            config.FETCHERS = self.config_json["fetchers"]
            return config
        except Exception as ex:
            print("ERROR - Exception while reading the ApiSecurityManager configuration: %s" % ex)
            raise Exception()


    def read_conf_from_file(self):
        if os.path.isfile(self.config_file_path):
            try:
                with open(self.config_file_path) as config_file:
                    return config_file.read()
            except Exception as ex:
                print("ERROR - Exception while reading the ApiSecurityManager config file: %s" % ex)
                raise Exception()
        else:
            print("ERROR - Could Not find configuration file '" + self.config_file_path + "'")
            raise Exception("Could Not find configuration file")

