MariaDB Docker image
====================

This container image includes MariaDB server 10.1 for OpenShift and general usage.
Users can choose between RHEL and CentOS based images.

Dockerfile for CentOS is called Dockerfile, Dockerfile for RHEL is called
Dockerfile.rhel7.

Environment variables and volumes
----------------------------------

The image recognizes the following environment variables that you can set during
initialization by passing `-e VAR=VALUE` to the Docker run command.

|    Variable name       |    Description                            |
| :--------------------- | ----------------------------------------- |
|  `MYSQL_USER`          | User name for MySQL account to be created |
|  `MYSQL_PASSWORD`      | Password for the user account             |
|  `MYSQL_DATABASE`      | Database name                             |
|  `MYSQL_ROOT_PASSWORD` | Password for the root user (optional)     |

The following environment variables influence the MySQL configuration file. They are all optional.

|    Variable name                |    Description                                                    |    Default
| :------------------------------ | ----------------------------------------------------------------- | -------------------------------
|  `MYSQL_LOWER_CASE_TABLE_NAMES` | Sets how the table names are stored and compared                  |  0
|  `MYSQL_MAX_CONNECTIONS`        | The maximum permitted number of simultaneous client connections   |  151
|  `MYSQL_MAX_ALLOWED_PACKET`     | The maximum size of one packet or any generated/intermediate string | 200M
|  `MYSQL_FT_MIN_WORD_LEN`        | The minimum length of the word to be included in a FULLTEXT index |  4
|  `MYSQL_FT_MAX_WORD_LEN`        | The maximum length of the word to be included in a FULLTEXT index |  20
|  `MYSQL_AIO`                    | Controls the `innodb_use_native_aio` setting value in case the native AIO is broken. See http://help.directadmin.com/item.php?id=529 |  1
|  `MYSQL_TABLE_OPEN_CACHE`       | The number of open tables for all threads                         |  400
|  `MYSQL_KEY_BUFFER_SIZE`        | The size of the buffer used for index blocks                      |  32M (or 10% of available memory)
|  `MYSQL_SORT_BUFFER_SIZE`       | The size of the buffer used for sorting                           |  256K
|  `MYSQL_READ_BUFFER_SIZE`       | The size of the buffer used for a sequential scan                 |  8M (or 5% of available memory)
|  `MYSQL_INNODB_BUFFER_POOL_SIZE`| The size of the buffer pool where InnoDB caches table and index data |  32M (or 50% of available memory)
|  `MYSQL_INNODB_LOG_FILE_SIZE`   | The size of each log file in a log group                          |  8M (or 15% of available available)
|  `MYSQL_INNODB_LOG_BUFFER_SIZE` | The size of the buffer that InnoDB uses to write to the log files on disk | 8M (or 15% of available memory)
|  `MYSQL_DEFAULTS_FILE`          | Point to an alternative configuration file                        |  /etc/my.cnf
|  `MYSQL_BINLOG_FORMAT`          | Set sets the binlog format, supported values are `row` and `statement` | statement

You can also set the following mount points by passing the `-v /host:/container` flag to Docker.

|  Volume mount point      | Description          |
| :----------------------- | -------------------- |
|  `/var/lib/mysql/data`   | MySQL data directory |

**Notice: When mouting a directory from the host into the container, ensure that the mounted
directory has the appropriate permissions and that the owner and group of the directory
matches the user UID or name which is running inside the container.**

Usage
---------------------------------

For this, we will assume that you are using the `rhscl/mariadb-100-rhel7` image.
If you want to set only the mandatory environment variables and not store
the database in a host directory, execute the following command:

```
$ docker run -d --name mariadb_database -e MYSQL_USER=user -e MYSQL_PASSWORD=pass -e MYSQL_DATABASE=db -p 3306:3306 rhscl/mariadb-100-rhel7
```

This will create a container named `mariadb_database` running MySQL with database
`db` and user with credentials `user:pass`. Port 3306 will be exposed and mapped
to the host. If you want your database to be persistent across container executions,
also add a `-v /host/db/path:/var/lib/mysql/data` argument. This will be the MySQL
data directory.

