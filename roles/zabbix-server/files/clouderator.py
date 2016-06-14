#!/usr/bin/python
#
# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import sys
import json
import urllib2
from optparse import OptionParser
from cm_api.api_client import ApiResource

ADMIN_USER = "admin"
ADMIN_PASS = "admin"
CLUSTER_NAME = "CDH-cluster"

def main():
    #script options
    parser = OptionParser()
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False,
                      help='Be more verbose')
    parser.add_option('-m', '--manager', dest='manager',
                      help='CDH manager address',)
    parser.add_option('-a', '--action', type='choice', action='store', dest='action',
                      choices=['manager', 'service_list', 'service_health'], default='manager',
                      help='Action to take')
    parser.add_option('-n', '--name', dest='name',
                      help='Name of the item to check',)
    (options, args) = parser.parse_args()

    #logging
    logging.basicConfig()
    if not options.manager:
        print 'You must specify a manager address'
        sys.exit(-1)
    if options.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    api = ApiResource(options.manager, username=ADMIN_USER, password=ADMIN_PASS, version=9)
    try:
        cluster = api.get_cluster(CLUSTER_NAME)
        if options.action == 'manager':
            print 'OK'
            sys.exit(0)
    except urllib2.URLError:
        print 'Could not connect to API'
        sys.exit(-1)

    if options.action == 'service_list':
        response = {'data': [{'{#SERVICENAME}': svc.name} for svc in cluster.get_all_services()]}
        print json.dumps(response)
    elif options.action == 'service_health':
        if not options.name:
            print 'Must specify a name for this check'
            sys.exit(-1)
        svc = cluster.get_service(options.name)
        if svc.healthSummary == 'GOOD':
            print 'OK'
            sys.exit(0)
        else:
            failed_checks = " ".join([
                check['name'] for check in svc.healthChecks if check['summary'] != 'GOOD'
            ])
            print 'Health is {0}. Failed checks: {1}'.format(svc.healthSummary, failed_checks)

main()
