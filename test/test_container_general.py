import re
import pytest
import tempfile

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.container_lib import ContainerTestLibUtils
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper
from container_ci_suite.container_lib import DatabaseWrapper

from conftest import VARS


class TestMariaDBGeneralContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        """
        Setup the test environment.
        """
        self.db_image = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.db_api = DatabaseWrapper(image_name=VARS.IMAGE_NAME)
        self.datadir = tempfile.mkdtemp(prefix="/tmp/mariadb-datadir-actions")
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"mkdir -p {self.datadir}/data",
                f"chmod -R a+rwx {self.datadir}",
            ]
        )

    def teardown_method(self):
        """
        Teardown the test environment.
        """
        self.db_image.cleanup()

    @pytest.mark.parametrize(
        "docker_args, username, password, root_password",
        [
            ("", "user", "pass", ""),
            ("", "user1", "pass1", "r00t"),
            ("--user 12345", "user", "pass", ""),
            ("--user 12345", "user1", "pass1", "r00t"),
        ],
    )
    def test_run(self, docker_args, username, password, root_password):
        """
        Test if the MariaDB container works properly with the different arguments
        like docker_args, username, password, and root_password.
        Steps are:
        1. Create a container with the given arguments
        2. Check if the container is created successfully
        3. Check if the database connection works
        4. Check if mariadb version is correct
        5. Check if the login access works
        6. Check if the local access works
        7. Test the database creation
        """
        root_password_arg = (
            f"-e MYSQL_ROOT_PASSWORD={root_password}" if root_password else ""
        )
        cid_file_name = f"test_{username}_{password}_{root_password}"
        assert self.db_image.create_container(
            cid_file_name=cid_file_name,
            container_args=[
                f"-e MYSQL_USER={username}",
                f"-e MYSQL_PASSWORD={password}",
                "-e MYSQL_DATABASE=db",
                f"{root_password_arg}",
                f"{docker_args}",
            ],
            command="run-mysqld",
        )
        cip, cid = self.db_image.get_cip_cid(cid_file_name=cid_file_name)
        assert cip, cid
        assert self.db_image.test_db_connection(
            container_ip=cip, username=username, password=password
        )
        output = PodmanCLIWrapper.podman_exec_shell_command(
            cid_file_name=cid,
            cmd="mysql --version",
        )
        assert VARS.VERSION in output
        # Define variable for login_access function
        # Let's check if the login access works for all the users and passwords
        # then assert at the end
        # If any of the login access fails, return False
        # If all the login access works, return True
        login_access = True

        for user, pwd, ret_value in [
            (username, password, True),
            (username, f"{password}_foo", False),
            ("root", "foo", False),
            ("root", "", False),
        ]:
            test_assert = self.db_image.db_lib.assert_login_access(
                container_ip=cip,
                username=user,
                password=pwd,
                expected_success=ret_value,
            )
            if not test_assert:
                print(
                    f"Login access failed for {user}:{pwd} with expected success {ret_value}"
                )
                access_output = False
                break
        assert access_output, "Login access failed for above results"
        if root_password:
            root_access_output = True
            for user, pwd, ret_value in [
                ("root", root_password, True),
                ("root", f"{root_password}_foo", False),
            ]:
                test_assert = self.db_image.db_lib.assert_login_access(
                    container_ip=cip,
                    username=user,
                    password=pwd,
                    expected_success=ret_value,
                )
                if not test_assert:
                    print(
                        f"Login access failed for {user}:{pwd} with expected success {ret_value}"
                    )
                    root_access_output = False
                    break
            assert root_access_output, "Login access failed for above results"

        assert self.db_image.db_lib.assert_local_access(container_id=cid)
        self.database_test(cip, username, password)

    def database_test(self, cip, username, password):
        """
        Test MariaDB database creation.
        """
        self.db_api.run_sql_command(
            container_ip=cip,
            username=username,
            password=password,
            container_id=VARS.IMAGE_NAME,
            database=VARS.DB_NAME,
            sql_cmd=[
                "CREATE TABLE tbl (col1 VARCHAR(20), col2 VARCHAR(20));",
            ],
        )
        self.db_api.run_sql_command(
            container_ip=cip,
            username=username,
            password=password,
            container_id=VARS.IMAGE_NAME,
            database=VARS.DB_NAME,
            sql_cmd=[
                'INSERT INTO tbl VALUES ("foo1", "bar1");',
                'INSERT INTO tbl VALUES ("foo2", "bar2");',
                'INSERT INTO tbl VALUES ("foo3", "bar3");',
            ],
        )
        output = self.db_api.run_sql_command(
            container_ip=cip,
            username=username,
            password=password,
            container_id=VARS.IMAGE_NAME,
            database=VARS.DB_NAME,
            sql_cmd="SELECT * FROM tbl;",
        )
        expected_db_output = [
            r"foo1\t*bar1",
            r"foo2\t*bar2",
            r"foo3\t*bar3",
        ]
        for row in expected_db_output:
            assert re.search(row, output), f"Row {row} not found in {output}"
        self.db_api.run_sql_command(
            container_ip=cip,
            username=username,
            password=password,
            container_id=VARS.IMAGE_NAME,
            database=VARS.DB_NAME,
            sql_cmd="DROP TABLE tbl;",
        )

    def test_datadir_actions(self):
        """
        Test container creation fails with invalid combinations of arguments.
        """
        self.datadir_action_test("")
        self.datadir_action_test("analyze")
        self.datadir_action_test("optimize")

    def datadir_action_test(self, action):
        """
        Test MariaDB datadir action.
        """
        mysql_user = "user"
        mysql_password = "foo"
        mysql_database = "db"
        cid_test = f"test_upgrade_{action}"
        assert self.db_image.create_container(
            cid_file_name=cid_test,
            container_args=[
                f"-e MYSQL_USER={mysql_user}",
                f"-e MYSQL_PASSWORD={mysql_password}",
                f"-e MYSQL_DATABASE={mysql_database}",
                f"-v {self.datadir}/data:/var/lib/mysql/data:Z",
            ],
        )
        cip, cid = self.db_image.get_cip_cid(cid_file_name=cid_test)
        assert cip, cid
        assert self.db_image.test_db_connection(
            container_ip=cip, username=mysql_user, password=mysql_password
        )
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid}")