If the database directory is not initialized, the entrypoint script will first
run [`mysql_install_db`](https://dev.mysql.com/doc/refman/5.6/en/mysql-install-db.html)
and setup necessary database users and passwords. After the database is initialized,
or if it was already present, `mysqld` is executed and will run as PID 1. You can
 stop the detached container by running `docker stop mariadb_database`.


MariaDB auto-tuning
-------------------

When the MySQL image is run with the `--memory` parameter set and you didn't
specify value for some parameters, their values will be automatically
calculated based on the available memory.

| Variable name                   | Configuration parameter   | Relative value
| :-------------------------------| ------------------------- | --------------
| `MYSQL_KEY_BUFFER_SIZE`         | `key_buffer_size`         | 10%
| `MYSQL_READ_BUFFER_SIZE`        | `read_buffer_size`        | 5%
| `MYSQL_INNODB_BUFFER_POOL_SIZE` | `innodb_buffer_pool_size` | 50%
| `MYSQL_INNODB_LOG_FILE_SIZE`    | `innodb_log_file_size`    | 15%
| `MYSQL_INNODB_LOG_BUFFER_SIZE`  | `innodb_log_buffer_size`  | 15%


MySQL root user
---------------------------------
The root user has no password set by default, only allowing local connections.
You can set it by setting the `MYSQL_ROOT_PASSWORD` environment variable. This
will allow you to login to the root account remotely. Local connections will
still not require a password.

To disable remote root access, simply unset `MYSQL_ROOT_PASSWORD` and restart
the container.


Changing passwords
------------------

Since passwords are part of the image configuration, the only supported method
to change passwords for the database user (`MYSQL_USER`) and root user is by
changing the environment variables `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD`,
respectively.

Changing database passwords through SQL statements or any way other than through
the environment variables aforementioned will cause a mismatch between the
values stored in the variables and the actual passwords. Whenever a database
container starts it will reset the passwords to the values stored in the
environment variables.


Default my.cnf file
-------------------
With environment variables we are able to customize a lot of different parameters
or configurations for the mysql bootstrap configurations. If you'd prefer to use
your own configuration file, you can override the `MYSQL_DEFAULTS_FILE` env
variable with the full path of the file you wish to use. For example, the default
location is `/etc/my.cnf` but you can change it to `/etc/mysql/my.cnf` by setting
 `MYSQL_DEFAULTS_FILE=/etc/mysql/my.cnf`


Extending image
---------------------------------
This image can be extended using [source-to-image](https://github.com/openshift/source-to-image).

For example to build customized MariaDB database image `my-mariadb-centos7` with configuration in `~/image-configuration/` run:

```
$ s2i build ~/image-configuration/ centos/mariadb-100-centos7 my-mariadb-centos7
```

The directory passed to `s2i build` can contain these directories:
- `mysql-cfg/`
  - when starting the container, files from this directory will be used as a configuration for the `mysqld` daemon
    - `envsubst` command is run on this file to still allow customization of the image using environmental variables

- `mysql-pre-init/`
  - shell scripts (`*.sh`) available in this directory are sourced before `mysqld` daemon is started

- `mysql-init/`
  - shell scripts (`*.sh`) available in this directory are sourced when `mysqld` daemon is started locally
    - in this phase, use `${mysql_flags}` to connect to the locally running daemon, for example `mysql $mysql_flags < dump.sql`

Variables that can be used in the scripts provided to s2i:

- `$mysql_flags` -- arguments for the `mysql` tool that will connect to the locally running `mysqld` during initialization
- `$MYSQL_RUNNING_AS_MASTER` -- variable defined when the container is run with `run-mysqld-master` command
- `$MYSQL_RUNNING_AS_SLAVE` -- variable defined when the container is run with `run-mysqld-slave` command
- `$MYSQL_DATADIR_FIRST_INIT` -- variable defined when the container was initialized from the empty data dir

During `s2i build` all provided files are copied into `/opt/app-root/src` directory into the resulting image. If some configuration files are present in the destination directory, files with the same name are overwritten. Also only one file with the same name can be used for customization and user provided files are preferred over default files in `/usr/share/container-scripts/mysql/`- so it is possible to overwrite them.

Same configuration directory structure can be used to customize the image every time the image is started using `docker run`. The directory has to be mounted into `/opt/app-root/src/` in the image (`-v ./image-configuration/:/opt/app-root/src/`). This overwrites customization built into the image.

It is also possible to use a `Dockerfile` to add the additional files into the new image. This is in particular helpful when we need to change the user for some commands (like installing additional RPMs). A `Dockerfile` that installs an additional RPM and adds a directory `./image-configuration` as s2i source, may look like this:

```
FROM rhscl/mariadb-101-rhel7
USER 0
RUN INSTALL_PKGS="openssh-server" && \
    yum install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    yum clean all
USER 27
COPY image-configuration /opt/app-root/src
```

To build such a Dockerfile, use either appropriate strategy in OpenShift or `docker build` command directly.


Changing the replication binlog_format
--------------------------------------
Some applications may wish to use `row` binlog_formats (for example, those built
  with change-data-capture in mind). The default replication/binlog format is
  `statement` but to change it you can set the `MYSQL_BINLOG_FORMAT` environment
  variable. For example `MYSQL_BINLOG_FORMAT=row`. Now when you run the database
  with `master` replication turned on (ie, set the Docker/container `cmd` to be
`run-mysqld-master`) the binlog will emit the actual data for the rows that change
as opposed to the statements (ie, DML like insert...) that caused the change.
