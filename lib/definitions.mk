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

SHELL:=/bin/bash

command=python $(venv)/bin/ansible-playbook -i $(inventory) $(directory)/$(type).yml $(if $(TEST),--check,) $(if $(DEBUG),-$(DEBUG),) $(if $(PRIVILEGED),-b,) $(if $(config_file),--extra-vars '@$(config_file)',) $(if $(pass_file),--extra-vars '@$(pass_file)',) 2>&1 | tee $(log_file)-$(type).log; exit $${PIPESTATUS[0]}

config_file=$(if $(CONFIG),$(CONFIG),$(directory)/tap.config)
pass_file=$(if $(SECRETS),$(SECRETS),$(directory)/tap.config.secrets)
log_file=$(if $(LOG_FILE),$(LOG_FILE),$(directory)/logs/tap-deploy-$(date))

directory=$(CURDIR)

date=$(shell date +"%Y%m%d-%H%M%S")

venv:=$(directory)/python-ansible

prepare: envs logs

logs:
	mkdir logs

envs:
	$(info Generating envs)
	$(eval export ANSIBLE_SSH_CONTROL_PATH='%(directory)s/%%h-%%r')
	$(eval export ANSIBLE_HOST_KEY_CHECKING=False)
	$(eval export PYTHONPATH=$PYTHONPATH:$(venv)/lib/python2.7/site-packages)
