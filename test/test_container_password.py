import tempfile

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.container_lib import ContainerTestLibUtils
from container_ci_suite.container_lib import DatabaseWrapper
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper

from conftest import VARS


class TestMariaDBPasswordContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        """
        Setup the test environment.
        """
        self.pwd_change = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.pwd_change.set_new_db_type(db_type="mariadb")
        self.dw_api = DatabaseWrapper(image_name=VARS.IMAGE_NAME)

    def teardown_method(self):
        """
        Teardown the test environment.
        """
        self.pwd_change.cleanup()

    def get_cip_cid(self, cid_file_name):
        """
        Get the IP and container ID from the cid file name.
        """
        cip = self.pwd_change.get_cip(cid_file_name=cid_file_name)
        assert cip
        cid = self.pwd_change.get_cid(cid_file_name=cid_file_name)
        assert cid
        return cip, cid

    def test_password_change(self):
        """
        Test password change.
        """
        self.pwd_dir_change = tempfile.mkdtemp(prefix="/tmp/mariadb-pwd")
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"chmod -R a+rwx {self.pwd_dir_change}",
            ]
        )

        self.password_change_test(
            username="user", password="foo", pwd_dir=self.pwd_dir_change
        )
        self.password_change_test(
            username="user",
            password="bar",
            pwd_dir=self.pwd_dir_change,
            pwd_change=True,
        )

    def test_password_change_new_user_test(self):
        """
        Test password change for new user.
        """
        self.user_dir_change = tempfile.mkdtemp(prefix="/tmp/mariadb-user")
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"chmod -R a+rwx {self.user_dir_change}",
            ]
        )
        self.password_change_test(
            username="user", password="foo", pwd_dir=self.user_dir_change
        )
        self.password_change_test(
            username="user2",
            password="bar",
            pwd_dir=self.user_dir_change,
            user_change=True,
        )

    def password_change_test(
        self,
        username,
        password,
        pwd_dir,
        user_change: bool = False,
        pwd_change: bool = False,
    ):
        cid_file_name = f"test_{username}_{password}_{user_change}"
        username = username
        password = password

        container_args = [
            f"-e MYSQL_USER={username}",
            f"-e MYSQL_PASSWORD={password}",
            "-e MYSQL_DATABASE=db",
            f"-v {pwd_dir}:/var/lib/mysql/data:Z",
        ]
        assert self.pwd_change.create_container(
            cid_file_name=cid_file_name,
            container_args=container_args,
        )
        cip, cid = self.get_cip_cid(cid_file_name=cid_file_name)
        if user_change:
            username = "user"
            password = "foo"
        assert self.pwd_change.test_db_connection(
            container_ip=cip, username=username, password=password
        )
        if user_change:
            mariadb_logs = PodmanCLIWrapper.podman_logs(
                container_id=cid,
            )
            assert "User user2 does not exist in database" in mariadb_logs
            username = "user"
            password = "bar"
            output = self.dw_api.run_sql_command(
                container_ip=cip,
                username=username,
                password=password,
                container_id=VARS.IMAGE_NAME,
                database=VARS.DB_NAME,
                ignore_error=True,
            )
            assert f"Access denied for user '{username}'@" in output, (
                f"The new password {password} should not work, but it does"
            )
        if pwd_change:
            output = self.dw_api.run_sql_command(
                container_ip=cip,
                username=username,
                password="pwdfoo",
                container_id=VARS.IMAGE_NAME,
                database=VARS.DB_NAME,
                ignore_error=True,
            )
            assert f"Access denied for user '{username}'@" in output, (
                f"The old password {password} should not work, but it does"
            )

        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid}")
