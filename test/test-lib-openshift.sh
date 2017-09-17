# Set of functions for testing docker images in OpenShift using 'oc' command

# ct_os_get_status
# --------------------
# Returns status of all objects to make debugging easier.
function ct_os_get_status() {
  oc get all
  oc status
}

# ct_get_public_ip
# --------------------
# Returns best guess for the IP that the node is accessible from other computers.
# This is a bit funny heuristic, simply goes through all IPv4 addresses that
# hostname -I returns and de-prioritizes IP addresses commonly used for local
# addressing. The rest of addresses are taken as public with higher probability.
function ct_get_public_ip() {
  local hostnames=$(hostname -I)
  local public_ip=''
  local found_ip
  for guess_exp in '127\.0\.0\.1' '192\.168\.[0-9\.]*' '172\.[0-9\.]*' \
                   '10\.[0-9\.]*' '[0-9\.]*' ; do
    found_ip=$(echo "${hostnames}" | grep -oe "${guess_exp}")
    if [ -n "${found_ip}" ] ; then
      hostnames=$(echo "${hostnames}" | sed -e "s/${found_ip}//")
      public_ip="${found_ip}"
    fi
  done
  if [ -z "${public_ip}" ] ; then
    echo "ERROR: public IP could not be guessed."
    return 1
  fi
  echo "${public_ip}"
}

# ct_os_run_in_pod [pod_prefix, cmd]
# --------------------
# Runs [cmd] in the pod specified by prefix [pod_prefix].
# Arguments: pod_prefix - prefix or whole ID of the pod to run the cmd in
# Arguments: cmd - command to be run in the pod
function ct_os_run_in_pod() {
  : # TODO
}

# ct_os_get_service_ip [service_name]
# --------------------
# Returns IP of the service specified by [service_name].
# Arguments: service_name - name of the service
function ct_os_get_service_ip() {
  local service_name="${1}" ; shift
  oc get "svc/${service_name}" -o yaml | grep clusterIP | \
     cut -d':' -f2 | grep -oe '172\.30\.[0-9\.]*'
}


# ct_os_get_all_pods_status
# --------------------
# Returns status of all pods.
function ct_os_get_all_pods_status() {
  oc get pods -o custom-columns=NAME:.metadata.name,Ready:status.containerStatuses[0].ready
}

# ct_os_get_pod_status [pod_prefix]
# --------------------
# Returns status of the pod specified by prefix [pod_prefix].
# Arguments: pod_prefix - prefix or whole ID of the pod
function ct_os_get_pod_status() {
  local pod_prefix="${1}" ; shift
  ct_os_get_all_pods_status | grep -e "^${pod_prefix}" | awk '{print $2}' \
                            | head -n 1
}

# ct_os_check_pod_readiness [pod_prefix, status]
# --------------------
# Checks whether the pod is ready.
# Arguments: pod_prefix - prefix or whole ID of the pod
# Arguments: status - expected status (true, false)
function ct_os_check_pod_readiness() {
  local pod_prefix="${1}" ; shift
  local status="${1}" ; shift
  test "$(ct_os_get_pod_status ${pod_prefix})" == "${status}"
}

# ct_os_wait_pod_ready [pod_prefix, timeout]
# --------------------
# Wait maximum [timeout] for the pod becomming ready.
# Arguments: pod_prefix - prefix or whole ID of the pod
# Arguments: timeout - how many seconds to wait seconds
function ct_os_wait_pod_ready() {
  local pod_prefix="${1}" ; shift
  local timeout="${1}" ; shift
  SECONDS=0
  echo -n "Waiting for ${pod_prefix} pod becoming ready ..."
  while ! ct_os_check_pod_readiness "${pod_prefix}" "true" ; do
    echo -n "."
    [ ${SECONDS} -gt ${timeout} ] && echo " FAIL" && return 1
    sleep 3
  done
  echo " DONE"
}

# ct_os_deploy_pure_image [image, env_params, ...]
# --------------------
# Runs [image] in the openshift and optionally specifies env_params
# as environment variables to the image.
# Arguments: image - prefix or whole ID of the pod to run the cmd in
# Arguments: env_params - environment variables parameters for the images.
function ct_os_deploy_pure_image() {
  local image="${1}" ; shift
  # ignore error exit code, because oc new-app returns error when image exists
  oc new-app ${image} $@ || :
  # let openshift cluster to sync to avoid some race condition errors
  sleep 3
}

# ct_os_deploy_s2i_image [image, app, env_params, ...]
# --------------------
# Runs [image] and [app] in the openshift and optionally specifies env_params
# as environment variables to the image.
# Arguments: image - prefix or whole ID of the pod to run the cmd in
# Arguments: app - url repo to the application, local files don't work,
#                  because OpenShift cluster doesn't see the local files
# Arguments: env_params - environment variables parameters for the images.
function ct_os_deploy_s2i_image() {
  local image="${1}" ; shift
  local app="${1}" ; shift
  # ignore error exit code, because oc new-app returns error when image exists
  oc new-app ${image}~${app} $@ || :
  # let openshift cluster to sync to avoid some race condition errors
  sleep 3
}

