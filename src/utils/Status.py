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
import time


class Status:

    def __init__(self, logger):
        self.logger = logger
        self.status = dict()
        self.status["time"] = 0
        self.status["has_errors"] = False
        self.status["apis"] = dict()
        self.status["apis"]["added"] = dict()
        self.status["apis"]["updated"] = dict()
        self.status["apis"]["deleted"] = dict()
        self.status["apis"]["added"]["success"] = []
        self.status["apis"]["added"]["error"] = []
        self.status["apis"]["updated"]["success"] = []
        self.status["apis"]["updated"]["error"] = []
        self.status["apis"]["deleted"]["success"] = []
        self.status["apis"]["deleted"]["error"] = []
        self.status["fetchers"] = dict()
        self.status["fetchers"]["success"] = []
        self.status["fetchers"]["error"] = []


    def update_api_error(self, status_type, value):
        self.update_api_status(status_type, "error", value)


    def update_api_success(self, status_type, value):
        self.update_api_status(status_type, "success", value)


    def update_api_status(self, status_type, result, value):
        self.status["apis"][status_type][result].append(value)


    def update_fetcher_error(self, value):
        self.status["fetchers"]["error"].append(value)


    def update_fetcher_success(self, value):
        self.status["fetchers"]["success"].append(value)


    def get_status(self):
        return self.status


    def report_status(self, path):
        if path is not None and path:
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
                status_file = os.path.join(path, "status.json")
                self.logger.info("Reporting status to %s", status_file)
                with open(status_file, 'w') as outfile:
                    json.dump(self.status, outfile)
            except Exception as ex:
                self.logger.error("Failed to report status to the status file. Error is %s", ex)


    def calculate_status(self):
        total_errors = 0
        for value in self.status["apis"].values():
            if len(value["error"]) > 0:
                total_errors += len(value["error"])
        if len(self.status["fetchers"]["error"]) > 0:
            total_errors += len(self.status["fetchers"]["error"])
        self.logger.info("There were %d errors while managing the APIs", total_errors)
        self.status["time"] = int(round(time.time() * 1000))
        if total_errors > 0:
            self.status["has_errors"] = True
            return 1
        else:
            self.status["has_errors"] = False
            return 0
