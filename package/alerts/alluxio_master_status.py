#!/usr/bin/env python

"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import urllib2
import ambari_simplejson as json # simplejson is much faster comparing to Python 2.6 json module and has the same functions set.
import logging

from resource_management import *

RESULT_STATE_OK = 'OK'
RESULT_STATE_CRITICAL = 'CRITICAL'
RESULT_STATE_UNKNOWN = 'UNKNOWN'
RESULT_STATE_SKIPPED = 'SKIPPED'


logger = logging.getLogger('ambari_alerts')

def execute(configurations={}, parameters={}, host_name=None):
  """
  Returns a tuple containing the result code and a pre-formatted result label

  Keyword arguments:
  configurations (dictionary): a mapping of configuration key to value
  parameters (dictionary): a mapping of script parameter key to value
  host_name (string): the name of this host where the alert is running
  """
  if configurations is None:
    return (RESULT_STATE_UNKNOWN, ['There were no configurations supplied to the script.'])

  print "CONFIGS:"
  for c in configurations:
    print c
  print "PARAMETERS:"
  for p in parameters:
    print p

  # We could check the pid file for this process
  #import params
  #pid_file = format("{params.pid_dir}/AlluxioMaster.pid")
  #check_process_status(pid_file)

  request_timeout = 5
  statuses = []

  # Hit the Alluxio Master API to inspect uptime
  master_status_url = "http://localhost:19999/api/v1/master/uptime_ms/"
  response = None
  try:
    response = urllib2.urlopen(master_status_url, timeout=request_timeout)
    response_data = response.read()
    if int(response_data) <= 0:
      return (RESULT_STATE_SKIPPED, ["Alluxio Master is running but reported an uptime of 0."])
  except:
    statuses.append("Could not connect to the Alluxio Master.")
  finally:
    if response is not None:
      try:
        response.close()
      except:
        pass


  # Hit the Alluxio Proxy API to verify the service is running
  proxy_status_url = "http://localhost:39999/api/v1/proxy/info/"
  response = None
  try:
    # If we get a response, assume everything is groovy
    response = urllib2.urlopen(proxy_status_url, timeout=request_timeout)
  except:
    statuses.append("Could not connect to the Alluxio Proxy.")
  finally:
    if response is not None:
      try:
        response.close()
      except:
        pass

  if len(statuses) <= 0:
    return (RESULT_STATE_OK, ["Alluxio Master and Proxy are running."])
  else:
    return (RESULT_STATE_CRITICAL, statuses)
