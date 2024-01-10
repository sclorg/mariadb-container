password_change() {
  log_info 'Setting passwords ...'

  # Set the password for MySQL user and root everytime this container is started.
  # This allows to change the password by editing the deployment configuration.
  if [[ -v MYSQL_USER && -v MYSQL_PASSWORD ]]; then
    local user_maches=$(echo "SELECT COUNT(*) AS found FROM mysql.user WHERE user='${MYSQL_USER}' AND Host='%' \G" | mysql $mysql_flags)
    if ! echo "${user_maches}" | grep -q 'found: 1' ; then
      log_info "WARNING: User ${MYSQL_USER} does not exist in database. Password not changed."
    else
mysql $mysql_flags <<EOSQL
      ALTER USER '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';
EOSQL
    fi
  fi

  # The MYSQL_ROOT_PASSWORD is optional, therefore we need to either enable remote
  # access with a password if the variable is set or disable remote access otherwise.
  if [ -v MYSQL_ROOT_PASSWORD ]; then
    # GRANT will create a user if it doesn't exist on 10.0 and lower, but we
    # need to explicitly call CREATE USER in 10.1 and higher
    # then set its password
    if [ "$MYSQL_VERSION" \> "10.0" ] ; then
mysql $mysql_flags <<EOSQL
      CREATE USER IF NOT EXISTS 'root'@'%';
EOSQL
    fi
mysql $mysql_flags <<EOSQL
      GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}' WITH GRANT OPTION;
EOSQL
  else
    if [ "$MYSQL_VERSION" \> "10.0" ] ; then
mysql $mysql_flags <<EOSQL
      DROP USER IF EXISTS 'root'@'%';
      FLUSH PRIVILEGES;
EOSQL
    else
      # In 10.0 and lower, We do GRANT and DROP USER to emulate a DROP USER IF EXISTS statement
      # http://bugs.mysql.com/bug.php?id=19166
mysql $mysql_flags <<EOSQL
      GRANT USAGE ON *.* TO 'root'@'%';
      DROP USER 'root'@'%';
      FLUSH PRIVILEGES;
EOSQL
    fi
  fi
}

if ! [ -v MYSQL_RUNNING_AS_SLAVE ] ; then
  password_change
fi

unset -f password_change

