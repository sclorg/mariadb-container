FROM {{ spec.s2i_base }}{% if spec.s2i_base_tag %}:{{ spec.s2i_base_tag }}{% endif %}


# MariaDB image for OpenShift.
#
# Volumes:
#  * /var/lib/mysql/data - Datastore for MariaDB
# Environment:
#  * $MYSQL_USER - Database user name
#  * $MYSQL_PASSWORD - User's password
#  * $MYSQL_DATABASE - Name of the database to create
#  * $MYSQL_ROOT_PASSWORD (Optional) - Password for the 'root' MySQL account

# Standalone ENV call so these values can be re-used in the other ENV calls
ENV MYSQL_VERSION={{ spec.version }} \
    MYSQL_SHORT_VERSION={{ spec.short }}

ENV VERSION="${MYSQL_VERSION}" \
    APP_DATA=/opt/app-root/src \
    HOME=/var/lib/mysql \
    NAME=mariadb \
    ARCH=x86_64 \
    SUMMARY="MariaDB {{ spec.version }} SQL database server" \
    DESCRIPTION="MariaDB is a multi-user, multi-threaded SQL database server. The container \
    image provides a containerized packaging of the MariaDB mysqld daemon and client application. \
    The mysqld server daemon accepts connections from clients and provides access to content from \
    MariaDB databases on behalf of the clients."

# Standalone ENV call so these values can be re-used in the other ENV calls
LABEL summary="${SUMMARY}" \
      description="${DESCRIPTION}" \
      io.k8s.description="${DESCRIPTION}" \
      io.k8s.display-name="MariaDB {{ spec.version }}" \
      io.openshift.expose-services="3306:mysql" \
      io.openshift.tags="database,mysql,mariadb,mariadb{{ spec.short }},mariadb-{{ spec.short }}" \
      com.redhat.component="{{ spec.com_redhat_component }}" \
      name="{{ spec.img_name }}" \
      com.redhat.license_terms="https://www.redhat.com/en/about/red-hat-end-user-license-agreements#rhel" \
      usage="podman run -d -e MYSQL_USER=user -e MYSQL_PASSWORD=pass -e MYSQL_DATABASE=db -p 3306:3306 {{ spec.full_img_name }}" \
      maintainer="SoftwareCollections.org <sclorg@redhat.com>"

EXPOSE 3306

# This image must forever use UID 27 for mysql user so our volumes are
# safe in the future. This should *never* change, the last test is there
# to make sure of that.
{% if spec.version == "10.3" or (spec.version == "10.5" and spec.prod == "rhel8") or (spec.version in ["10.11", "11.8"] and spec.prod not in ["c10s", "rhel10"]) %}
RUN {{ spec.environment_setup }}
    INSTALL_PKGS="{{ spec.pkgs }} ${NAME}-server" && \
{% elif spec.version == "10.5" and spec.prod == "c9s" %}
RUN dnf -y module disable mariadb && \
    INSTALL_PKGS="{{ spec.pkgs }} ${NAME}-server" && \
{% elif spec.version == "10.5" and spec.prod not in  ["c9s", "rhel8"] %}
RUN INSTALL_PKGS="{{ spec.pkgs }} ${NAME}-server" && \
{% elif spec.version in ["10.11", "11.8"] and spec.prod in ["c10s", "rhel10"] %}
RUN INSTALL_PKGS="{{ spec.pkgs }} ${NAME}${MYSQL_VERSION}-server" && \
{% endif %}
    dnf install -y --setopt=tsflags=nodocs ${INSTALL_PKGS} && \
    /usr/libexec/mysqld -V | grep -qe "${MYSQL_VERSION}\." && echo "Found VERSION ${MYSQL_VERSION}" && \
    dnf -y clean all --enablerepo='*' && \
    mkdir -p ${HOME}/data && chown -R mysql:root ${HOME} && \
    test "$(id mysql)" = "uid=27(mysql) gid=27(mysql) groups=27(mysql)"
# Get prefix path and path to scripts rather than hard-code them in scripts
ENV CONTAINER_SCRIPTS_PATH=/usr/share/container-scripts/mysql \
    MYSQL_PREFIX=/usr

COPY {{ spec.version }}/root-common /
COPY {{ spec.version }}/s2i-common/bin/ $STI_SCRIPTS_PATH
COPY {{ spec.version }}/root /

# Hard links are not supported in Testing Farm approach during sync to guest
# operation system. Therefore tests are failing on error
# /usr/libexec/s2i/run no such file or directory
RUN ln -s /usr/bin/run-mysqld $STI_SCRIPTS_PATH/run

# this is needed due to issues with squash
# when this directory gets rm'd by the container-setup
# script.
# Also reset permissions of filesystem to default values
RUN rm -rf /etc/my.cnf.d/* && \
    /usr/libexec/container-setup && \
    rpm-file-permissions

USER 27

ENTRYPOINT ["container-entrypoint"]
CMD ["run-mysqld"]
