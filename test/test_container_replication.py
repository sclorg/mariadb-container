import re
from time import sleep

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.engines.database import DatabaseWrapper
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper

from conftest import VARS


class TestMariaDBReplicationContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        """
        Setup the test environment.
        """
        self.replication_db = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.replication_db.set_new_db_type(db_type="mysql")
        self.db_wrapper_api = DatabaseWrapper(image_name=VARS.IMAGE_NAME)

    def teardown_method(self):
        """
        Teardown the test environment.
        """
        self.replication_db.cleanup()

    def test_replication(self):
        """
        Test replication.
        """
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
        # Now wait till the SOURCE will see the REPLICA
        assert self.replication_db.test_db_connection(
            container_ip=master_cip,
            username="root",
            password="root",
        )
        slave_found = False
        for _ in range(3):
            result = self.db_wrapper_api.run_sql_command(
                container_ip=master_cip,
                username="root",
                password="root",
                container_id=master_cid,
                database=VARS.DB_NAME,
                sql_cmd="SHOW SLAVE HOSTS;",
                podman_run_command="exec",
            )
            if not result:
                sleep(3)
                continue
            if slave_cip in result:
                slave_found = True
                break
            sleep(3)
        assert slave_found, (
            f"Replica {slave_cip} not found in MASTER {master_cip} after 3 attempts. See logs for more details. Result: {result}"
        )
        assert self.replication_db.test_db_connection(
            container_ip=slave_cip,
            username="root",
            password="root",
        )
        sql_cmd = "show slave status\\G;"
        mysql_cmd = f'mysql -uroot <<< "{sql_cmd}"'
        print(f"MySQL command: {mysql_cmd}")
        slave_status = PodmanCLIWrapper.call_podman_command(
            cmd=f"exec {slave_cid} bash -c '{mysql_cmd}'",
        )
        words = [
            "Slave_IO_Running:\\s*Yes",
            "Slave_SQL_Running:\\s*Yes",
        ]
        for word in words:
            assert re.search(word, slave_status), (
                f"Word {word} not found in {slave_status}"
            )

        table_output = self.db_wrapper_api.run_sql_command(
            container_ip=master_cip,
            username="root",
            password="root",
            container_id=master_cid,
            database=VARS.DB_NAME,
            sql_cmd="CREATE TABLE t1 (a INT); INSERT INTO t1 VALUES (24);",
            podman_run_command="exec",
        )
        # let's wait for the table to be created and available for replication
        sleep(3)
        table_output = PodmanCLIWrapper.podman_exec_shell_command(
            cid_file_name=slave_cid,
            cmd=f"mysql -uroot <<< 'select * from t1;' {VARS.DB_NAME}",
        )
        assert re.search(r"^a\n^24", table_output.strip(), re.MULTILINE), (
            f"Replica {slave_cip} did not get value from MASTER {master_cip}"
        )
