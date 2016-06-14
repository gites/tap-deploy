#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# recommended pylint: pylint docker_registry.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 docker_registry.py


from re import match
from ansible.module_utils.basic import *
import httplib2
import urllib
from json import loads


MODULE_ARGUMENTS = {
    'action': {'type': 'str', 'required': True},
    'slave-docker-registry': {'type': 'str'},
    'master-docker-registry': {'type': 'str'},
    'slave-docker-registry-ca': {'type': 'str'},
    'master-docker-registry-ca': {'type': 'str'},
    'slave-docker-registry-key': {'type': 'str'},
    'master-docker-registry-key': {'type': 'str'},
    'slave-docker-registry-cert': {'type': 'str'},
    'master-docker-registry-cert': {'type': 'str'},
    'image-name': {'type': 'str'},
    'image-tag': {'type': 'str'}
}


def createRegistryClient(module, dr='slave'):
  url = module.params.get("{0}-docker-registry".format(dr), None)
  if url is None:
    module.fail_json(msg="Module param {0}-docker-registry is not set".format(dr))
  if not match("^http[s]?://[a-z0-9][-a-z.0-9]*(:(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}))?/?$", url):
    module.fail_json(msg="Host url is not valid url address")
  if match("^http://.*$", url):
    client = DockerRegistryInsecureClient(module, "{0}-docker-registry".format(dr))
    client.checkApiVersion()
    return client
  if match("^https://.*$", url):
    client = DockerRegistrySecureClient(module, "{0}-docker-registry".format(dr))
    client.checkApiVersion()
    return client
  module.fail_json(msg="Registry url does not matching http or https protocol")


class DockerRegistryInsecureClient:

  def __init__(self, module, docker_registry):
    self.__module = module
    self.__docker_registry = docker_registry
    self.__url = module.params.get(docker_registry, None)
    if self.__url[-1] == '/':
      self.__url = self.__url + '/'

  def sendRequest(self, request, method='GET', data={}, headers={}, autofail=True, asJson=True):
    http = httplib2.Http()
    try:
      response, context = http.request(self.__url + request, method, body=urllib.urlencode(data), headers=headers)
      if not match("^2..$", str(response.status)) and autofail:
        self.__module.fail_json(msg="Http request to docker-registry failed - invalid response", url=self.__url,
                                request=request, method=method, headers=headers, data=data, response=response, context=context)
      return (response, loads(context) if asJson else context)
    except Exception as e:
      self.__module.fail_json(msg="Http request to docker-registry failed", url=self.__url, request=request, method=method, headers=headers, data=data, exception=str(e))

  def checkApiVersion(self):
    response = self.sendRequest('v2/', autofail=False)
    if match("^4..$", str(response[0].status)):
      self.__module.fail_json("Api version 2 not supported for " + self.__docker_registry)

  def listCatalog(self):
    response = self.sendRequest('v2/_catalog')[1]
    return response['repositories']

  def getTags(self, name):
    response = self.sendRequest('v2/{0}/tags/list'.format(name))[1]
    return response['tags']


class DockerRegistrySecureClient:

  def __init__(self, module, docker_registry):
    self.__module = module
    self.__docker_registry = docker_registry
    self.__url = module.params.get(docker_registry, None)
    if self.__url[-1] == '/':
      self.__url = self.__url + '/'

    self.__ca = module.params.get("{0}-ca".format(docker_registry), None)
    self.__cert = module.params.get("{0}-cert".format(docker_registry), None)
    self.__key = module.params.get("{0}-key".format(docker_registry), None)

    if self.__key is None:
      module.fail_json(msg="Param {0}-key is not set for {0} in secured connection".format(docker_registry))
    if self.__cert is None:
      module.fail_json(msg="Param {0}-cert is not set for {0} in secured connection".format(docker_registry))
    if self.__ca is None:
      module.fail_json(msg="Param {0}-ca is not set for {0} in secured connection".format(docker_registry))

  def sendRequest(self, request, method='GET', data={}, headers={}, autofail=True, asJson=True):
    try:
      http = httplib2.Http(ca_certs=self.__ca, disable_ssl_certificate_validation=True)
    except Exception as e:
      self.__module.fail_json(msg="Unable to create obiect with CA", exception=str(e))

    try:
      http.add_certificate(key=self.__key, cert=self.__cert, domain='')
    except Exception as e:
      self.__module.fail_json(msg="Unable to enable ssl authentication", exception=str(e))

    try:
      response, context = http.request(self.__url + request, method, body=urllib.urlencode(data), headers=headers)
      if not match("^2..$", str(response.status)) and autofail:
        self.__module.fail_json(msg="Http request to docker-registry failed - invalid response", url=self.__url,
                                request=request, method=method, headers=headers, data=data, response=response, context=context)
      return (response, loads(context) if asJson else context)
    except Exception as e:
      self.__module.fail_json(msg="Http request to docker-registry failed", url=self.__url, request=request, method=method, headers=headers, data=data, exception=str(e))

  def checkApiVersion(self):
    response = self.sendRequest('v2/', autofail=False)
    if match("^4..$", str(response[0].status)):
      self.__module.fail_json("Api version 2 not supported for " + self.__docker_registry)

  def listCatalog(self):
    response = self.sendRequest('v2/_catalog')[1]
    return response['repositories']

  def getTags(self, name):
    response = self.sendRequest('v2/{0}/tags/list'.format(name))[1]
    return response['tags']


def findAction(name):
  current_module = sys.modules[__name__]
  functions = [current_module.__dict__.get(a) for a in dir(current_module) if isinstance(current_module.__dict__.get(a), types.FunctionType)]
  actions = [a for a in functions if a.func_name == 'action_{0}'.format(name) and a.func_code.co_argcount == 1]

  if len(actions) == 0:
    return None

  return actions[0]


# list diff
def action_list(module):
  client_slave = createRegistryClient(module)
  client_master = createRegistryClient(module, "master")

  update = []

  list_slave = client_slave.listCatalog()
  list_master = client_master.listCatalog()

  for repo in list_slave:
    tags_slave = client_slave.getTags(repo)
    tags_master = client_master.getTags(repo) if repo in list_master else []
    for tag in tags_slave:
      if tag not in tags_master:
        update.append({'name': repo, 'tag': tag})

  module.exit_json(data=update, changed=len(update) > 0)


# list diff
def action_exists(module):
  client_master = createRegistryClient(module, "master")

  name = module.params.get('image-name', None)
  if name is None or name == '':
    module.fail_json(msg="Param image-name have to be set and not empty for exists action")

  tag = module.params.get('image-tag', None)
  if tag is None or tag == '':
    module.fail_json(msg="Param image-tag have to be set and not empty for exists action")

  list_master = client_master.listCatalog()
  if name in list_master:
    tags_master = client_master.getTags(name)
    if tag in tags_master:
      module.exit_json(exists=True, changed=False, tag=tag, name=name, msg="Image exists in remote docker registry")
  module.exit_json(exists=False, changed=False, tag=tag, name=name, msg="Image does not exists in remote docker registry")


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

  action = findAction(module.params.get('action'))

  if action is None:
    module.fail_json(msg="Unable to find specified action", action=module.param.get('action'))

  action(module)

  module.fail_json(msg="Action did not finish with exit state", action=module.param.get('action'))

main()
