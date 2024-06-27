#!/bin/bash
#
# Functions for tests for the MariaDB image in OpenShift.
#
# IMAGE_NAME specifies a name of the candidate image used for testing.
# The image has to be available before this script is executed.
#

THISDIR=$(dirname ${BASH_SOURCE[0]})

source "${THISDIR}/test-lib.sh"
source "${THISDIR}/test-lib-openshift.sh"
source "${THISDIR}/test-lib-remote-openshift.sh"

function check_mysql_os_service_connection() {
  local util_image_name="${1}" ; shift
  local service_name="${1}" ; shift
  local user="${1}" ; shift
  local pass="${1}" ; shift
  local timeout="${1:-60}" ; shift || :
  local pod_ip=$(ct_os_get_service_ip ${service_name})

  : "  Service ${service_name} check ..."

  local cmd="echo 'SELECT 42 as testval\g' | mysql --connect-timeout=15 -h ${pod_ip} -u${user} -p${pass}"
  local expected_value='^42'
  local output
  local ret
  SECONDS=0

  echo -n "Waiting for ${service_name} service becoming ready ..."
  while true ; do
    output=$(docker run --rm ${util_image_name} bash -c "${cmd}" || :)
    echo "${output}" | grep -qe "${expected_value}" && ret=0 || ret=1
    if [ ${ret} -eq 0 ] ; then
      echo " PASS"
      return 0
    fi
    echo -n "."
    [ ${SECONDS} -gt ${timeout} ] && break
    sleep 3
  done
  echo " FAIL"
  return 1
}

