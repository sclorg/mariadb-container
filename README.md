MariaDB SQL Database Server Docker Image
========================================

[![Build and push images to Quay.io registry](https://github.com/sclorg/mariadb-container/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/sclorg/mariadb-container/actions/workflows/build-and-push.yml)

Images available on Quay are:
* CentOS Stream 9 [mariadb-105](https://quay.io/repository/sclorg/mariadb-105-c9s)
* CentOS Stream 9 [mariadb-1011](https://quay.io/repository/sclorg/mariadb-1011-c9s)
* CentOS Stream 10 [mariadb-1011](https://quay.io/repository/sclorg/mariadb-1011-c10s)
* Fedora [mariadb-1011](https://quay.io/repository/fedora/mariadb-1011)
* Fedora [mariadb-118](https://quay.io/repository/fedora/mariadb-118)

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
* RHEL10

CentOS Stream versions currently supported are:
* CentOS Stream 9
* CentOS Stream 10


Installation
----------------------
Choose either the CentOS Stream or RHEL based image:

*  **RHEL based image**

    These images are available in the [Red Hat Container Catalog](https://catalog.redhat.com/en/search?searchType=containers).
    To download it, run:

    ```
    $ podman pull registry.redhat.io/rhel10/mariadb-1011
    ```

    To build a RHEL10 based MariaDB image, you need to run Docker build on a properly
    subscribed RHEL machine.

    ```
    $ git clone --recursive https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ git submodule update --init
    $ make build TARGET=rhel10 VERSIONS=10.11
    ```

* **CentOS Stream based image**

    This image is available on [Quay.io](https://quay.io/search).
    To download it, run:

    ```
    $ podman pull quay.io/sclorg/mariadb-1011-c10s
    ```

    To build a CentOS Stream based MariaDB image from scratch, run:

    ```
    $ git clone --recursive https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ git submodule update --init
    $ make build TARGET=c10s VERSIONS=10.11
    ```

For using other versions of MariaDB, just replace the `10.11` value with a particular version
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

Testing
---------------------------------

This repository also provides a test framework, which checks basic functionality
of the MariaDB image.

Users can choose between testing MariaDB based on a RHEL or CentOS Stream image.

*  **RHEL based image**

    To test a RHEL10 based MariaDB image, you need to run the test on a properly
    subscribed RHEL machine.

    ```
    $ git clone --recursive https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ git submodule update --init
    $ make test TARGET=rhel10 VERSIONS=10.11
    ```

*  **CentOS Stream based image**

    ```
    $ git clone --recursive https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ git submodule update --init
    $ make test TARGET=c10s VERSIONS=10.11
    ```
    
For using other versions of MariaDB, just replace the `10.11` value with a particular version
in the commands above.

**Notice: By omitting the `VERSIONS` parameter, the build/test action will be performed
on all provided versions of MariaDB, which must be specified in  `VERSIONS` variable.
This variable must be set to a list with possible versions (subdirectories).**
