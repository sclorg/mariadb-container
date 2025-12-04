import re

import pytest

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper

from conftest import VARS


class TestMariaDBConfigurationContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        self.db = ContainerTestLib(image_name=VARS.IMAGE_NAME)

    def teardown_method(self):
        self.db.cleanup()

    def test_container_creation_fails(self):
        """
        Test container creation fails with no arguments.
        """
        cid_config_test = "container_creation_fails"
        assert self.db.assert_container_creation_fails(
            cid_file_name=cid_config_test, container_args=[], command=""
        )

    @pytest.mark.parametrize(
        "mysql_user, mysql_password, mysql_database, mysql_root_password",
        [
            ["-e MYSQL_USER=user", "", "-e MYSQL_DATABASE=db", ""],
            ["", "-e MYSQL_PASSWORD=pass", "-e MYSQL_DATABASE=db", ""],
            [
                "-e MYSQL_USER=user",
                "",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=pass",
            ],
            [
                "",
                "-e MYSQL_PASSWORD=pass",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=pass",
            ],
        ],
    )
    def test_try_image_invalid_combinations(
        self, mysql_user, mysql_password, mysql_database, mysql_root_password
    ):
        """
        Test container creation fails with invalid combinations of arguments.
        """
        cid_file_name = "try_image_invalid_combinations"
        assert self.db.assert_container_creation_fails(
            cid_file_name=cid_file_name,
            container_args=[
                mysql_user,
                mysql_password,
                mysql_database,
                mysql_root_password,
            ],
            command="",
        )

    @pytest.mark.parametrize(
        "mysql_user, mysql_password, mysql_database, mysql_root_password, expected_result",
        [
            ("-e MYSQL_USER=user", "-e MYSQL_PASSWORD=pass", "", "", True),
            (
                "-e MYSQL_USER=$invalid",
                "-e MYSQL_PASSWORD=pass",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=root_pass",
                True,
            ),
            # LONG DATABASE NAME returns  invalid reference format
            (
                f"MYSQL_USER={VARS.VERY_LONG_USER_NAME}",
                "-e MYSQL_PASSWORD=pass",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=root_pass",
                False,
            ),
            (
                "-e MYSQL_USER=user",
                "-e MYSQL_PASSWORD=",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=root_pass",
                True,
            ),
            (
                "-e MYSQL_USER=user",
                "-e MYSQL_PASSWORD=pass",
                "-e MYSQL_DATABASE=$invalid",
                "-e MYSQL_ROOT_PASSWORD=root_pass",
                True,
            ),
            # LONG DATABASE NAME returns  invalid reference format
            (
                "-e MYSQL_USER=user",
                "-e MYSQL_PASSWORD=pass",
                f"MYSQL_DATABASE={VARS.VERY_LONG_DB_NAME}",
                "-e MYSQL_ROOT_PASSWORD=root_pass",
                False,
            ),
            (
                "-e MYSQL_USER=user",
                "-e MYSQL_PASSWORD=pass",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=",
                True,
            ),
            (
                "-e MYSQL_USER=root",
                "-e MYSQL_PASSWORD=pass",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=pass",
                True,
            ),
        ],
    )
    def test_invalid_configuration_tests(
        self,
        mysql_user,
        mysql_password,
        mysql_database,
        mysql_root_password,
        expected_result,
    ):
        """
        Test invalid configuration combinations for MySQL container.
        """
        cid_config_test = "invalid_configuration_tests"
        assert (
            self.db.assert_container_creation_fails(
                cid_file_name=cid_config_test,
                container_args=[
                    mysql_user,
                    mysql_password,
                    mysql_database,
                    mysql_root_password,
                ],
                command="",
            )
            == expected_result
        )


