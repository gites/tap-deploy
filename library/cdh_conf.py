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

import socket
from ansible.module_utils.basic import *
from cm_api.api_client import ApiResource

CLUSTER_NAME = "CDH-cluster"
MODULE_ARGUMENTS = {
  'host': {'type': 'str', 'required': True},
  'user': {'type': 'str', 'required': True},
  'pass': {'type': 'str', 'required': True}
}


class CdhConfiguration(object):
  def __init__(self, cm_api, name):
    self.cm_api = cm_api
    self.clusterName = name
    self.configMap = self.cm_api.get('cm/deployment')

  def get_config_for_cluster(self, cm_api=None):
    configuration = dict.fromkeys({'services', 'cloudera'})
    # Services
    configuration['services'] = self._get_services_conf()
    # Cloudera
    configuration['cloudera'] = self._get_cloudera_conf()

    return configuration


  def _get_cloudera_conf(self):
    conf = dict.fromkeys({'users', 'config'})
    conf['users'] = self._transform_list_to_dict(self.configMap['users'], 'name')
    conf['config'] = self._transform_list_to_dict(self.configMap['managerSettings']['items'], 'name')

    return conf


  def _get_roles_hosts(self, name):
    cluster = self._find_item_by_attr_value(name, 'name', self.configMap['clusters'])
    hosts_conf = dict()
    hosts = self._transform_list_to_dict(self.configMap['hosts'], 'hostId')

    for service in cluster['services']:
      service_obj = self._find_item_by_attr_value(service['name'], 'name', cluster['services'])
      roles = self._transform_list_to_dict(service_obj['roles'], 'name')
      for role in roles:
        for host in roles[role]['hostRef']:
          id = roles[role]['hostRef'][host]
          hosts_conf[role] = hosts[id]

    return hosts_conf


  def _get_services_conf(self):
    cluster = self._find_item_by_attr_value(self.clusterName, 'name', self.configMap['clusters'])
    api_cluster = self.cm_api.get_cluster(self.clusterName)
    services_conf = dict.fromkeys(service['name'] for service in cluster['services'])

    for name in services_conf:
      # Get from config
      service = self._find_item_by_attr_value(name, 'name', cluster['services'])
      services_conf[name] = dict.fromkeys({'roles', 'rolesConfigGroup', 'config', 'rolesHosts'})
      services_conf[name]['roles'] = self._get_roles(service)
      services_conf[name]['rolesHosts'] = self._get_roles_hosts(service)
      services_conf[name]['rolesConfigGroup'] = self._get_rolesConfigGroup(service)

      # Get from cm_api
      api_service = api_cluster.get_service(name)
      services_conf[name]['config'] = self._transform_config_to_dict(api_service.get_config(view='full')[0])

    return services_conf


  def _get_roles_hosts(self, service):
    hosts = self._transform_list_to_dict(self.configMap['hosts'], 'hostId')
    hosts_conf = dict()

    roles = self._transform_list_to_dict(service['roles'], 'name')
    for role in roles:
      for host in roles[role]['hostRef']:
        id = roles[role]['hostRef'][host]
        hosts_conf[role] = hosts[id]

    return hosts_conf


  def _get_roles(self, service):
    api_cluster = self.cm_api.get_cluster(self.clusterName)
    api_service = api_cluster.get_service(service['name'])
    roles = self._transform_list_to_dict(service['roles'], 'name')
    for role in roles:
      roles[role]['config'] = self._transform_config_to_dict(api_service.get_role(role).get_config(view='full'))

    return roles


  def _get_rolesConfigGroup(self, service):
    api_cluster = self.cm_api.get_cluster(self.clusterName)
    api_service = api_cluster.get_service(service['name'])
    rolesConfigGroup = self._transform_list_to_dict(service['roleConfigGroups'], 'name')
    for role in rolesConfigGroup:
      rolesConfigGroup[role]['config'] = self._transform_config_to_dict(
        api_service.get_role_config_group(role).get_config(view='full'))

    return rolesConfigGroup


  def _transform_config_to_dict(self, dictionary):
    new_dict = dict()
    for key in dictionary:
      value = getattr(dictionary[key], 'value', dictionary[key].default)
      if value is None:
        value = dictionary[key].default
      new_dict[key] = {'value': value, 'default': dictionary[key].default}

    return new_dict


  def _transform_list_to_dict(self, list, key_attr_name):
    new_dict = dict()
    for dictionary in list:
      new_dict[dictionary[key_attr_name]] = dictionary.copy()

    return new_dict


  def _find_item_by_attr_value(self, attr_value, attr_name, array_with_dicts):
    try:
      return next(item for item in array_with_dicts if item[attr_name] == attr_value)
    except StopIteration:
      return dict()


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)
  host_a = module.params.get('host', None)
  pass_a = module.params.get('pass', None)
  user_a = module.params.get('user', None)

  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  result = sock.connect_ex((host_a, 7183))

  if result == 0:
    # Port is open then use https port
    api = ApiResource(server_host=host_a, username=user_a, password=pass_a, use_tls=True, version=9)
  else:
    # Port is not open then use http port
    api = ApiResource(server_host=host_a, username=user_a, password=pass_a, version=9)

  cdh_config = CdhConfiguration(api, CLUSTER_NAME)
  module.exit_json(changed=True, msg='Collected', config=cdh_config.get_config_for_cluster(CLUSTER_NAME))


main()
