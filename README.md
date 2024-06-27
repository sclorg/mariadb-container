MariaDB SQL Database Server Docker Image
========================================

[![Build and push images to Quay.io registry](https://github.com/sclorg/mariadb-container/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/sclorg/mariadb-container/actions/workflows/build-and-push.yml)

Images available on Quay are:
* CentOS Stream 9 [mariadb-105](https://quay.io/repository/sclorg/mariadb-105-c9s)
* CentOS Stream 9 [mariadb-1011](https://quay.io/repository/sclorg/mariadb-1011-c9s)
* Fedora [mariadb-103](https://quay.io/repository/fedora/mariadb-103)
* Fedora [mariadb-105](https://quay.io/repository/fedora/mariadb-105)
* Fedora [mariadb-1011](https://quay.io/repository/fedora/mariadb-1011)

This repository contains Dockerfiles for MariaDB images for OpenShift and general usage.
Users can choose between RHEL, Fedora and CentOS Stream based images.

MariaDB container is very similar to the MySQL container available at
[https://github.com/sclorg/mysql-container](https://github.com/sclorg/mysql-container).

For more information about using these images with OpenShift, please see the
official [OpenShift Documentation](https://docs.okd.io/latest/using_images/db_images/mariadb.html).

For more information about contributing, see
[the Contribution Guidelines](https://github.com/sclorg/welcome/blob/master/contribution.md).
For more information about concepts used in these podman images, see the
[Landing page](https://github.com/sclorg/welcome).


Versions
---------------
MariaDB versions currently provided are:
* [MariaDB 10.3](10.3)
* [MariaDB 10.5](10.5)
* [MariaDB 10.11](10.11)

RHEL versions currently supported are:
* RHEL8
* RHEL9

CentOS versions currently supported are:
* CentOS Stream 9


Installation
----------------------

*  **RHEL8 based image**

    These images are available in the [Red Hat Container Catalog](https://access.redhat.com/containers/#/registry.access.redhat.com/rhel8/mariadb-105).
    To download it run:

    ```
    $ podman pull registry.access.redhat.com/rhel8/mariadb-105
    ```

    To build a RHEL8 based MariaDB image, you need to run Docker build on a properly
    subscribed RHEL machine.

    ```
    $ git clone --recursive https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ git submodule update --init
    $ make build TARGET=rhel8 VERSIONS=10.5
    ```

For using other versions of MariaDB, just replace the `10.5` value by particular version
in the commands above.

Note: while the installation steps are calling `podman`, you can replace any such calls by `docker` with the same arguments.

**Notice: By omitting the `VERSIONS` parameter, the build/test action will be performed
on all provided versions of MariaDB, which must be specified in  `VERSIONS` variable.
This variable must be set to a list with possible versions (subdirectories).**


Usage
---------------------------------

For information about usage of Dockerfile for MariaDB 10.3,
see [usage documentation](10.3).

For information about usage of Dockerfile for MariaDB 10.5,
see [usage documentation](10.5).

For information about usage of Dockerfile for MariaDB 10.11,
see [usage documentation](10.11).

Test
---------------------------------

This repository also provides a test framework, which checks basic functionality
of the MariaDB image.

Users can choose between testing MariaDB based on a RHEL or CentOS image.

*  **RHEL based image**

    To test a RHEL8 based MariaDB image, you need to run the test on a properly
    subscribed RHEL machine.

    ```
    $ cd mariadb-container
    $ git submodule update --init
    $ make test TARGET=rhel8 VERSIONS=10.5
    ```

For using other versions of MariaDB, just replace the `10.5` value by particular version
in the commands above.

**Notice: By omitting the `VERSIONS` parameter, the build/test action will be performed
on all provided versions of MariaDB, which must be specified in  `VERSIONS` variable.
This variable must be set to a list with possible versions (subdirectories).**
