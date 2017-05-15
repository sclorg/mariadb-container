#!/bin/bash

source ${CONTAINER_SCRIPTS_PATH}/helpers.sh

# Data directory where MySQL database files live. The data subdirectory is here
# because .bashrc and my.cnf both live in /var/lib/mysql/ and we don't want a
# volume to override it.
export MYSQL_DATADIR=/var/lib/mysql/data

# Configuration settings.
export MYSQL_DEFAULTS_FILE=${MYSQL_DEFAULTS_FILE:-/etc/my.cnf}
export MYSQL_BINLOG_FORMAT=${MYSQL_BINLOG_FORMAT:-STATEMENT}
export MYSQL_LOWER_CASE_TABLE_NAMES=${MYSQL_LOWER_CASE_TABLE_NAMES:-0}
export MYSQL_MAX_CONNECTIONS=${MYSQL_MAX_CONNECTIONS:-151}
export MYSQL_FT_MIN_WORD_LEN=${MYSQL_FT_MIN_WORD_LEN:-4}
export MYSQL_FT_MAX_WORD_LEN=${MYSQL_FT_MAX_WORD_LEN:-20}
export MYSQL_AIO=${MYSQL_AIO:-1}
export MYSQL_MAX_ALLOWED_PACKET=${MYSQL_MAX_ALLOWED_PACKET:-200M}
export MYSQL_TABLE_OPEN_CACHE=${MYSQL_TABLE_OPEN_CACHE:-400}
export MYSQL_SORT_BUFFER_SIZE=${MYSQL_SORT_BUFFER_SIZE:-256K}

if [ -n "${NO_MEMORY_LIMIT:-}" -o -z "${MEMORY_LIMIT_IN_BYTES:-}" ]; then
  key_buffer_size='32M'
  read_buffer_size='8M'
  innodb_buffer_pool_size='32M'
  innodb_log_file_size='8M'
  innodb_log_buffer_size='8M'
else
  key_buffer_size="$(python -c "print(int((${MEMORY_LIMIT_IN_BYTES}/(1024*1024))*0.1))")M"
  read_buffer_size="$(python -c "print(int((${MEMORY_LIMIT_IN_BYTES}/(1024*1024))*0.05))")M"
  innodb_buffer_pool_size="$(python -c "print(int((${MEMORY_LIMIT_IN_BYTES}/(1024*1024))*0.5))")M"
  innodb_log_file_size="$(python -c "print(int((${MEMORY_LIMIT_IN_BYTES}/(1024*1024))*0.15))")M"
  innodb_log_buffer_size="$(python -c "print(int((${MEMORY_LIMIT_IN_BYTES}/(1024*1024))*0.15))")M"
fi
export MYSQL_KEY_BUFFER_SIZE=${MYSQL_KEY_BUFFER_SIZE:-$key_buffer_size}
export MYSQL_READ_BUFFER_SIZE=${MYSQL_READ_BUFFER_SIZE:-$read_buffer_size}
export MYSQL_INNODB_BUFFER_POOL_SIZE=${MYSQL_INNODB_BUFFER_POOL_SIZE:-$innodb_buffer_pool_size}
export MYSQL_INNODB_LOG_FILE_SIZE=${MYSQL_INNODB_LOG_FILE_SIZE:-$innodb_log_file_size}
export MYSQL_INNODB_LOG_BUFFER_SIZE=${MYSQL_INNODB_LOG_BUFFER_SIZE:-$innodb_log_buffer_size}

# this stores whether the database was initialized from empty datadir
export MYSQL_DATADIR_FIRST_INIT=false

# Be paranoid and stricter than we should be.
# https://dev.mysql.com/doc/refman/en/identifiers.html
mysql_identifier_regex='^[a-zA-Z0-9_]+$'
mysql_password_regex='^[a-zA-Z0-9_~!@#$%^&*()-=<>,.?;:|]+$'

# Variables that are used to connect to local mysql during initialization
mysql_flags="-u root --socket=/tmp/mysql.sock"
admin_flags="--defaults-file=$MYSQL_DEFAULTS_FILE $mysql_flags"

# Make sure env variables don't propagate to mysqld process.
function unset_env_vars() {
  log_info 'Cleaning up environment variables MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE and MYSQL_ROOT_PASSWORD ...'
  unset MYSQL_USER MYSQL_PASSWORD MYSQL_DATABASE MYSQL_ROOT_PASSWORD
}

# Poll until MySQL responds to our ping.
function wait_for_mysql() {
  pid=$1 ; shift

  while [ true ]; do
    if [ -d "/proc/$pid" ]; then
      mysqladmin --socket=/tmp/mysql.sock ping &>/dev/null && log_info "MySQL started successfully" && return 0
    else
      return 1
    fi
    log_info "Waiting for MySQL to start ..."
    sleep 1
  done
}

# Start local MySQL server with a defaults file
function start_local_mysql() {
  log_info 'Starting MySQL server with disabled networking ...'
  ${MYSQL_PREFIX}/libexec/mysqld \
    --defaults-file=$MYSQL_DEFAULTS_FILE \
    --skip-networking --socket=/tmp/mysql.sock "$@" &
  mysql_pid=$!
  wait_for_mysql $mysql_pid
}

# Shutdown mysql flushing privileges
function shutdown_local_mysql() {
  log_info 'Shutting down MySQL ...'
  mysqladmin $admin_flags flush-privileges shutdown
}

