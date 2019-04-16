FROM registry.fedoraproject.org/f28/s2i-core:latest

# MariaDB image for OpenShift.
#
# Volumes:
#  * /var/lib/mysql/data - Datastore for MariaDB
# Environment:
#  * $MYSQL_USER - Database user name
#  * $MYSQL_PASSWORD - User's password
#  * $MYSQL_DATABASE - Name of the database to create
#  * $MYSQL_ROOT_PASSWORD (Optional) - Password for the 'root' MySQL account

ENV MYSQL_VERSION=10.2 \
    APP_DATA=/opt/app-root/src \
    HOME=/var/lib/mysql \
    NAME=mariadb \
    VERSION=10.2 \
    ARCH=x86_64 \
    SUMMARY="MariaDB 10.2 SQL database server" \
    DESCRIPTION="MariaDB is a multi-user, multi-threaded SQL database server. The container \
image provides a containerized packaging of the MariaDB mysqld daemon and client application. \
The mysqld server daemon accepts connections from clients and provides access to content from \
MariaDB databases on behalf of the clients."

LABEL summary="$SUMMARY" \
      description="$DESCRIPTION" \
      io.k8s.description="MariaDB is a multi-user, multi-threaded SQL database server" \
      io.k8s.display-name="MariaDB 10.2" \
      io.openshift.expose-services="3306:mysql" \
      io.openshift.tags="database,mysql,mariadb,mariadb102,galera" \
      com.redhat.component="$NAME" \
      name="$FGC/$NAME" \
      version="$VERSION" \
      usage="docker run -d -e MYSQL_USER=user -e MYSQL_PASSWORD=pass -e MYSQL_DATABASE=db -p 3306:3306 $FGC/$NAME" \
      maintainer="SoftwareCollections.org <sclorg@redhat.com>"

EXPOSE 3306

# This image must forever use UID 27 for mysql user so our volumes are
# safe in the future. This should *never* change, the last test is there
# to make sure of that.
RUN INSTALL_PKGS="rsync tar gettext hostname bind-utils groff-base shadow-utils mariadb mariadb-server policycoreutils" && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    dnf clean all && \
    mkdir -p /var/lib/mysql/data && chown -R mysql.0 /var/lib/mysql && \
    test "$(id mysql)" = "uid=27(mysql) gid=27(mysql) groups=27(mysql)"

# Get prefix path and path to scripts rather than hard-code them in scripts
ENV CONTAINER_SCRIPTS_PATH=/usr/share/container-scripts/mysql \
    MYSQL_PREFIX=/usr

COPY 10.2/root-common /
COPY 10.2/s2i-common/bin/ $STI_SCRIPTS_PATH
COPY 10.2/root /

# this is needed due to issues with squash
# when this directory gets rm'd by the container-setup
# script.
# Also reset permissions of filesystem to default values
RUN rm -rf /etc/my.cnf.d/* && \
    /usr/libexec/container-setup && \
    rpm-file-permissions

# Not using VOLUME statement since it's not working in OpenShift Online:
# https://github.com/sclorg/httpd-container/issues/30
# VOLUME ["/var/lib/mysql/data"]

USER 27

ENTRYPOINT ["container-entrypoint"]
CMD ["run-mysqld"]
