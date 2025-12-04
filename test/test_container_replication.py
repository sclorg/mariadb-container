import re
from time import sleep

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper

from conftest import VARS


class TestMariaDBReplicationContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        self.replication_db = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.replication_db.set_new_db_type(db_type="mysql")

    def teardown_method(self):
        self.replication_db.cleanup()

    def test_replication(self):
        """ """
        cluster_args = "-e MYSQL_MASTER_USER=master -e MYSQL_MASTER_PASSWORD=master -e MYSQL_DATABASE=db"
        master_cid_name = "master.cid"
        username = "user"
        password = "foo"
        # Run the MySQL source
        assert self.replication_db.create_container(
            cid_file_name=master_cid_name,
            container_args=[
                f"-e MYSQL_USER={username}",
                f"-e MYSQL_PASSWORD={password}",
                "-e MYSQL_ROOT_PASSWORD=root",
            ],
            docker_args=cluster_args,
            command="mysqld-master",
        )
        master_cip = self.replication_db.get_cip(cid_file_name=master_cid_name)
        print(f"Master IP: {master_cip}")
        master_cid = self.replication_db.get_cid(cid_file_name=master_cid_name)
        assert master_cid
        # Run the MySQL replica
        slave_cid_name = "slave.cid"
        assert self.replication_db.create_container(
            cid_file_name=slave_cid_name,
            container_args=[
                f"-e MYSQL_MASTER_SERVICE_NAME={master_cip}",
            ],
            docker_args=cluster_args,
            command="mysqld-slave",
        )
        slave_cip = self.replication_db.get_cip(cid_file_name=slave_cid_name)
        assert slave_cip
        slave_cid = self.replication_db.get_cid(cid_file_name=slave_cid_name)
        assert slave_cid
        print(f"Replica IP: {slave_cid}")
        # Now wait till the SOURCE will see the REPLICA
        result = self.replication_db.test_db_connection(
            container_ip=master_cip,
            username="root",
            password="root",
        )
        result = PodmanCLIWrapper.call_podman_command(
            cmd=f"exec {master_cid} mysql -uroot -e 'SHOW SLAVE HOSTS;' db",
            ignore_error=True,
        )
        print(f"Showing replicas: {result}")
        assert slave_cip in result, (
            f"Replica {slave_cip} not found in MASTER {master_cip}"
        )
        mysql_cmd = "mysql -uroot <<< 'show slave status\\G;'"
        slave_status = PodmanCLIWrapper.podman_exec_shell_command(
            cid_file_name=slave_cid,
            cmd=mysql_cmd,
        )
        print(f"Slave status: {slave_status}")
        assert slave_status
        assert re.search(r"Slave_IO_Running:\s*Yes", slave_status), (
            f"Slave {slave_cid} is not running"
        )

        assert re.search(r"Slave_SQL_Running:\s*Yes", slave_status), (
            f"Slave {slave_cid} is not running"
        )
        self.replication_db.test_db_connection(
            container_ip=master_cip,
            username=username,
            password=password,
            max_attempts=120,
            sql_cmd="-e 'CREATE TABLE t1 (a INT); INSERT INTO t1 VALUES (24);'",
        )
        # let's wait for the table to be created and available for replication
        sleep(3)
        table_output = PodmanCLIWrapper.podman_exec_shell_command(
            cid_file_name=slave_cid,
            cmd=f"mysql -uroot <<< 'select * from t1;' {VARS.DB_NAME}",
        )
        print(f"Selecting from table: {table_output}")
        assert re.search(r"^a\n^24", table_output.strip(), re.MULTILINE), (
            f"Replica {slave_cip} did not get value from MASTER {master_cip}"
        )
