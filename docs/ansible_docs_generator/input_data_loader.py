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

from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager

from ansible_models import SimplePlay, Playbook
from files import read_file_lines


def load_puml_input_data(inventory_filename, playbook_filename,
                         diagram_order_filename):
    inventory = _load_inventory(inventory_filename)
    playbook = _load_playbook(playbook_filename)
    _verify_playbook_with_inventory(playbook, inventory)
    diagram_order = _load_diagram_order(diagram_order_filename)
    return inventory, playbook, diagram_order


def load_autodoc_input_data(playbook_filename):
    playbook = _load_playbook(playbook_filename)
    roledocs = _load_roles_documentation(playbook)
    return roledocs


def _load_inventory(inventory_filename):
    loader = DataLoader()
    variable_manager = VariableManager()
    inventory = Inventory(loader=loader,
                          variable_manager=variable_manager,
                          host_list=inventory_filename)
    return inventory


def _load_playbook(playbook_filename):
    return Playbook(playbook_filename)


def _verify_playbook_with_inventory(playbook, inventory):
    group_not_in_inventory_msg = \
        'You defined host or group of hosts "{}" in a playbook, ' \
        'but it is not included in the inventory file.'
    for play in playbook.get_plays():
        if isinstance(play, SimplePlay):
            for host in play.get_hosts():
                if len(inventory.get_hosts(host)) == 0:
                    raise Exception(group_not_in_inventory_msg.format(host))


def _load_diagram_order(diagram_order_filename):
    diagram_order = {}
    index = 0
    for line in read_file_lines(diagram_order_filename):
        if line.startswith('#'):
            continue
        if not line == '':
            diagram_order[line] = index
        index = index + 1
    return diagram_order


def _load_roles_documentation(playbook):
    autodocs = {}
    for play in playbook.get_plays():
        try:
            autodoc_started = False
            role_autodoc_lines = []
            for line in read_file_lines(play.get_main_filename()):
                if _begin_of_autodoc(line):
                    # autodoc starts with '### AUTODOC'
                    autodoc_started = True
                elif autodoc_started:
                    if _end_of_autodoc(line):
                        # autodoc ends with '###'
                        # or with uncommented not empty line
                        break
                    else:
                        role_autodoc_lines.append(line.lstrip('#'))
            autodocs[play.get_role()] = role_autodoc_lines
        except:
            print('WARNING can\' find role: ' + play.get_role())
            pass

    return autodocs


def _end_of_autodoc(line):
    return line.startswith('###') \
           or (line is not '' and not line.startswith('#'))


def _begin_of_autodoc(line):
    return line.startswith('### AUTODOC')
