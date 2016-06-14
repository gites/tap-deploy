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

import json
import yaml
import requests
import time

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: tapkube
short_description: Manage Kubernetes resources.
options:
  api_endpoint:
    description:
      - API endpoint to the kubernetes cluseter
    required: true
    default: null
  inline_data:
    description:
      - Kubernetes resource definition inline
    required: false
    default: null
  file_reference:
    description:
      - Path to file with Kubernetes resource definition
    required: false
    default: null
  insecure:
    description:
      - Do not use secure (https) connection
    required: false
    default: False
  state:
    description:
      - Requested state
    required: true
    default: "present"
    choices: ["present", "absent", "update", "replace"]
  do_not_retry:
    description:
      - Do not retry calls to kubernetes api
    default: False
  use_anti_affinity:
      description:
      - Use Pod Anti Affinity rule to ensure that pods are not being scheduled on the same nodes.
    default: False
  ca_cert_file:
    description:
      - Path to file with ca cert
    required: false
    default: /home/centos/.kube/ca.crt
  client_cert_file:
    description:
      - Path to file with client cert
    required: false
    default: /home/centos/.kube/admin.crt
  client_key_file:
    description:
      - Path to file with client key
    required: false
    default: /home/centos/.kube/admin.key
'''

DEFAULT_NAMESPACE = "default"
TYPES_API_MAP = {
    "binding": "/api/v1/namespaces/{namespace}/bindings",
    "configmap": "/api/v1/namespaces/{namespace}/configmaps",
    "deployment": "/apis/extensions/v1beta1/namespaces/{namespace}/deployments",
    "daemonset": "/apis/extensions/v1beta1/namespaces/{namespace}/daemonsets",
    "endpoints": "/api/v1/namespaces/{namespace}/endpoints",
    "ingress": "/apis/extensions/v1beta1/namespaces/{namespace}/ingresses",
    "limitrange": "/api/v1/namespaces/{namespace}/limitranges",
    "namespace": "/api/v1/namespaces",
    "node": "/api/v1/nodes",
    "persistentvolume": "/api/v1/persistentvolumes",
    "persistentvolumeclaim": "/api/v1/namespaces/{namespace}/persistentvolumeclaims",
    "pod": "/api/v1/namespaces/{namespace}/pods",
    "podtemplate": "/api/v1/namespaces/{namespace}/podtemplates",
    "replicationcontroller": "/api/v1/namespaces/{namespace}/replicationcontrollers",
    "resourcequota": "/api/v1/namespaces/{namespace}/resourcequotas",
    "scale": "/apis/extensions/v1beta1/namespaces/{namespace}/deployments/{scalename}/scale",
    "secret": "/api/v1/namespaces/{namespace}/secrets",
    "service": "/api/v1/namespaces/{namespace}/services",
    "serviceaccount": "/api/v1/namespaces/{namespace}/serviceaccounts",
    "job": "/apis/extensions/v1beta1/namespaces/{namespace}/jobs"
}

STATES = ["present", "absent", "update", "replace", "scale"]
FIELDS = {
    "api_endpoint": {"required": True, "type": "str"},
    "inline_data": {"required": False, "type": "str"},
    "file_reference": {"required": False, "type": "str"},
    "insecure": {"default": False, "type": "bool"},
    "state": {"default": "present", "choices": STATES, "type": "str"},
    "ca_cert_file": {"default": "/home/centos/.kube/ca.crt", "type": "str"},
    "client_cert_file": {"default": "/home/centos/.kube/admin.crt", "type": "str"},
    "client_key_file": {"default": "/home/centos/.kube/admin.key", "type": "str"},
    "do_not_retry": {"default": False, "type": "bool"},
    "use_anti_affinity": {"default": False, "type": "bool"}
}

RETRY_TIME_IN_SECONDS = 180
RETRY_DELAY_IN_SECONDS = 5

module = AnsibleModule(
        argument_spec=FIELDS,
        mutually_exclusive=(('inline_data', 'file_reference'),),
        required_one_of=(('inline_data', 'file_reference'),)
)


def main():
    api_endpoint = module.params.get('api_endpoint')
    inline_data = module.params.get('inline_data')
    file_reference = module.params.get('file_reference')
    state = module.params.get('state')
    insecure = module.params.get('insecure')

    resources_data = get_resources_data(inline_data, file_reference)

    resources = []
    for r in resources_data:
        resources.append(Resource(state, api_endpoint, insecure, r))

    process_resources(resources)


def get_yaml_from_file(file_reference):
    """
    Get yaml data from file
    :param path: Path to the file with data
    :return: Array with  yaml Python objects
    """
    with open(file_reference, 'r') as yaml_file:
        data = [r for r in yaml.load_all(yaml_file)]
    return data


def get_resources_data(inline_data, file_reference):
    """
    Get resource data from inline_data or from file
    :param inline_data: yaml data
    :param file_reference: path to file with yaml data
    :return:
    """
    if inline_data:
        return [yaml.load(inline_data)]
    else:
        try:
            return get_yaml_from_file(file_reference)
        except Exception as e:
            module.fail_json(msg="Unable to retrieve yaml data from file %s. Error: %s" % (file_reference, str(e)))


def process_resources(resources):
    module_response = []
    task_changed = False
    for r in resources:
        resource_changed, resource_response = r.process()
        task_changed |= resource_changed
        module_response.append(resource_response)

    module.exit_json(changed=task_changed, api_response=module_response)


class Resource(object):
    def __init__(self, requested_state, api_endpoint, insecure, data):
        self.requested_state = requested_state
        self.api_endpoint = api_endpoint
        self.data = data
        self.kind = self.data.get("kind").lower()
        if module.params.get('use_anti_affinity'):
            self.add_anti_affinity()
        if insecure:
            self.protocol = "http"
            self.ca_cert_file = None
            self.client_cert_file = None
            self.client_key_file = None
        else:
            self.protocol = "https"
            self.ca_cert_file = module.params.get('ca_cert_file')
            self.client_cert_file = module.params.get('client_cert_file')
            self.client_key_file = module.params.get('client_key_file')
        self.choice_map = {
            "present": self.create_resource_in_kubernetes,
            "absent": self.delete_resource_in_kubernetes,
            "update": self.update_resource_in_kubernetes,
            "replace": self.replace_resource_in_kubernetes,
            "scale": self.scale_resource_in_kubernetes,
        }
        self.headers={"Content-Type": "application/json"}
        self.name = self.get_resource_name_from_data()

    def add_anti_affinity(self):
        if self.kind == "deployment":
            annotations = self.data.get("spec").get("template").get("metadata").get("annotations", {})
            pod_app_value = self.data.get("spec").get("template").get("metadata").get("labels").get("app")
            annotations["scheduler.alpha.kubernetes.io/affinity"] = self.create_affinity_annotation_json("app", [pod_app_value])
            self.data["spec"]["template"]["metadata"]["annotations"] = annotations

    def create_affinity_annotation_json(self, expression_key, expression_values):
        expression = {
            "key": expression_key,
            "operator": "In",
            "values": expression_values
        }
        label_selector = {
            "matchExpressions": [expression]
        }
        required_during_scheduling_ignored_during_execution = {
            "labelSelector": label_selector,
            "topologyKey": "kubernetes.io/hostname"
        }
        pod_anti_affinity = {
            "requiredDuringSchedulingIgnoredDuringExecution": [required_during_scheduling_ignored_during_execution]
        }
        affinity = {
            "podAntiAffinity": pod_anti_affinity
        }

        return json.dumps(affinity)

    def get_resource_name_from_data(self):
        if "metadata" not in self.data:
            module.fail_json(msg="No metadata in kubernetes resource definition")
        if "name" not in self.data.get("metadata"):
            module.fail_json(msg="No name in metadata in kubernetes resource definition")
        return self.data.get("metadata").get("name")

    def process(self):
        url = self.build_url()

        if module.params.get('do_not_retry'):
            return self.choice_map.get(self.requested_state)(url)
        else:
            exception = Exception()
            #retry loop
            for x in range(0, RETRY_TIME_IN_SECONDS/RETRY_DELAY_IN_SECONDS):
                try:
                    return self.choice_map.get(self.requested_state)(url)
                except Exception as e:
                    exception = e
                time.sleep(RETRY_DELAY_IN_SECONDS)
            module.fail_json(msg=exception.message)

    def build_url(self):
        namespace = self.data.get('metadata').get('namespace', DEFAULT_NAMESPACE)
        try:
            url = self.api_endpoint + TYPES_API_MAP[self.kind]
        except KeyError:
            module.fail_json(msg="No such kubernetes resource kind: %s" % self.kind)
        url = url.replace("{namespace}", namespace)
        url = url.replace("{scalename}", self.name)
        url = self.protocol+"://"+url

        return url

    def get_kubernetes_resource(self):
        url = self.build_url()
        response = requests.get(url=url+"/"+self.name, json=self.data, headers=self.headers, verify=False, cert=(self.client_cert_file, self.client_key_file))
        if response.status_code >= 200 and response.status_code < 300:
            return response.json()

        raise Exception("Unable to get resource: %s error: %s" % (self.name, response.json()))

    def create_resource_in_kubernetes(self, url):
        response = requests.post(url=url, json=self.data, headers=self.headers, verify=False, cert=(self.client_cert_file, self.client_key_file))

        if response.status_code >= 200 and response.status_code < 300:
            return True, response.json()
        elif response.status_code == requests.codes.conflict or response.status_code == requests.codes.unprocessable_entity:
            try:
                return self.update_resource_in_kubernetes(url)
            except Exception as e:
                raise Exception("Unable to create resource, error: %s Trying to update resource, error: %s" % (response.json(), e.message))

        raise Exception("Unable to create resource, error: %s" % response.json())

    def delete_resource_in_kubernetes(self, url):
        response = requests.delete(url=url+"/"+self.name, json=self.data, headers=self.headers, verify=False, cert=(self.client_cert_file, self.client_key_file))

        if response.status_code >= 200 and response.status_code < 300:
            return True, response.json()
        elif response.status_code == requests.codes.not_found:
            return False, "Resource: %s already deleted" % self.name

        raise Exception("Unable to delete resource: %s error: %s" % (self.name, response.json()))

    def replace_resource_in_kubernetes(self, url):
        response = requests.put(url=url+"/"+self.name, json=self.data, headers=self.headers, verify=False, cert=(self.client_cert_file, self.client_key_file))

        if response.status_code >= 200 and response.status_code < 300:
            return True, response.json()
        elif response.status_code == requests.codes.conflict:
            resource = self.get_kubernetes_resource()
            return False, resource

        raise Exception("Unable to replace resource: %s error: %s" % (self.name, response.json()))

    def scale_resource_in_kubernetes(self, url):
        response = requests.put(url=url, json=self.data, headers=self.headers, verify=False, cert=(self.client_cert_file, self.client_key_file))

        if response.status_code >= 200 and response.status_code < 300:
            return True, response.json()
        elif response.status_code == requests.codes.conflict:
            resource = self.get_kubernetes_resource()
            return False, resource

        raise Exception("Unable to scale resource: %s error: %s" % (self.name, response.json()))

    def update_resource_in_kubernetes(self, url):
        resource_data_before_update = self.get_kubernetes_resource()
        response = requests.patch(url=url+"/"+self.name, json=self.data, headers={"Content-Type": "application/merge-patch+json"}, verify=False, cert=(self.client_cert_file, self.client_key_file))

        if response.status_code >= 200 and response.status_code < 300:
            resource_data_after_update = self.get_kubernetes_resource()
            if resource_data_before_update.get("metadata").get("resourceVersion") == resource_data_after_update.get("metadata").get("resourceVersion"):
                return False, response.json()
            return True, response.json()
        elif response.status_code == requests.codes.conflict:
            resource = self.get_kubernetes_resource()
            return False, resource

        raise Exception("Unable to update resource: %s error: %s" % (self.name, response.json()))


if __name__ == '__main__':
    main()
