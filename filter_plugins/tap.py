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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible import errors
from random import choice
from string import ascii_uppercase, ascii_lowercase, digits
from json import dumps
from urlparse import urlparse

def rand_password(a, length=32):
  if a is None or a == '':
    try:
      return ''.join(choice(ascii_uppercase + digits + ascii_lowercase) for _ in range(length))
    except TypeError as e:
      raise errors.AnsibleFilterError('rand_password() can only be used with numbers: %s' % str(e))
  return a


def pass_manager(a, section, option, value):
  if type(a) is not dict and type(a) is not list:
    raise Exception("Type is not a dict, nor a list")
  if section not in a:
    a[section] = {}

  if option not in a[section]:
    a[section][option] = value

  return a


def split(a, s):
  return a.split(s)


def json_to_str(a):
  if type(a) is not dict and type(a) is not list:
    raise Exception("Type is not a dict, nor a list")
  return dumps(a)


def role_host(json, service, role):
  return json['config']['services'][service]['rolesHosts'][role]['hostname']


def role_ip(json, service, role):
  return json['config']['services'][service]['rolesHosts'][role]['ipAddress']


def role_prop(json, service, role, property):
  return json['config']['services'][service]['roles'][role]['config'][property]['value']


def service_config(json, service, property, value):
  return json['config']['services'][service]['config'][property][value]


def cloudera(json, property):
  return json['config']['cloudera']['config'][property]['value']


def srv_def(json, service, property):
  return service_config(json, service, property, 'default')


def srv_prop(json, service, property):
  return service_config(json, service, property, 'value')


def zookeeper_cluster(json, service, port):
  role_hosts = json['config']['services'][service]['rolesHosts'];
  cluster_hosts = []
  for host in role_hosts:
    cluster_hosts.append(role_hosts[host]['hostname'] + ':' + port)

  return ','.join(cluster_hosts)

def to_port(url):
  '''
  Takes port part out of url specified in RFC 1808 format.
  '''
  if not url:
    return ''

  res = urlparse(url)
  return res.port

def to_hostname(url):
  '''
  Takes hostname part out of url specified in RFC 1808 format.
  '''
  if not url:
    return ''

  res = urlparse(url)
  return res.hostname

def to_java_format(no_proxy):
  '''
  Convert no_proxy value from unix convention to a format required by Java.
  For example value '.example.com,.cluster.local' will translated into
  '*.example.com|*.cluster.local'.
  '''

  if not no_proxy:
    return ''

  splits = [split.replace('.', '*.', 1) for split in no_proxy.split(',')]

  #TODO: add '|localhost|127.*|[::1]', or not ...
  return '|'.join(splits)

def add_prefix(strings, prefix):
  '''
  Add prefix to each string value in table
  '''
  if type(strings) is str:
    return prefix + strings
  if type(strings) is list:
    return [prefix + str(item) for item in strings]
  raise Exception("Type {0} is not supported".format(str(type(strings))))


def add_suffix(strings, suffix):
  '''
  Add suffix to each string value in table
  '''
  if type(strings) is str:
    return strings + suffix
  if type(strings) is list:
    return [str(item) + suffix for item in strings]
  raise Exception("Type {0} is not supported".format(str(type(strings))))

class FilterModule(object):
  ''' TAP core jinja2 filters '''

  def filters(self):
    return {
      'rand_password': rand_password,
      'pass_manager': pass_manager,
      'json_to_str': json_to_str,
      'split': split,
      'role_host': role_host,
      'role_ip' : role_ip,
      'role_prop': role_prop,
      'srv_prop': srv_prop,
      'srv_def': srv_def,
      'cloudera': cloudera,
      'zookeeper_cluster': zookeeper_cluster,
      'to_java_format': to_java_format,
      'to_hostname': to_hostname,
      'to_port': to_port,
      'add_suffix': add_suffix,
      'add_prefix': add_prefix
    }