# ct_os_deploy_template_image [template, env_params]
# --------------------
# Runs template in the openshift and optionally gives env_params to use
# specific values in the template.
# Arguments: template - prefix or whole ID of the pod to run the cmd in
# Arguments: env_params - environment variables parameters for the template.
# Example usage: ct_os_deploy_template_image mariadb-ephemeral-template.yaml \
#                                            DATABASE_SERVICE_NAME=mysql-57-centos7 \
#                                            DATABASE_IMAGE=mysql-57-centos7 \
#                                            MYSQL_USER=testu \
#                                            MYSQL_PASSWORD=testp \
#                                            MYSQL_DATABASE=testdb
function ct_os_deploy_template_image() {
  local template="${1}" ; shift
  oc process -f "${template}" $@ | oc create -f -
  # let openshift cluster to sync to avoid some race condition errors
  sleep 3
}

# _ct_os_get_uniq_project_name
# --------------------
# Returns a uniq name of the OpenShift project.
function _ct_os_get_uniq_project_name() {
  local r
  while true ; do
    r=${RANDOM}
    mkdir /var/tmp/os-test-${r} &>/dev/null && echo test-${r} && break
  done
}

# ct_os_new_project [project]
# --------------------
# Creates a new project in the openshfit using 'os' command.
# Arguments: project - project name, uses a new random name if omitted
# Expects 'os' command that is properly logged in to the OpenShift cluster.
# Not using mktemp, because we cannot use uppercase characters.
function ct_os_new_project() {
  local project_name="${1:-$(_ct_os_get_uniq_project_name)}" ; shift || :
  oc new-project ${project_name}
  # let openshift cluster to sync to avoid some race condition errors
  sleep 3
}

# ct_os_delete_project [project]
# --------------------
# Deletes the specified project in the openshfit
# Arguments: project - project name, uses the current project if omitted
function ct_os_delete_project() {
  local project_name="${1:-$(oc project -q)}" ; shift || :
  oc delete project "${project_name}"
}

# ct_os_docker_login
# --------------------
# Logs in into docker daemon
function ct_os_docker_login() {
  # docker login fails with "404 page not found" error sometimes, just try it more times
  for i in `seq 6` ; do
    docker login -u developer -p $(oc whoami -t) 172.30.1.1:5000 && return 0 || :
    sleep 5
  done
  return 1
}

# ct_os_upload_image [image]
# --------------------
# Uploads image from local registry to the OpenShift internal registry.
# Arguments: image - image name to upload
function ct_os_upload_image() {
  local input_name="${1}" ; shift
  local image_name=${input_name##*/}
  local output_name="172.30.1.1:5000/$(oc project -q)/${image_name}"

  ct_os_docker_login
  docker tag ${input_name} ${output_name}
  docker push ${output_name}
}

# ct_os_install_in_centos
# --------------------
# Installs os cluster in CentOS
function ct_os_install_in_centos() {
  yum install -y centos-release-openshift-origin
  yum install -y wget git net-tools bind-utils iptables-services bridge-utils\
                 bash-completion origin-clients docker origin-clients
}

# ct_os_cluster_up [dir, is_public]
# --------------------
# Runs the local OpenShift cluster using 'oc cluster up' and logs in as developer.
# Arguments: dir - directory to keep configuration data in, random if omitted
# Arguments: is_public - sets either private or public hostname for web-UI,
#                        use "true" for allow remote access to the web-UI,
#                        "false" is default
function ct_os_cluster_up() {
  ct_os_cluster_running && echo "Cluster already running. Nothing is done." && return 0
  mkdir -p /var/tmp/openshift
  local dir="${1:-$(mktemp -d /var/tmp/openshift/os-data-XXXXXX)}" ; shift || :
  local is_public="${1:-'false'}" ; shift || :
  if ! grep -qe '--insecure-registry.*172\.30\.0\.0' /etc/sysconfig/docker ; then
    sed -i '/OPTIONS=.*/c\OPTIONS="--selinux-enabled --insecure-registry 172.30.0.0/16"' /etc/sysconfig/docker
  fi
  systemctl restart docker

  systemctl stop firewalld
  setenforce 0

  local cluster_ip="127.0.0.1"
  [ "${is_public}" == "true" ] && cluster_ip=$(ct_get_public_ip)

  mkdir -p ${dir}/{config,data}
  oc cluster up --host-data-dir=${dir}/data --host-config-dir=${dir}/config \
                --use-existing-config --public-hostname=${cluster_ip}
  oc version
  oc login -u system:admin
  oc login -u developer -p developer
  # let openshift cluster to sync to avoid some race condition errors
  sleep 3
}

# ct_os_cluster_down
# --------------------
# Shuts down the local OpenShift cluster using 'oc cluster down'
function ct_os_cluster_down() {
  oc cluster down
}

# ct_os_cluster_running
# --------------------
# Returns 0 if oc cluster is running
function ct_os_cluster_running() {
  oc status &>/dev/null
}


