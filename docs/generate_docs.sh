#!/bin/bash

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

set -e

PLANTUML_URL="http://sourceforge.net/projects/plantuml/files/plantuml.8047.jar/download"
PLANTUML="plantuml.jar"
PLAYBOOK="../site.yml"
APPS_PLAYBOOK="../apps.yml"

GENERATE_PUML_PY=./ansible_docs_generator/generate_puml.py
GENERATE_HTML_PY=./ansible_docs_generator/generate_html.py

INPUT_DIR="input/"
DIAGRAM_ORDER=$INPUT_DIR"diagram_order"
INVENTORY=$INPUT_DIR"inventory_sample"
HTML_TEMPLATE=$INPUT_DIR"docs.html.template"

OUTPUT_DIR="output/"
PUML=$OUTPUT_DIR"docs.puml"
SVG=$OUTPUT_DIR"docs.svg"
HTML=$OUTPUT_DIR"docs.html"
APPS_PUML=$OUTPUT_DIR"apps_docs.puml"
APPS_SVG=$OUTPUT_DIR"apps_docs.svg"
APPS_HTML=$OUTPUT_DIR"apps_docs.html"

mkdir $OUTPUT_DIR -p


wget $PLANTUML_URL -O $PLANTUML


virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

echo " >>>>> generate puml <<<<<";  python $GENERATE_PUML_PY $INVENTORY $PLAYBOOK $DIAGRAM_ORDER $PUML;  echo " ok!"
echo " >>>>> generate png  <<<<<";  java -jar $PLANTUML $PUML;                                           echo " ok!"
echo " >>>>> generate svg  <<<<<";  java -jar $PLANTUML $PUML -tsvg;                                     echo " ok!"
echo " >>>>> generate html <<<<<";  python $GENERATE_HTML_PY $PLAYBOOK $SVG $HTML_TEMPLATE $HTML;        echo " ok!"

echo " >>>>> generate apps puml <<<<<";  python $GENERATE_PUML_PY $INVENTORY $APPS_PLAYBOOK $DIAGRAM_ORDER $APPS_PUML;  echo " ok!"
echo " >>>>> generate apps png  <<<<<";  java -jar $PLANTUML $APPS_PUML;                                                echo " ok!"
echo " >>>>> generate apps svg  <<<<<";  java -jar $PLANTUML $APPS_PUML -tsvg;                                          echo " ok!"
echo " >>>>> generate apps html <<<<<";  python $GENERATE_HTML_PY $APPS_PLAYBOOK $APPS_SVG $HTML_TEMPLATE $APPS_HTML;   echo " ok!"

deactivate