class TestMariaDBConfigurationTests:
    """
    Test MariaDB container configuration tests.
    """

    def setup_method(self):
        self.db = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.db.set_new_db_type(db_type="mysql")

    def teardown_method(self):
        self.db.cleanup()

    def test_configuration_auto_calculated_settings(self):
        """
        Test MariaDB container configuration auto-calculated settings.
        """
        cid_config_test = "auto-config_test"
        username = "config_test_user"
        password = "config_test"
        assert self.db.create_container(
            cid_file_name=cid_config_test,
            container_args=[
                "--env MYSQL_COLLATION=latin2_czech_cs",
                "--env MYSQL_CHARSET=latin2",
                f"--env MYSQL_USER={username}",
                f"--env MYSQL_PASSWORD={password}",
                "--env MYSQL_DATABASE=db",
            ],
            docker_args="--memory=256m",
        )
        cip = self.db.get_cip(cid_file_name=cid_config_test)
        assert cip
        return_value = self.db.test_db_connection(
            container_ip=cip,
            username=username,
            password=password,
            max_attempts=10,
            database=VARS.DB_NAME,
        )
        assert return_value
        cid = self.db.get_cid(cid_file_name=cid_config_test)
        db_configuration = PodmanCLIWrapper.podman_exec_shell_command(
            cid_file_name=cid,
            cmd="cat /etc/my.cnf /etc/my.cnf.d/*",
        )
        assert db_configuration
        assert re.search(
            r"key_buffer_size\s*=\s*25M",
            db_configuration,
        )
        assert re.search(
            r"read_buffer_size\s*=\s*12M",
            db_configuration,
        )
        assert re.search(
            r"innodb_log_file_size\s*=\s*38M",
            db_configuration,
        )
        assert re.search(
            r"innodb_log_buffer_size\s*=\s*38M",
            db_configuration,
        )
        # do some real work to test replication in practice
        return_value = self.db.test_db_connection(
            container_ip=cip,
            username=username,
            password=password,
            database=VARS.DB_NAME,
            sql_cmd="-e 'CREATE TABLE tbl (col VARCHAR(20));'",
        )
        print(f"Creating table: {return_value}")
        assert self.db.test_db_connection(
            container_ip=cip,
            username=username,
            password=password,
            sql_cmd="-e 'SHOW CREATE TABLE tbl;'",
            database=VARS.DB_NAME,
        )
        show_table_output = PodmanCLIWrapper.call_podman_command(
            cmd=f"exec {cid} mysql -uroot -e 'SHOW CREATE TABLE tbl;' {VARS.DB_NAME}",
            ignore_error=True,
        )
        assert "CHARSET=latin2" in show_table_output
        assert "COLLATE=latin2_czech_cs" in show_table_output
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid}")

    def test_configuration_options_settings(self):
        """
        Test MariaDB container configuration options.
        """
        cid_config_test = "config_test"
        assert self.db.create_container(
            cid_file_name=cid_config_test,
            container_args=[
                "--env MYSQL_USER=config_test_user",
                "--env MYSQL_PASSWORD=config_test",
                "--env MYSQL_DATABASE=db",
                "--env MYSQL_LOWER_CASE_TABLE_NAMES=1",
                "--env MYSQL_LOG_QUERIES_ENABLED=1",
                "--env MYSQL_MAX_CONNECTIONS=1337",
                "--env MYSQL_FT_MIN_WORD_LEN=8",
                "--env MYSQL_FT_MAX_WORD_LEN=15",
                "--env MYSQL_MAX_ALLOWED_PACKET=10M",
                "--env MYSQL_TABLE_OPEN_CACHE=100",
                "--env MYSQL_SORT_BUFFER_SIZE=256K",
                "--env MYSQL_KEY_BUFFER_SIZE=16M",
                "--env MYSQL_READ_BUFFER_SIZE=16M",
                "--env MYSQL_INNODB_BUFFER_POOL_SIZE=16M",
                "--env MYSQL_INNODB_LOG_FILE_SIZE=4M",
                "--env MYSQL_INNODB_LOG_BUFFER_SIZE=4M",
                "--env WORKAROUND_DOCKER_BUG_14203=",
            ],
        )
        cip = self.db.get_cip(cid_file_name=cid_config_test)
        assert cip
        assert self.db.test_db_connection(
            container_ip=cip,
            username="config_test_user",
            password="config_test",
            database=VARS.DB_NAME,
        )
        cip = self.db.get_cip(cid_file_name=cid_config_test)
        assert cip
        return_value = self.db.test_db_connection(
            container_ip=cip,
            username="config_test_user",
            password="config_test",
            max_attempts=10,
            database=VARS.DB_NAME,
        )
        assert return_value
        cid = self.db.get_cid(cid_file_name=cid_config_test)
        db_configuration = PodmanCLIWrapper.podman_exec_shell_command(
            cid_file_name=cid,
            cmd="cat /etc/my.cnf /etc/my.cnf.d/*",
        )
        assert db_configuration
        assert re.search(
            r"lower_case_table_names\s*=\s*1",
            db_configuration,
        )
        assert re.search(
            r"general_log\s*=\s*1",
            db_configuration,
        )
        assert re.search(
            r"max_connections\s*=\s*1337",
            db_configuration,
            re.MULTILINE | re.IGNORECASE,
        )
        assert re.search(r"ft_min_word_len\s*=\s*8", db_configuration)
        assert re.search(
            r"ft_max_word_len\s*=\s*15",
            db_configuration,
        )
        assert re.search(r"max_allowed_packet\s*=\s*10M", db_configuration)
        assert re.search(r"table_open_cache\s*=\s*100", db_configuration)
        assert re.search(r"sort_buffer_size\s*=\s*256K", db_configuration)
        assert re.search(r"key_buffer_size\s*=\s*16M", db_configuration)
        assert re.search(r"read_buffer_size\s*=\s*16M", db_configuration)
        assert re.search(r"innodb_log_file_size\s*=\s*4M", db_configuration)
        assert re.search(r"innodb_log_buffer_size\s*=\s*4M", db_configuration)
