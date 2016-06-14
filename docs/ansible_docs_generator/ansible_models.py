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

import yaml
from abc import abstractmethod, ABCMeta


class Playbook:
    # Playbook is a list od plays. As play you can understand:
    #  SimplePlay
    #  IncludedPlaybook

    def __init__(self, playbook_filename):
        self._plays = []
        with open(playbook_filename, 'r') as playbook_stream:
            playbook_yaml = yaml.load_all(playbook_stream)
            for playbook in playbook_yaml:
                for play in playbook:
                    if 'include' in play:
                        self._plays.append(IncludedPlaybook(play['include']))
                    else:
                        hosts = play['hosts']
                        roles = play['roles']
                        for role in roles:
                            self._plays.append(SimplePlay(hosts, role))

    def get_plays(self):
        return self._plays


class Play:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_role(self):
        pass

    @abstractmethod
    def get_main_filename(self):
        pass


class SimplePlay:
    #  SimplePlay -
    # group of host and group of roles to be deployed on that group

    error_msg = \
        'Role "{}" is of type "{}" while only "str" and "dict" are supported'

    def __init__(self, hosts, role):
        self._hosts = hosts.split(' ') if type(hosts) is str else hosts
        if type(role) is str:
            self._role = role
        elif type(role) is dict:
            self._role = role['role']
        else:
            raise Exception(error_msg.format(role, type(role)))

    def get_hosts(self):
        return self._hosts

    def get_role(self):
        return self._role

    def get_main_filename(self):
        return '../roles/' + self._role + '/tasks/main.yml'


class IncludedPlaybook(Play):
    # IncludedPlaybook -
    # sometimes, playbooks includes another playbooks (composition)

    def __init__(self, playbook_name):
        self._playbook_name = playbook_name

    def get_playbook_name(self):
        return self._playbook_name

    def get_role(self):
        return self._playbook_name

    def get_main_filename(self):
        return '../' + self._playbook_name
