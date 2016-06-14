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

from re import match
from socket import inet_aton, inet_ntoa
from struct import unpack, pack


def get_hostname(name, ip_address, subnet=24):
  if type(ip_address) is not str:
    ip_address = str(ip_address)
  if match("^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$",
           ip_address) is None:
    raise Exception("IP string is invalid -- {0}".format(ip_address))
  if type(subnet) is not int:
    raise Exception("Port is not int")

  ip = unpack("!L", inet_aton(ip_address))[0]
  mask = (1L << 32 - subnet) - 1

  host_hip = ip & mask
  host_hip_address = inet_ntoa(pack("!L", host_hip)).split(".")
  while host_hip_address[0] == '0':
    host_hip_address.pop(0)

  return "{0}-{1}".format(name, '-'.join(host_hip_address))


INSTANCES = {
    'hadoop-master-controller': {
        'count': {'minimal': 1, 'maximum': 1},
        'collides': ["compute-master", "compute-worker", "compute-nat", "compute-ca", "storage-master", "storage-worker"],
        'group': 3
    },
    'hadoop-master-primary': {
        'count': {'minimal': 1, 'maximum': 1},
        'collides': ["compute-master", "compute-worker", "compute-nat", "compute-ca", "storage-master", "storage-worker", "hadoop-master-secondary", "hadoop-master"],
        'group': 3
    },
    'hadoop-master-secondary': {
        'count': {'minimal': 0, 'maximum': 1},
        'collides': ["compute-master", "compute-worker", "compute-nat", "compute-ca", "storage-master", "storage-worker", "hadoop-master-primary", "hadoop-master"],
        'group': 3
    },
    'hadoop-master': {
        'count': {'minimal': 0, 'maximum': 5},
        'collides': ["compute-master", "compute-worker", "compute-nat", "compute-ca", "storage-master", "storage-worker", "hadoop-master-primary", "hadoop-master-secondary"],
        'group': 3
    },
    'hadoop-worker': {
        'count': {'minimal': 1, 'maximum': None},
        'collides': ["compute-master", "compute-worker", "compute-nat", "compute-ca", "storage-master", "storage-worker"],
        'group': 3
    },
    'compute-master': {
        'count': {'minimal': 1, 'maximum': 7},
        'colides': ["hadoop-master-controller", "hadoop-master-primary", "hadoop-master-secondary", "hadoop-master", "hadoop-worker"],
        'group': 1
    },
    'compute-worker': {
        'count': {'minimal': 1, 'maximum': None},
        'colides': ["hadoop-master-controller", "hadoop-master-primary", "hadoop-master-secondary", "hadoop-master", "hadoop-worker"],
        'group': 2
    },
    'storage-master': {
        'count': {'minimal': 1, 'maximum': 7},
        'colides': ["hadoop-master-controller", "hadoop-master-primary", "hadoop-master-secondary", "hadoop-master", "hadoop-worker"],
        'group': 4
    },
    'storage-worker': {
        'count': {'minimal': 1, 'maximum': 7},
        'colides': ["hadoop-master-controller", "hadoop-master-primary", "hadoop-master-secondary", "hadoop-master", "hadoop-worker"],
        'group': 4
    },
    'storage-client': {
        'count': {'minimal': 0, 'maximum': None},
        'selector': ['compute-worker', 'compute-master'],
        'colides': ["hadoop-master-controller", "hadoop-master-primary", "hadoop-master-secondary", "hadoop-master", "hadoop-worker"],
        'group': 4
    },
    'jumpbox': {
        'count': {'minimal': 1, 'maximum': 1},
        'group': 0
    },
    'zabbix-master': {
        'count': {'minimal': 0, 'maximum': 1},
        'group': 1
    }
}


def parse_instances(instances):
  parsed = {}
  for item, key in INSTANCES.iteritems():
    parsed[str(item)] = []

  instance_names = []

  for instance, tags in instances.iteritems():
    if str(instance) in instance_names:
      raise Exception("Instance name {0} is not unique".format(instance))
    instance_names.append(str(instance))
    for role in tags['roles']:
      if str(role) not in parsed:
        raise Exception("Unknown role {0} for instance {1}".format(role, instance))
      parsed[str(role)].append(str(instance))

  for item, key in INSTANCES.iteritems():
    parsed[str(item)] = list(set(parsed[str(item)]))

    if key['count']['minimal'] is not None and len(parsed[str(item)]) < key['count']['minimal']:
      raise Exception("You have to specify atleast {0} instance of {1}".format(key['count']['minimal'], item))
    if key['count']['maximum'] is not None and len(parsed[str(item)]) > key['count']['maximum']:
      raise Exception("You have to specify maximum {0} instances of {1}".format(key['count']['maximum'], item))

  for item, key in INSTANCES.iteritems():
    if 'selector' in key:
      data = parsed[str(item)]
      for selector in key['selector']:
        if str(selector) == str(item):
          raise Exception("You can not include role inside itself")
        data = data + parsed[str(selector)]
      parsed[str(item)] = data

    parsed[str(item)] = list(set(parsed[str(item)]))

  for instance, tags in instances.iteritems():
    roles = tags['roles']
    for role in roles:
      if 'collides' not in INSTANCES[str(role)]:
        continue
      for collision in INSTANCES[str(role)]['collides']:
        if collision == role:
          continue
        if collision in roles:
          raise Exception("For instance {0} role {1} colides with {2}".format(instance, role, collision))

  return parsed