function test_mysql_pure_image() {
  local image_name=${1:-quay.io/sclorg/mariadb-105-c9s}
  local image_name_no_namespace=${image_name##*/}
  local service_name="${image_name_no_namespace%%:*}-testing"

  ct_os_new_project
  # Create a specific imagestream tag for the image so that oc cannot use anything else
  ct_os_upload_image "v3" "${image_name}" "$image_name_no_namespace"

  ct_os_deploy_pure_image "$image_name_no_namespace" \
                          --name "${service_name}" \
                          --env MYSQL_ROOT_PASSWORD=test

  ct_os_wait_pod_ready "${service_name}" 60
  check_mysql_os_service_connection "${image_name}" "${service_name}" root test

  ct_os_delete_project
}

function test_mysql_template() {
  local image_name=${1:-quay.io/sclorg/mariadb-105-c9s}
  local image_name_no_namespace=${image_name##*/}
  local service_name="${image_name_no_namespace%%:*}-testing"

  ct_os_new_project
  ct_os_upload_image "v3" "${image_name}" "mariadb:$VERSION"

  ct_os_deploy_template_image ${THISDIR}/mariadb-ephemeral-template.json \
                              NAMESPACE="$(oc project -q)" \
                              MARIADB_VERSION="$VERSION" \
                              DATABASE_SERVICE_NAME="${service_name}" \
                              MYSQL_USER=testu \
                              MYSQL_PASSWORD=testp \
                              MYSQL_DATABASE=testdb

  ct_os_wait_pod_ready "${service_name}" 60
  check_mysql_os_service_connection "${image_name}" "${service_name}" testu testp

  ct_os_delete_project
}

function test_mysql_s2i() {
  local image_name=${1:-quay.io/sclorg/mariadb-105-c9s}
  local app=${2:-https://github.com/sclorg/mariadb-container.git}
  local context_dir=${3:-test/test-app}
  local image_name_no_namespace=${image_name##*/}
  local service_name="${image_name_no_namespace%%:*}-testing"

  ct_os_new_project
  # Create a specific imagestream tag for the image so that oc cannot use anything else
  ct_os_upload_image "v3" "${image_name}" "$image_name_no_namespace"

  ct_os_deploy_s2i_image "$image_name_no_namespace" "${app}" \
                          --context-dir="${context_dir}" \
                          --name "${service_name}" \
                          --env MYSQL_ROOT_PASSWORD=test \
                          --env MYSQL_OPERATIONS_USER=testo \
                          --env MYSQL_OPERATIONS_PASSWORD=testo \
                          --env MYSQL_DATABASE=testopdb \
                          --env MYSQL_USER=testnormal \
                          --env MYSQL_PASSWORD=testnormal

  ct_os_wait_pod_ready "${service_name}" 60
  check_mysql_os_service_connection "${image_name}" "${service_name}" testo testo 120

  ct_os_delete_project
}

function test_mariadb_integration() {
  local service_name=mariadb
  TEMPLATES="mariadb-ephemeral-template.json
  mariadb-persistent-template.json"
  SHORT_VERSION="${VERSION//.}"
  namespace_image="${OS}/mariadb-${SHORT_VERSION}"
  # Check if the current version is already GA
  # This directory is cloned from TMT plan repo 'sclorg-tmt-plans'
  local devel_file="/root/sclorg-tmt-plans/devel_images"
  if [ -f "${devel_file}" ]; then
    if grep -q "${OS}=mariadb-container=${VERSION}" "$devel_file" ; then
      echo "This version is currently developed, so skipping this test."
      return
    fi
  fi
  for template in $TEMPLATES; do
    ct_os_test_template_app_func "${IMAGE_NAME}" \
                                 "${THISDIR}/${template}" \
                                 "${service_name}" \
                                 "ct_os_check_cmd_internal 'registry.redhat.io/${namespace_image}' '${service_name}-testing' \"echo 'SELECT 42 as testval\g' | mysql --connect-timeout=15 -h <IP> testdb -utestu -ptestp\" '^42' 120" \
                                 "-p MARIADB_VERSION=${VERSION} \
                                  -p DATABASE_SERVICE_NAME="${service_name}-testing" \
                                  -p MYSQL_USER=testu \
                                  -p MYSQL_PASSWORD=testp \
                                  -p MYSQL_DATABASE=testdb"
  done
}

# Check the imagestream
function test_mariadb_imagestream() {
  local tag="-el8"
  if [ "${OS}" == "rhel9" ]; then
    tag="-el9"
  fi
  # Check if the current version is already GA
  # This directory is cloned from TMT plan repo 'sclorg-tmt-plans'
  local devel_file="/root/sclorg-tmt-plans/devel_images"
  if [ -f "${devel_file}" ]; then
    if grep -q "${OS}=mariadb-container=${VERSION}" "$devel_file" ; then
      echo "This version is currently developed, so skipping this test."
      return
    fi
  fi
  TEMPLATES="mariadb-ephemeral-template.json
  mariadb-persistent-template.json"
  for template in $TEMPLATES; do
    ct_os_test_image_stream_template "${THISDIR}/imagestreams/mariadb-${OS%[0-9]*}.json" "${THISDIR}/examples/${template}" mariadb "-p MARIADB_VERSION=${VERSION}${tag}"
  done
}

function test_mariadb_template() {
  # Check if the current version is already GA
  # This directory is cloned from TMT plan repo 'sclorg-tmt-plans'
  local devel_file="/root/sclorg-tmt-plans/devel_images"
  if [ -f "${devel_file}" ]; then
    if grep -q "${OS}=mariadb-container=${VERSION}" "$devel_file" ; then
      echo "This version is currently developed, so skipping this test."
      return
    fi
  fi
  TEMPLATES="mariadb-ephemeral-template.json
  mariadb-persistent-template.json"
  for template in $TEMPLATES; do
    ct_os_test_image_stream_template "${THISDIR}/imagestreams/mariadb-${OS%[0-9]*}.json" "${THISDIR}/examples/${template}" mariadb
  done
}


# Check the latest imagestreams
function run_latest_imagestreams() {
  # Check if the current version is already GA
  # This directory is cloned from TMT plan repo 'sclorg-tmt-plans'
  local devel_file="/root/sclorg-tmt-plans/devel_images"
  if [ -f "${devel_file}" ]; then
    if grep -q "${OS}=mariadb-container=${VERSION}" "$devel_file" ; then
      echo "This version is currently developed, so skipping this test."
      return
    fi
  fi
  local result=1
  # Switch to root directory of a container
  echo "Testing the latest version in imagestreams"
  pushd "${THISDIR}/../.." >/dev/null || return 1
  ct_check_latest_imagestreams
  result=$?
  popd >/dev/null || return 1
  return $result
}
# vim: set tabstop=2:shiftwidth=2:expandtab:
