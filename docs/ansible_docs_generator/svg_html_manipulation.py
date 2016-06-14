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

import xml.etree.ElementTree as ET


def fill_svg_with_js_events_on_role_click(input_filename):
    namespace = 'http://www.w3.org/2000/svg'
    tag_prefix = '{' + namespace + '}'
    ET.register_namespace('', namespace)

    tree = ET.parse(input_filename)

    role_polygon = None
    for child in tree.getroot().find(tag_prefix + 'g'):
        # (1/3) look for consecutive polygon / text pair -
        # - it reperesents ansible role in plantUML generated SVG
        if child.tag == tag_prefix + 'polygon':
            role_polygon = child
        elif child.tag == tag_prefix + 'text' \
                and child.text is not None and role_polygon is not None:
            # (2/3) set onmousedown event for polygon / text pair
            _set_click_event_on_role(child, role_polygon)
            # (3/3) reset polygon, start looking for another pair
            role_polygon = None

    return ET.tostring(tree.getroot(), method='xml')


def _set_click_event_on_role(role_text, role_polygon):
    onmousedown_event = "showDocs('" + role_text.text + "')"
    role_polygon.set('onmousedown', onmousedown_event)
    role_text.set('onmousedown', onmousedown_event)


def fill_html_with_svg_content(html_content, svg_content):
    html_and_svg_content = []
    for line in html_content:
        if line == '{{ PASTE_SVG_CONTENT_HERE }}':
            line = svg_content
        html_and_svg_content.append(line)
    return html_and_svg_content


def fill_html_with_roledocs_content(html_content, rolesdocs):
    html_and_roledocs_content = []
    for line in html_content:
        if line == '{{ PASTE_ROLES_DOCUMENTATION_HERE }}':
            line = rolesdocs.__str__()
        html_and_roledocs_content.append(line)
    return html_and_roledocs_content


def prepare_html_roledocs(roledocs):
    new_roledocs = {}
    for rolename, roledoc_lines in roledocs.items():
        html_content = '<h2>' + rolename + '</h2>'
        for line in roledoc_lines:
            html_content = html_content + line + '<br/>'
        new_roledocs[rolename] = html_content
    return new_roledocs
