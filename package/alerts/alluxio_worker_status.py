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
  disk_used_critical_percent = 80 #default threshold

  PERCENT_USED_CRITICAL_KEY = "disk.used.critical.threshold"
  if PERCENT_USED_CRITICAL_KEY in parameters:
    disk_used_critical_percent = float(parameters[PERCENT_USED_CRITICAL_KEY]) * 100

  # We could check the pid file for this process
  #import params
  #pid_file = format("{params.pid_dir}/AlluxioMaster.pid")
  #check_process_status(pid_file)

  request_timeout = 5
  statuses = []

  # Hit the Alluxio Worker API to inspect uptime
  worker_status_url = "http://localhost:30000/api/v1/worker/uptime_ms/"
  response = None
  try:
    response = urllib2.urlopen(worker_status_url, timeout=request_timeout)
    response_data = response.read()
    if int(response_data) <= 0:
      return (RESULT_STATE_SKIPPED, ["Alluxio Worker is running but reported an uptime of 0."])
  except:
    statuses.append("Could not connect to the Alluxio Worker.")
  finally:
    if response is not None:
      try:
        response.close()
      except:
        pass

  # Hit the Alluxio Worker API to calculate disk percentage used
  worker_base_url = "http://localhost:30000/api/v1/worker/"
  response = None
  try:
    used_bytes_response = urllib2.urlopen(worker_base_url + "used_bytes", timeout=request_timeout)
    used_bytes = float(used_bytes_response.read())
    capacity_bytes_response = urllib2.urlopen(worker_base_url + "capacity_bytes", timeout=request_timeout)
    capacity_bytes = float(capacity_bytes_response.read())
    percent_used = (used_bytes / capacity_bytes) * 100
    if percent_used > disk_used_critical_percent:
      statuses.append("Alluxio Worker disk space used is above " + str(disk_used_critical_percent) + "%")
  except:
    statuses.append("Could not connect to the Alluxio Worker.")
  finally:
    if response is not None:
      try:
        response.close()
      except:
        pass

  if len(statuses) <= 0:
    return (RESULT_STATE_OK, ["Alluxio Worker is running."])
  else:
    return (RESULT_STATE_CRITICAL, statuses)
