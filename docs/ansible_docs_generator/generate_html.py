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

from files import read_file_lines, save_file_lines
from input_data_loader import load_autodoc_input_data
from svg_html_manipulation import \
    fill_svg_with_js_events_on_role_click, fill_html_with_svg_content, \
    fill_html_with_roledocs_content, prepare_html_roledocs


def main():
    playbook_filename, svg_filename, html_template_filename, \
        html_output_filename = parse_args()

    roledocs = load_autodoc_input_data(playbook_filename)
    roledocs = prepare_html_roledocs(roledocs)

    html_content = \
        read_file_lines(html_template_filename)
    svg_docs_content = \
        fill_svg_with_js_events_on_role_click(svg_filename)
    html_and_svg_content = \
        fill_html_with_svg_content(html_content, svg_docs_content)
    html_svg_and_roledocs_content = \
        fill_html_with_roledocs_content(html_and_svg_content, roledocs)
    save_file_lines(html_svg_and_roledocs_content, html_output_filename)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("playbook",
                        help="Ansible playbook filename.")
    parser.add_argument("svg",
                        help="Svg generated from uml filename.")
    parser.add_argument("html_input",
                        help="Html documentation template filename.")
    parser.add_argument("html_output",
                        help="Html to be generated (final documentation) "
                             "filename.")
    args = parser.parse_args()
    return args.playbook, args.svg, args.html_input, args.html_output


main()
