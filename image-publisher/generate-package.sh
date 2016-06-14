#!/bin/bash -x

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

################################################ FUNCTION DEFINITIONS ##################################################

function clean_docker_images_beside_registry_2 {
	set +x
	$SUDO docker rmi -f $(docker images | grep -vw 'registry\|IMAGE' |  awk '{print $3}') >/dev/null 2>&1
	set -x
}

function clean_all_docker_images {
	set +x
	$SUDO docker rmi -f $(docker images | grep -vw 'IMAGE' |  awk '{print $3}') >/dev/null 2>&1
	set -x
}

function login_to_docker {
	set -e
	$SUDO docker login -u ${TAP_REGISTRY_USER} -p ${TAP_REGISTRY_PASS} https://${TAP_REGISTRY_URL}/v2/
	set +e
}

function start_docker_registry {
	mkdir -p `pwd`/data
	set -e
	$SUDO docker run -d -p ${DISTRIBUTION_PORT}:5000 --name package-registry -v `pwd`/data:/var/lib/registry registry:2
	set +e
	
	REPO_OK=0
	for (( i=0; i<20; i++ )) ; do
		curl -s http://localhost:${DISTRIBUTION_PORT}/v2/ | grep '{}'
		if [ $? -eq 0 ]; then
			echo "ok, repo works."
			REPO_OK=1
			break
		else
			echo "repo is not yet ready..."
			sleep 5
	    fi
	done
	if [ ${REPO_OK} -eq 0 ]; then
	    echo "Repo is not working..."
	    exit 1
	fi
}

function stop_docker_registry {
	$SUDO docker exec package-registry chmod -R 777 /var/lib/registry
	$SUDO docker stop package-registry
	$SUDO docker rm package-registry
}

function pull_image_from_registry {
    set +x
    IMAGE_IDENTIFIER=$1
    $SUDO docker pull ${IMAGE_IDENTIFIER} >/dev/null
    if [ $? -eq 1 ]; then
      echo "No such image $IMAGE_IDENTIFIER"
      exit 1
    fi
    set -x
}

function pull_images_from_images_txt_file {
    while read img; do
        IMAGE_NAME=`echo "$img" | cut -d' ' -f1`
        IMAGE_HOST=`echo "$img" | cut -d' ' -f2`
        if [ "$IMAGE_HOST" == "dockerhub" ]; then
            set -e
            pull_image_from_registry ${IMAGE_NAME}
            $SUDO docker tag ${IMAGE_NAME} localhost:${DISTRIBUTION_PORT}/${IMAGE_NAME}
            set +e
        else
            set -e
            pull_image_from_registry ${IMAGE_HOST}/${IMAGE_NAME}
            $SUDO docker tag ${IMAGE_HOST}/${IMAGE_NAME} localhost:${DISTRIBUTION_PORT}/${IMAGE_NAME}
            set +e
        fi
        set -e
        $SUDO docker push localhost:${DISTRIBUTION_PORT}/${IMAGE_NAME}
        set +e
    done < images.txt
}

function pull_images_from_base_images_txt_file {
    while read img; do
        IMAGE_NAME=`echo "$img" | cut -d' ' -f1`
        IMAGE_HOST=`echo "$img" | cut -d' ' -f2`
        if [ "$IMAGE_HOST" == "dockerhub" ]; then
            set -e
            pull_image_from_registry ${IMAGE_NAME}
            $SUDO docker tag ${IMAGE_NAME} localhost:${DISTRIBUTION_PORT}/${IMAGE_NAME}
            set +e
        else
            set -e
            pull_image_from_registry ${IMAGE_HOST}/${IMAGE_NAME}
            $SUDO docker tag ${IMAGE_HOST}/${IMAGE_NAME} localhost:${DISTRIBUTION_PORT}/${IMAGE_NAME}
            set +e
        fi
        set -e
        $SUDO docker push localhost:${DISTRIBUTION_PORT}/${IMAGE_NAME}
        set +e
    done < base-images.txt
}

function pull_images_from_repos_txt_file {
    while read img; do
        NAME=`echo "$img" | cut -d':' -f1`
        TAG_NUM=`echo "$img" | cut -d':' -f2`

        if [ ${NAME} != ${TAG_NUM} ]; then 
            OVERWRITTEN_VERSION=${TAG_NUM}
        else
            OVERWRITTEN_VERSION=${VERSION}
        fi

        set -e
        pull_image_from_registry ${TAP_REGISTRY_URL}/${NAME}:${OVERWRITTEN_VERSION}

        $SUDO docker tag ${TAP_REGISTRY_URL}/${NAME}:${OVERWRITTEN_VERSION} localhost:${DISTRIBUTION_PORT}/${NAME}:${VERSION}
        $SUDO docker push localhost:${DISTRIBUTION_PORT}/${NAME}:${VERSION}
        
         if [ ${TAG_IMAGES_AS_LATESTS} == 'TAG_IMAGES_AS_LATESTS' ] && [ ${OVERWRITTEN_VERSION} != ${VERSION} ]; then
            $SUDO docker tag ${TAP_REGISTRY_URL}/${NAME}:${OVERWRITTEN_VERSION} ${TAP_REGISTRY_URL}/${NAME}:${VERSION}
            $SUDO docker push ${TAP_REGISTRY_URL}/${NAME}:${VERSION}

            $SUDO docker tag ${TAP_REGISTRY_URL}/${NAME}:${OVERWRITTEN_VERSION} ${TAP_REGISTRY_URL}/${NAME}:latest
            $SUDO docker push ${TAP_REGISTRY_URL}/${NAME}:latest
        fi
        set +e
    done < repos.txt
}

