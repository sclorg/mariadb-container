MariaDB SQL Database Server Docker Image
========================================

MariaDB 10.3 Quay.io status: [![Docker Repository on Quay](https://quay.io/repository/centos7/mariadb-103-centos7/status "Docker Repository on Quay")](https://quay.io/repository/centos7/mariadb-103-centos7)

This repository contains Dockerfiles for MariaDB images for OpenShift and general usage.
Users can choose between RHEL, Fedora and CentOS based images.

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

RHEL versions currently supported are:
* RHEL7
* RHEL8

CentOS versions currently supported are:
* CentOS7


Installation
----------------------
Choose either the CentOS7 or RHEL7 based image:

*  **RHEL7 based image**

    These images are available in the [Red Hat Container Catalog](https://access.redhat.com/containers/#/registry.access.redhat.com/rhscl/mariadb-103-rhel7).
    To download it run:

    ```
    $ podman pull registry.access.redhat.com/rhscl/mariadb-103-rhel7
    ```

    To build a RHEL7 based MariaDB image, you need to run Docker build on a properly
    subscribed RHEL machine.

    ```
    $ git clone --recursive https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ git submodule update --init
    $ make build TARGET=rhel7 VERSIONS=10.3
    ```

*  **CentOS7 based image**

    This image is available on DockerHub. To download it run:

    ```
    $ podman pull quay.io/centos7/mariadb-103-centos7
    ```

    To build a CentOS based MariaDB image from scratch, run:

    ```
    $ git clone --recursive https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ git submodule update --init
    $ make build TARGET=centos7 VERSIONS=10.3
    ```

For using other versions of MariaDB, just replace the `10.3` value by particular version
in the commands above.

Note: while the installation steps are calling `podman`, you can replace any such calls by `docker` with the same arguments.

**Notice: By omitting the `VERSIONS` parameter, the build/test action will be performed
on all provided versions of MariaDB, which must be specified in  `VERSIONS` variable.
This variable must be set to a list with possible versions (subdirectories).**


Usage
---------------------------------

For information about usage of Dockerfile for MariaDB 10.3,
see [usage documentation](10.3).

Test
---------------------------------

This repository also provides a test framework, which checks basic functionality
of the MariaDB image.

Users can choose between testing MariaDB based on a RHEL or CentOS image.

*  **RHEL based image**

    To test a RHEL7 based MariaDB image, you need to run the test on a properly
    subscribed RHEL machine.

    ```
    $ cd mariadb-container
    $ git submodule update --init
    $ make test TARGET=rhel7 VERSIONS=10.3
    ```

*  **CentOS based image**

    ```
    $ cd mariadb-container
    $ git submodule update --init
    $ make test TARGET=centos7 VERSIONS=10.3
    ```

For using other versions of MariaDB, just replace the `10.3` value by particular version
in the commands above.

**Notice: By omitting the `VERSIONS` parameter, the build/test action will be performed
on all provided versions of MariaDB, which must be specified in  `VERSIONS` variable.
This variable must be set to a list with possible versions (subdirectories).**
