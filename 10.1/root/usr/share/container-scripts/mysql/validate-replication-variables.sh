function validate_replication_variables() {
  if ! [[ ! -z ${MYSQL_DATABASE+x} && ! -z ${MYSQL_MASTER_USER+x} && ! -z ${MYSQL_MASTER_PASSWORD+x} && \
        ( "${MYSQL_RUNNING_AS_SLAVE:-0}" != "1" || ! -z ${MYSQL_MASTER_SERVICE_NAME+x} ) ]]; then
    echo
    echo "For master/slave replication, you have to specify following environment variables:"
    echo "  MYSQL_MASTER_SERVICE_NAME (slave only)"
    echo "  MYSQL_DATABASE"
    echo "  MYSQL_MASTER_USER"
    echo "  MYSQL_MASTER_PASSWORD"
    echo
  fi
  [[ "$MYSQL_DATABASE" =~ $mysql_identifier_regex ]] || usage "Invalid database name"
  [[ "$MYSQL_MASTER_USER"     =~ $mysql_identifier_regex ]] || usage "Invalid MySQL master username"
  [ ${#MYSQL_MASTER_USER} -le 16 ] || usage "MySQL master username too long (maximum 16 characters)"
  [[ "$MYSQL_MASTER_PASSWORD" =~ $mysql_password_regex   ]] || usage "Invalid MySQL master password"
}

validate_replication_variables