function zip_images_from_mounted_volume {
	set -e	
	tar czf tap-images.tar.gz ./data
	rm -rf ./data
	set +e
}

function get_images_from_mounted_volume {
	set -e	
	mv ./data ../files/$1
	set +e
}

function copy_cached_images_to_tap_storage {
	set -e
	scp -i ${TAP_STORAGE_KEY_FILENAME} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${IMAGES_ZIP_PACKAGE} ${TAP_STORAGE_USER}@${TAP_STORAGE_URL}:/storage/www/tap-releases/dependencies/images-cache
	set +e
}

function prepare_and_upload_cached_images_zip {
	pull_images_from_images_txt_file
	stop_docker_registry
	clean_docker_images_beside_registry_2
	zip_images_from_mounted_volume tap-images
	mv tap-images.tar.gz ${IMAGES_ZIP_PACKAGE}
	copy_cached_images_to_tap_storage
	start_docker_registry
}

################################################ SCRIPT ENTRY POINT ###################################################

########################################## VALIDATION OF GLOBAL VARIABLES #############################################

set +x
set -e
if [ $# -ne 10 ]; then
    echo "Wrong number of input arguments: $#, should be 10

Usage:
$0 <REGISTRY_USER> <REGISTRY_PASS> <REGISTRY_URL> <STORAGE_USER> <STORAGE_PASS> <STORAGE_URL> <STORAGE_KEY_LOCATION> <IMAGE_VERSION> <STRATEGY> <TAG_IMAGES_AS_LATESTS>

STRATEGY valid values:
PREPARE_IMAGES_ZIP_ONLY - Script will pull and zip only images defined in images.txt
PREPARE_TAP_PACKAGE_BASED_ON_EXISTING_IMAGE_ZIP - Script will create full tap package based on images downloaded from remote storage and those pulled from image registry
PREPARE_TAP_PACKAGE_FROM_SCRATCH - Script will pull all neccessary images (iterating through images.txt and repos.txt) and tap package will be created
"

    exit 2
fi
set +e
set -x

TAP_REGISTRY_USER=$1
TAP_REGISTRY_PASS=$2
TAP_REGISTRY_URL=$3

TAP_STORAGE_USER=$4
TAP_STORAGE_PASS=$5
TAP_STORAGE_URL=$6

TAP_STORAGE_KEY_FILENAME=$7
VERSION=$8
STRATEGY=$9
TAG_IMAGES_AS_LATESTS=$10

if [ ! -f ${TAP_STORAGE_KEY_FILENAME} ]; then
	echo "Storage key file doesn't exists: ${TAP_STORAGE_KEY_FILENAME}"
fi

PROJECT_NAME=TAP
DISTRIBUTION_PORT=5001
SUDO=""
IMAGES_TXT_HASH=`md5sum images.txt | cut -d' ' -f1`
IMAGES_ZIP_PACKAGE=tap-fixed-images-${IMAGES_TXT_HASH}.tar.gz


###################################################### EXECUTE LOGIC #################################################

rm -f tap-images-*.tar.gz
stop_docker_registry
login_to_docker
clean_docker_images_beside_registry_2
start_docker_registry

if [ ${STRATEGY} == "PREPARE_IMAGES_ZIP_ONLY" ]; then
	prepare_and_upload_cached_images_zip
	rm ${IMAGES_ZIP_PACKAGE}
	stop_docker_registry
	clean_docker_images_beside_registry_2
fi

if [ ${STRATEGY} == "PREPARE_TAP_PACKAGE_BASED_ON_EXISTING_IMAGE_ZIP" ]; then
	wget -q http://${TAP_STORAGE_USER}:${TAP_STORAGE_PASS}@${TAP_STORAGE_URL}/dependencies/images-cache/${IMAGES_ZIP_PACKAGE}
	if [ $? -ne 0 ]; then
		prepare_and_upload_cached_images_zip
	fi
	set -e
	tar -xf ${IMAGES_ZIP_PACKAGE}
	rm ${IMAGES_ZIP_PACKAGE}
	set +e
	pull_images_from_repos_txt_file
	stop_docker_registry
	clean_docker_images_beside_registry_2
	get_images_from_mounted_volume tap-images
	start_docker_registry
	pull_images_from_base_images_txt_file
	stop_docker_registry
	clean_docker_images_beside_registry_2
	get_images_from_mounted_volume tap-base-images
fi

if [ ${STRATEGY} == "PREPARE_TAP_PACKAGE_FROM_SCRATCH" ]; then
	pull_images_from_images_txt_file &
	pull_images_from_repos_txt_file &
	wait
	stop_docker_registry
	clean_docker_images_beside_registry_2
	get_images_from_mounted_volume tap-images
	start_docker_registry
	pull_images_from_base_images_txt_file
	stop_docker_registry
	clean_docker_images_beside_registry_2
	get_images_from_mounted_volume tap-base-images
fi
