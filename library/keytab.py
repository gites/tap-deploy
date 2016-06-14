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

#
# recommended pylint: pylint keytab.py -d maybe-no-member,line-too-long --indent-string "  "
# recommended formating: autopep8 --indent-size 2 -i --ignore E501 keytab.py

DOCUMENTATION = ''''''
EXAMPLES = ''''''

from ansible.module_utils.basic import *
from subprocess import PIPE, Popen
from datetime import datetime, timedelta
from re import match
from os import makedirs, remove
from os.path import exists, isdir, join
from base64 import b64encode

# arguments that the module gets in various actions
MODULE_ARGUMENTS = {
    'usr': {'type': 'str', 'required': True},
    'dir': {'type': 'str', 'required': True}
}


def execute(cmd):
  proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
  out, err = proc.communicate()
  proc.wait()
  return out, err, proc.returncode


def restrict_permissions(directory, recursive=False):
  out, err, ret = execute("chown {0} root:root '{1}' && chmod {0} g-rwx,o-rwx '{1}'".format('-R' if recursive else '', directory))
  return ret == 0


def check_keytab(path, user):
  out, err, ret = execute("kinit -k -t '{0}' '{1}'".format(path, user))
  return ret == 0


def generate_keytab(path, user):
  out, err, ret = execute("kadmin.local -q 'xst -norandkey -k \"{0}\" \"{1}\"'".format(path, user))
  return ret == 0


def main():
  module = AnsibleModule(argument_spec=MODULE_ARGUMENTS)

  usr_a = module.params.get('usr', None)
  dir_a = module.params.get('dir', None)
  std, err, ret = execute('kadmin.local -q "listprincs"')

  if ret != 0:
    module.fail_json(msg='You do not have access to kadmin.local')

  usr_norm = usr_a.replace('/', '.').replace('@', '.')

  if not exists(dir_a):
    makedirs(dir_a)
  elif not isdir(dir_a):
    module.fail_json(msg='Param \'dir\' is not a directory')

  if not restrict_permissions(dir_a, True):
    module.fail_json(msg='Unable to change permissions on directory')

  path = join(dir_a, usr_norm)

  renew = True
  if os.path.exists(path):
    # check if keytab is valid
    renew = not check_keytab(path, usr_a)
    if renew:
      remove(path)

  if renew:
    if not generate_keytab(path, usr_a):
      module.fail_json(msg='Unable to create keytab for user {0}'.format(usr_a))

  if not check_keytab(path, usr_a):
    module.fail_json(msg='Keytab {0} for user {1} is wrong'.format(path, usr_a))

  if not restrict_permissions(path):
    module.fail_json(msg='Unable to change permissions on keytab')

  with open(path, "rb") as kt:
    encoded_file = b64encode(kt.read())

  module.exit_json(msg='Keytab generated', principal=usr_a, base64=encoded_file, changed=renew, path=path)

main()
