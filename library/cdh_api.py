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

from socket import socket, AF_INET, SOCK_STREAM
from sys import modules
from types import FunctionType

from json import dumps
from cm_api.api_client import ApiResource
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = ''''''
EXAMPLES = '''
# Update admin password
- name: Update admin password
  cdh_api:
    action: update_admin_password
    host: localhost
    api_username: admin
    api_password: admin
    password: new_password

# Create or update test user with read-only role
- name: Create test user
  cdh_api:
    action: create_user
    host: localhost
    api_username: admin
    api_password: new_password
    username: test
    password: test_password
    roles:
      - ROLE_USER
'''

MODULE_ARGUMENTS = {
    'host': {'type': 'str', 'required': True},
    'action': {'type': 'str', 'required': True},
    'api_version': {'type': 'str', 'default': 9},
    'api_username': {'type': 'str', 'default': 'admin'},
    'api_password': {'type': 'str', 'default': 'admin'},
    'username': {'type': 'str'},
    'password': {'type': 'str'},
    'roles': {'type': 'list', 'default': ['ROLE_USER']}
}


def determine_api_protocol(host):
    sock = socket(AF_INET, SOCK_STREAM)
    result = sock.connect_ex((host, 7183))
    return 7183 if result == 0 else 7180


def get_api_connection_params(module):
    host_a = module.params.get('host', None)
    api_a = module.params.get('api_version', 9)
    api_params = {}
    api_params['server_host'] = host_a
    api_params['server_port'] = determine_api_protocol(host_a)
    api_params['use_tls'] = api_params['server_port'] == 7183
    api_params['version'] = api_a
    return api_params


def get_api(module, username=None, password=None, raise_exception=True):
    username_a = username if username is not None else module.params.get('api_username', 'admin')
    password_a = password if password is not None else module.params.get('api_password', 'admin')
    api_params = get_api_connection_params(module)
    api_params['username'] = username_a
    api_params['password'] = password_a
    return validate_api(module, ApiResource(**api_params), raise_exception)


def validate_api(module, api, raise_exception=True):
    try:
        api.get_all_clusters()
        return api
    except Exception as exception:
        if raise_exception:
            module.fail_json(msg="Unable to open connection to the cloudera manager api", exception=str(exception))
        return None


def check_required_params(module, params):
    param_map = {}
    for param in params:
        value = module.params.get(param, None)
        if value is None:
            module.fail_json(msg="Param {0} is required for this action, but not defined".format(param))
        param_map[param] = value
    return param_map


def api_put_request(api, path, params=None, data=None, contenttype="application/json"):
    data_parsed = dumps(data)
    return api.put(path, params=params, data=data_parsed, contenttype=contenttype)


def api_post_request(api, path, params=None, data=None, contenttype="application/json"):
    data_parsed = dumps(data)
    return api.post(path, params=params, data=data_parsed, contenttype=contenttype)


def api_delete_request(api, path, params=None):
    return api.delete(path, params=params)


def api_get_request(api, path, params=None):
    return api.get(path, params=params)


def find_action(name):
    current_module = modules[__name__]
    functions = [current_module.__dict__.get(a) for a in dir(current_module) if isinstance(current_module.__dict__.get(a), FunctionType)]
    actions = [a for a in functions if a.func_name == 'action_{0}'.format(name) and a.func_code.co_argcount == 1]

    if len(actions) == 0:
        return None

    return actions[0]


def action_create_user(module):
    api = get_api(module)
    params = check_required_params(module, ['username', 'password', 'roles'])
    changed = False

    if params['roles'] == []:
        module.fail_json(msg='Variable roles can not be empty')

    users = [user for user in api.get_all_users() if user.name == params['username']]

    if len(users) == 0:
        changed = True
        try:
            user = api.create_user(**params)
        except Exception as exception:
            module.fail_json(msg='Unable to create user with name {0}'.format(params['username']), exception=str(exception))

    user = api.get_user(params['username'])

    if user.roles != params['roles']:
        changed = True
        try:
            api_put_request(api, 'users/{0}'.format(params['username']), data={'roles': params['roles']})
        except Exception as exception:
            module.fail_json(msg="Unable to override user {0} roles".format(params['username']), exception=str(exception))

    test_api = get_api(module, params['username'], params['password'], False)

    if test_api is None:
        changed = True
        try:
            api_put_request(api, 'users/{0}'.format(params['username']), data={'password': params['password']})
        except Exception as exception:
            module.fail_json(msg="Unable to override user {0} password".format(params['username']), exception=str(exception))

        test_api = get_api(module, params['username'], params['password'], False)
        if test_api is None:
            module.fail_json(msg="Unknown exception after changing password for user {0}".format(params['username']))

    module.exit_json(msg="User {0} successfully updated".format(params['username']), changed=changed, username=params['username'])


def action_update_admin_password(module):
    params = check_required_params(module, ['password'])
    test_api = get_api(module, 'admin', params['password'], False)

    if test_api is None:
        api = get_api(module)
        try:
            api_put_request(api, 'users/admin', data={'password': params['password']})
        except Exception as exception:
            module.fail_json(msg="Unable to override admin password", exception=exception)

        test_api = get_api(module, 'admin', params['password'], False)
        if test_api is None:
            module.fail_json(msg="Unknown exception after changing password for user admin")

        module.exit_json(msg="Password for admin updated", changed=True)
    module.exit_json(msg="Password for admin did not change", changed=False)


def main():
    module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

    action = find_action(module.params.get('action'))

    if action is None:
        module.fail_json(msg="Unable to find specified action", action=module.params.get('action'))

    action(module)

    module.fail_json(msg="Action did not finish with exit state", action=module.params.get('action'))

if __name__ == '__main__':
    main()
