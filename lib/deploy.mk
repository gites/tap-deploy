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

deploy: deploy-platform deploy-apps deploy-marketplace deploy-samples

deploy-platform: deploy-prepare
	$(eval type=platform)
	$(command)

deploy-apps: deploy-prepare
	$(eval type=apps)
	$(command)

deploy-marketplace: deploy-prepare
	$(eval type=marketplace)
	$(command)

deploy-samples: deploy-prepare
	$(eval type=samples)
	$(command)

deploy-prepare: prepare
	$(eval PRIVILEGED=true)
	$(eval inventory=$(HOME)/tap-configuration/tap.inventory.out)
	$(eval CONFIG=$(HOME)/tap-configuration/tap.config)
	$(eval SECRETS=$(HOME)/tap-configuration/tap.config.secrets)
