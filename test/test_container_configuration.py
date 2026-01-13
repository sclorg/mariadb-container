import re

import pytest

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper
from container_ci_suite.container_lib import DatabaseWrapper

from conftest import VARS


class TestMariaDBConfigurationContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        """
        Setup the test environment.
        """
        self.db = ContainerTestLib(image_name=VARS.IMAGE_NAME)

    def teardown_method(self):
        """
        Teardown the test environment.
        """
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
        """
        Setup the test environment.
        """
        self.db_config = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.db_config.set_new_db_type(db_type="mysql")
        self.db_api = DatabaseWrapper(image_name=VARS.IMAGE_NAME)

    def teardown_method(self):
        """
        Teardown the test environment.
        """
        self.db_config.cleanup()

    def test_configuration_auto_calculated_settings(self):
        """
        Test MariaDB container configuration auto-calculated settings.
        Steps are:
        1. Create a container with the given arguments
        2. Check if the container is created successfully
        3. Check if the database connection works
        4. Check if the database configurations are correct
        5. Stop the container
        """
        cid_config_test = "auto-config_test"
        username = "config_test_user"
        password = "config_test"
        assert self.db_config.create_container(
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
        cip, cid = self.db_config.get_cip_cid(cid_file_name=cid_config_test)
        assert cip, cid
        assert self.db_config.test_db_connection(
            container_ip=cip,
            username=username,
            password=password,
            max_attempts=10,
            database=f"db {VARS.SSL_OPTION}",
        )
        db_configuration = PodmanCLIWrapper.podman_exec_shell_command(
            cid_file_name=cid,
            cmd="cat /etc/my.cnf /etc/my.cnf.d/*",
        )
        words = [
            "key_buffer_size\\s*=\\s*25M",
            "read_buffer_size\\s*=\\s*12M",
            "innodb_log_file_size\\s*=\\s*38M",
            "innodb_log_buffer_size\\s*=\\s*38M",
        ]
        for word in words:
            assert re.search(word, db_configuration), (
                f"Word {word} not found in {db_configuration}"
            )
        # do some real work to test replication in practice
        self.db_api.run_sql_command(
            container_ip=cip,
            username=username,
            password=password,
            container_id=cid,
            database=VARS.DB_NAME,
            sql_cmd="CREATE TABLE tbl (col VARCHAR(20));",
            podman_run_command="exec",
        )
        show_table_output = self.db_api.run_sql_command(
            container_ip=cip,
            username=username,
            password=password,
            container_id=cid,
            database=VARS.DB_NAME,
            sql_cmd="SHOW CREATE TABLE tbl;",
            podman_run_command="exec",
        )
        assert "CHARSET=latin2" in show_table_output
        assert "COLLATE=latin2_czech_cs" in show_table_output
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid}")

    def test_configuration_options_settings(self):
        """
        Test MariaDB container configuration options.
        """
        cid_config_test = "config_test"
        assert self.db_config.create_container(
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
        cip = self.db_config.get_cip(cid_file_name=cid_config_test)
        assert cip
        assert self.db_config.test_db_connection(
            container_ip=cip,
            username="config_test_user",
            password="config_test",
            database=VARS.DB_NAME,
        )
        cip = self.db_config.get_cip(cid_file_name=cid_config_test)
        assert cip
        assert self.db_config.test_db_connection(
            container_ip=cip,
            username="config_test_user",
            password="config_test",
            max_attempts=10,
            database=VARS.DB_NAME,
        )
        cid = self.db_config.get_cid(cid_file_name=cid_config_test)
        db_configuration = PodmanCLIWrapper.podman_exec_shell_command(
            cid_file_name=cid,
            cmd="cat /etc/my.cnf /etc/my.cnf.d/*",
        )
        words = [
            "lower_case_table_names\\s*=\\s*1",
            "general_log\\s*=\\s*1",
            "max_connections\\s*=\\s*1337",
            "ft_min_word_len\\s*=\\s*8",
            "ft_max_word_len\\s*=\\s*15",
            "max_allowed_packet\\s*=\\s*10M",
            "table_open_cache\\s*=\\s*100",
            "sort_buffer_size\\s*=\\s*256K",
            "key_buffer_size\\s*=\\s*16M",
            "read_buffer_size\\s*=\\s*16M",
            "innodb_log_file_size\\s*=\\s*4M",
            "innodb_log_buffer_size\\s*=\\s*4M",
        ]
        for word in words:
            assert re.search(word, db_configuration), (
                f"Word {word} not found in {db_configuration}"
            )
