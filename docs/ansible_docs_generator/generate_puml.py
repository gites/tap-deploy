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

import argparse

from ansible_to_uml import generate_plant_uml
from files import save_file_lines
from input_data_loader import load_puml_input_data


def main():
    inventory_filename, playbook_filename, diagram_order_filename, \
        uml_filename = parse_args()
    inventory, playbook, diagram_order = \
        load_puml_input_data(inventory_filename,
                             playbook_filename,
                             diagram_order_filename)
    uml_content = generate_plant_uml(playbook, inventory, diagram_order)
    save_file_lines(uml_content, uml_filename)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", help="Inventory filename.")
    parser.add_argument("playbook", help="Playbook filename.")
    parser.add_argument("diagram_order", help="Diagram order filename.")
    parser.add_argument("puml", help="Puml to be generated filename.")
    args = parser.parse_args()
    return args.inventory, args.playbook, args.diagram_order, args.puml


main()