# Initialize the MySQL database (create user accounts and the initial database)
function initialize_database() {
  log_info 'Initializing database ...'
  log_info 'Running mysql_install_db ...'
  # Using --rpm since we need mysql_install_db behaves as in RPM
  # Using empty --basedir to work-around https://bugzilla.redhat.com/show_bug.cgi?id=1406391
  mysql_install_db --rpm --datadir=$MYSQL_DATADIR --basedir=''
  start_local_mysql "$@"

  if [ -v MYSQL_RUNNING_AS_SLAVE ]; then
    log_info 'Initialization finished'
    return 0
  fi

  if [ -v MYSQL_RUNNING_AS_MASTER ]; then
    # Save master status into a separate database.
    STATUS_INFO=$(mysql $admin_flags -e 'SHOW MASTER STATUS\G')
    BINLOG_POSITION=$(echo "$STATUS_INFO" | grep 'Position:' | head -n 1 | sed -e 's/^\s*Position: //')
    BINLOG_FILE=$(echo "$STATUS_INFO" | grep 'File:' | head -n 1 | sed -e 's/^\s*File: //')
    GTID_INFO=$(mysql $admin_flags -e "SELECT BINLOG_GTID_POS('$BINLOG_FILE', '$BINLOG_POSITION') AS gtid_value \G")
    GTID_VALUE=$(echo "$GTID_INFO" | grep 'gtid_value:' | head -n 1 | sed -e 's/^\s*gtid_value: //')

    mysqladmin $admin_flags create replication
    mysql $admin_flags <<EOSQL
    use replication
    CREATE TABLE replication (gtid VARCHAR(256));
    INSERT INTO replication (gtid) VALUES ('$GTID_VALUE');
EOSQL
  fi

  # Do not care what option is compulsory here, just create what is specified
  if [ -v MYSQL_USER ]; then
    log_info "Creating user specified by MYSQL_USER (${MYSQL_USER}) ..."
mysql $mysql_flags <<EOSQL
    CREATE USER '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';
EOSQL
  fi

  if [ -v MYSQL_DATABASE ]; then
    log_info "Creating database ${MYSQL_DATABASE} ..."
    mysqladmin $admin_flags create "${MYSQL_DATABASE}"
    if [ -v MYSQL_USER ]; then
      log_info "Granting privileges to user ${MYSQL_USER} for ${MYSQL_DATABASE} ..."
mysql $mysql_flags <<EOSQL
      GRANT ALL ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'%' ;
      FLUSH PRIVILEGES ;
EOSQL
    fi
  fi

  if [ -v MYSQL_ROOT_PASSWORD ]; then
    log_info "Setting password for MySQL root user ..."
mysql $mysql_flags <<EOSQL
    CREATE USER IF NOT EXISTS 'root'@'%';
    GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}' WITH GRANT OPTION;
EOSQL
  fi
  log_info 'Initialization finished'

  # remember that the database was just initialized, it may be needed on other places
  export MYSQL_DATADIR_FIRST_INIT=true
}

# The 'server_id' number for slave needs to be within 1-4294967295 range.
# This function will take the 'hostname' if the container, hash it and turn it
# into the number.
# See: https://dev.mysql.com/doc/refman/en/replication-options.html#option_mysqld_server-id
function server_id() {
  checksum=$(sha256sum <<< $(hostname -i))
  checksum=${checksum:0:14}
  echo -n $((0x${checksum}%4294967295))
}

function wait_for_mysql_master() {
  while true; do
    log_info "Waiting for MySQL master (${MYSQL_MASTER_SERVICE_NAME}) to accept connections ..."
    mysqladmin --host=${MYSQL_MASTER_SERVICE_NAME} --user="${MYSQL_MASTER_USER}" \
      --password="${MYSQL_MASTER_PASSWORD}" ping &>/dev/null && log_info "MySQL master is ready" && return 0
    sleep 1
  done
}

function get_matched_files() {
  local custom_dir default_dir
  custom_dir="$1"
  default_dir="$2"
  files_matched="$3"
  find "$default_dir" -maxdepth 1 -type f -name "$files_matched" -printf "%f\n"
  [ -d "$custom_dir" ] && find "$custom_dir" -maxdepth 1 -type f -name "$files_matched" -printf "%f\n"
}

# process extending files in $1 and $2 directories
# - source all *.sh files
#   (if there are files with same name source only file from $1)
function process_extending_files() {
  local custom_dir default_dir
  custom_dir=$1
  default_dir=$2

  while read filename ; do
    # Custom file is prefered
    if [ -f $custom_dir/$filename ]; then
      source $custom_dir/$filename
    else
      source $default_dir/$filename
    fi
  done <<<"$(get_matched_files "$custom_dir" "$default_dir" '*.sh' | sort -u)"
}

# process extending config files in $1 and $2 directories
# - expand variables in *.cnf and copy the files into /etc/my.cnf.d directory
#   (if there are files with same name source only file from $1)
function process_extending_config_files() {
  local custom_dir default_dir
  custom_dir=$1
  default_dir=$2

  get_matched_files "$custom_dir" "$default_dir" '*.cnf' | sort -u | while read filename ; do
    # Custom file is prefered
    if [ -f $custom_dir/$filename ]; then
       envsubst < $custom_dir/$filename > /etc/my.cnf.d/$filename
    else
       envsubst < $default_dir/$filename > /etc/my.cnf.d/$filename
    fi
  done
}