CORE_PARAMS = {
    'user': {
        'required': True,
        'ansible': {
            'type': 'inventory',
            'name': 'ansible_user'
        }
    },
    'port': {
        'required': False,
        'default': '22',
        'ansible': {
            'type': 'inventory',
            'name': 'ansible_port'
        }
    },
    'ssh-key': {
        'required': False,
        'default': "~/.ssh/id_rsa",
        'ansible': {
            'type': 'inventory',
            'name': 'ansible_ssh_private_key_file'
        }
    },
    'storage': {
        'required': False,
        'default': {},
        'ansible': {
            'type': 'host',
            'name': 'storage'
        }
    }
}


def check_instances(instances, role_params={}):
  parsed = {}
  var = {}
  params = CORE_PARAMS.copy()
  params.update(role_params)
  for instance, tags in instances.iteritems():
    parsed[str(instance)] = {}
    var[str(instance)] = {}
    for param, options in params.iteritems():

      if str(param) in tags and tags[str(param)] is not None and tags[str(param)] != '':
        value = tags[str(param)]
      elif 'required' in options and options['required']:
        if str(param) not in tags or tags[str(param)] is None or tags[str(param)] == '':
          raise Exception("Param {0} is required for instance {1}".format(param, instance))
        value = tags[str(param)]
      elif 'default' not in options:
        raise Exception("Not required params requires default value {0}".format(param))
      else:
        value = options['default']

      if 'ansible' not in options or 'type' not in options['ansible'] or options['ansible']['type'] == None or options['ansible']['type'] == '' or 'name' not in options['ansible'] or options['ansible']['name'] == None or options['ansible']['name'] == '':
        raise Exception("You have to specify what to do with param")

      if value != None and value != '':
        if options['ansible']['type'] == 'inventory':
          parsed[str(instance)][str(options['ansible']['name'])] = str(value)
        elif options['ansible']['type'] == 'host':
          var[str(instance)][str(options['ansible']['name'])] = str(value)
        else:
          raise Exception("Unknown value for ansible param type for param {0}".format(param))

    if 'connection' not in tags:
      raise Exception("Connection should be defined for {0}".format(instance))
    if 'type' not in tags['connection']:
      raise Exception("Type should be defined for connection for instance {0}".format(instance))

    if tags['connection']['type'] == 'local':
      if 'jumpbox' not in tags['roles']:
        raise Exception("You can only set local connestion on jumpbox")
      parsed[str(instance)]['ansible_connection'] = 'local'
    elif tags['connection']['type'] == 'ssh-key':
      if 'jumpbox' in tags['roles']:
        raise Exception("Local connection can be only set for instance with jumpbox role")
      parsed[str(instance)]['ansible_connection'] = 'ssh'
    elif tags['connection']['type'] == 'ssh-pass':
      raise Exception("Connection type 'ssh-pass' is not supported yes")
    else:
      raise Exception("Unknown connection type {0} for instance {1}".format(tags['connection']['type'], instance))

  return {'inventory': parsed, 'vars': var}

def get_instance_group(roles):
  return min([INSTANCES[role]['group'] for role in roles])

def generate_inventory_record(instance_params, instance, domain):
  params = ' '.join(['{0}="{1}"'.format(item[0], item[1]) for item in instance_params[str(instance)].iteritems()])
  return "{0}.instance.{2} {1}".format(instance, params, domain)


def get_host_vars(vars_map, instance):
  return [item for item in vars_map if instance in item['hosts']]


def get_host_health_map(instance_map, instance):
  checks = []
  for item in instance_map:
    if instance not in item['from']:
      continue
    port = '22' if 'port' not in item else item['port']
    for target in item['to']:
      checks.append({ 'host': target, 'port': port })
  return checks


class FilterModule(object):
  ''' TAP core jinja2 filters '''

  def filters(self):
    return {
        'get_hostname': get_hostname,
        'parse_instances': parse_instances,
        'check_instances': check_instances,
        'generate_inventory_record': generate_inventory_record,
        'get_host_vars': get_host_vars,
        'get_host_health_map': get_host_health_map,
        'get_instance_group': get_instance_group
    }
