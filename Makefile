# Variables are documented in hack/build.sh.
BASE_IMAGE_NAME = mariadb
VERSIONS = 10.0 10.1
OPENSHIFT_NAMESPACES = 

# Include common Makefile code.
include hack/common.mk
