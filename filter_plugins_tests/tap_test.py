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

import unittest

import tap

class TestTapF(unittest.TestCase):

  def test_to_java_format_none(self):
    self.assertEqual(tap.to_java_format(None), '')

  def test_to_java_format(self):
    unix = '.example.com,.cluster.local,localhost'
    java = '*.example.com|*.cluster.local|localhost'
    self.assertEqual(tap.to_java_format(unix), java)

  def test_to_hostname_none(self):
    self.assertEquals(tap.to_hostname(None), '')

  def test_to_hostname(self):
    self.assertEquals(tap.to_hostname('http://proxy.example.com:8080'), 'proxy.example.com')

  def test_to_port_none(self):
    self.assertEquals(tap.to_port(None), '')

  def test_to_port(self):
    self.assertEquals(tap.to_port('http://proxy.example.com:8080'), 8080)

