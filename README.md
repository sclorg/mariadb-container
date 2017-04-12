MariaDB SQL Database Server Docker Image
========================================

This repository contains Dockerfiles for MariaDB images for OpenShift and general usage.
Users can choose between RHEL and CentOS based images.

MariaDB container is very similar to the MySQL container available at
[https://github.com/sclorg/mysql-container](https://github.com/sclorg/mysql-container).

For more information about using these images with OpenShift, please see the
official [OpenShift Documentation](https://docs.openshift.org/latest/using_images/db_images/mysql.html).


Versions
---------------
MariaDB versions currently provided are:
* [mariadb-10.0](10.0)
* [mariadb-10.1](10.1)

RHEL versions currently supported are:
* RHEL7
* RHEL6 (mariadb-10.1 only)

CentOS versions currently supported are:
* CentOS7


Installation
----------------------
Choose either the CentOS7, RHEL6, or RHEL7 based image:

*  **RHEL7 based image**

    This image is available in Red Hat Container Registry. To download it run:

    ```
    $ docker pull registry.access.redhat.com/rhscl/mariadb-101-rhel7
    ```

    To build a RHEL7 based MariaDB image, you need to run Docker build on a properly
    subscribed RHEL machine.

    ```
    $ git clone https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ make build TARGET=rhel7 VERSION=10.1
    ```

*  **RHEL6 based image**

    To build a RHEL6 based MariaDB image, you need to run Docker build on a properly
    subscribed RHEL machine.

    ```
    $ git clone https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ make build TARGET=rhel6 VERSION=10.1
    ```

*  **CentOS7 based image**

    This image is available on DockerHub. To download it run:

    ```
    $ docker pull centos/mariadb-101-centos7
    ```

    To build a CentOS based MariaDB image from scratch, run:

    ```
    $ git clone https://github.com/sclorg/mariadb-container.git
    $ cd mariadb-container
    $ make build TARGET=centos7 VERSION=10.1
    ```

For using other versions of MariaDB, just replace the `10.1` value by particular version
in the commands above.

**Notice: By omitting the `VERSION` parameter, the build/test action will be performed
on all provided versions of MariaDB, which must be specified in  `VERSIONS` variable.
This variable must be set to a list with possible versions (subdirectories).**


Usage
---------------------------------

For information about usage of Dockerfile for MariaDB 10.0,
see [usage documentation](10.0).

For information about usage of Dockerfile for MariaDB 10.1,
see [usage documentation](10.1).


Test
---------------------------------

This repository also provides a test framework, which checks basic functionality
of the MariaDB image.

Users can choose between testing MariaDB based on a RHEL or CentOS image.

*  **RHEL7 based image**

    To test a RHEL7 based MariaDB image, you need to run the test on a properly
    subscribed RHEL machine.

    ```
    $ cd mariadb-container
    $ make test TARGET=rhel7 VERSION=10.1
    ```

*  **RHEL6 based image**

    To test a RHEL6 based MariaDB image, you need to run the test on a properly
    subscribed RHEL machine.

    ```
    $ cd mariadb-container
    $ make test TARGET=rhel6 VERSION=10.1
    ```

*  **CentOS based image**

    ```
    $ cd mariadb-container
    $ make test TARGET=centos7 VERSION=10.1
    ```

For using other versions of MariaDB, just replace the `10.1` value by particular version
in the commands above.

**Notice: By omitting the `VERSION` parameter, the build/test action will be performed
on all provided versions of MariaDB, which must be specified in  `VERSIONS` variable.
This variable must be set to a list with possible versions (subdirectories).**
