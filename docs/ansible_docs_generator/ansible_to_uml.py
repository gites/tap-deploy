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

from ansible_models import IncludedPlaybook


def generate_plant_uml(playbook, inventory, diagram_order):
    plant_uml_content = []

    plant_uml_content.append('@startuml')
    plant_uml_content.append('')
    plant_uml_content.extend(
        _participants_to_puml(inventory, diagram_order))
    plant_uml_content.append('')
    plant_uml_content.extend(
        _playbook_to_puml(playbook, inventory, diagram_order))
    plant_uml_content.append('')
    plant_uml_content.append('@enduml')
    return plant_uml_content


def _participants_to_puml(inventory, diagram_order):
    participants = map(
        lambda host: HostOrder(_sanitize_hostname(host),
                               diagram_order[host.get_name()]),
        inventory.get_hosts())
    participants.sort(key=lambda ho: ho.get_order())
    return map(lambda p: 'participant ' + p.get_hostname(), participants)


def _playbook_to_puml(playbook, inventory, diagram_order):
    plant_uml_content = []
    colors = ['#fbfb77', '#e8e806']
    for i, play in enumerate(playbook.get_plays()):
        color = colors[i % 2]  # choose light and  color alternately
        content, hostlist = \
            _play_to_puml(inventory, diagram_order, play, color)
        plant_uml_content.extend(content)
        plant_uml_content.extend(_hostslist_to_commented_puml(hostlist))
        plant_uml_content.append('')
    return plant_uml_content


def _play_to_puml(inventory, diagram_order, play, color):
    if isinstance(play, IncludedPlaybook):
        content, hostlist = \
            _included_playbook_to_puml(diagram_order, play)
    else:
        content, hostlist = \
            _simple_play_to_puml(inventory, diagram_order, play, color)
    return content, hostlist


def _included_playbook_to_puml(diagram_order, play):
    hosts = map(
        lambda (host, order): HostOrder(_sanitize_hostname(host), order),
        diagram_order.items())
    hosts.sort(key=lambda ho: ho.get_order())
    first_host_name = hosts[0].get_hostname()
    last_host_name = hosts[-1].get_hostname()

    # show included playbook as big box (from first to last host horizontally,
    # 3 lines vertically) with different color
    role = '\\n' + play.get_role() + '\\n'
    plant_uml_content = []
    plant_uml_content.append('\'EXTERNAL PLAYBOOK - '
                             'shows as something that run on all hosts')
    plant_uml_content.append('note over {}, {} #ef9030 : {}'
                             .format(first_host_name, last_host_name, role))

    return plant_uml_content, hosts


def _simple_play_to_puml(inventory, diagram_order, play, color):
    sorted_hostOrder_list = \
        _sorted_hosts_from_play(inventory, diagram_order, play)

    groups = []
    current_group = ConsecutiveHostsGroup(play.get_role())
    previous_index = None
    group_start_index = None
    group_end_index = None

    # iterate all hosts and split into groups if indexes are not consecutive
    # separate groups wll be visible on the diagram as separate blocks
    for ho in sorted_hostOrder_list:
        index = ho.get_order()
        if previous_index is None or previous_index + 1 == index:
            current_group.add_host(ho.get_hostname())
        else:
            groups.append(current_group)
            current_group = ConsecutiveHostsGroup(play.get_role())
            current_group.add_host(ho.get_hostname())
        previous_index = index
    groups.append(current_group)

    plant_uml_content = map(
        lambda group: _consecutive_hosts_to_puml(group, color), groups)
    return plant_uml_content, sorted_hostOrder_list


def _sorted_hosts_from_play(inventory, diagram_order, play):
    role = play.get_role()
    hostlist = []
    for host_group in play.get_hosts():
        hostlist.extend(map(
            lambda host: HostOrder(_sanitize_hostname(host),
                                   diagram_order[host.get_name()]),
            inventory.get_hosts(host_group)))
    hostlist.sort(key=lambda ho: ho.get_order())
    return hostlist


def _sanitize_hostname(host):
    # plantUML does not like dashes
    return str(host).replace('-', '_')


def _consecutive_hosts_to_puml(group, color):
    role = group.get_role()
    if len(group.get_hosts()) == 1:
        return 'note over {} {} : {}'.format(group.get_hosts()[0], color, role)
    else:
        return 'note over {}, {} {} : {}'\
            .format(group.get_hosts()[0], group.get_hosts()[-1], color, role)


def _hostslist_to_commented_puml(notes):
    plant_uml_content = []
    plant_uml_content.append('\'WHOLE LIST:')
    for note in notes:
        plant_uml_content.append('\'' + note.get_hostname())
    return plant_uml_content


class ConsecutiveHostsGroup:
    def __init__(self, role):
        self._role = role
        self._hosts = []

    def get_role(self):
        return self._role

    def get_hosts(self):
        return self._hosts

    def add_host(self, host):
        self._hosts.append(host)


class HostOrder:
    def __init__(self, host, order):
        self._hostname = host
        self._order = order

    def get_hostname(self):
        return self._hostname

    def get_order(self):
        return self._order
