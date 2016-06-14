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

import base64
import zipfile

from os import listdir, path
from os.path import isfile, join
from ansible.module_utils.basic import *

MODULE_ARGUMENTS = ['dir', 'action']


def get_base64_from_file(path):
  files_base_dict = dict.fromkeys(path)
  with open(path, "rb") as content:
    file_name = os.path.basename(path)
    files_base_dict[file_name] = base64.b64encode(content.read())
  return files_base_dict


def get_base64_for_directory(path):
  files = [f for f in listdir(path) if isfile(join(path, f))]
  files_base_dict = dict.fromkeys(file for file in files)
  for file in files:
    with open(join(path, file), "rb") as content:
      files_base_dict[file] = base64.b64encode(content.read())
  return files_base_dict


def get_base64_from_files_in_archive(path):
  files_base_dict = dict()
  with zipfile.ZipFile(path) as zipper:
    for name in zipper.namelist():
      with zipper.open(name) as fp:
        files_base_dict[name] = base64.b64encode(fp.read())
  return files_base_dict


def main():
  module = AnsibleModule(argument_spec=dict((argument, {'type': 'str'}) for argument in MODULE_ARGUMENTS))
  path = module.params.get('dir', None)
  action = module.params.get('action', None)

  if action == 'archive':
    module.exit_json(changed=True, msg='Collected', config=get_base64_from_files_in_archive(path))
  elif action == 'directory':
    module.exit_json(changed=True, msg='Collected', config=get_base64_for_directory(path))
  elif action == 'file':
    module.exit_json(changed=True, msg='Collected', config=get_base64_from_file(path))


main()
