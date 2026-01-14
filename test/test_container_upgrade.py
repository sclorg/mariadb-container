import re
import tempfile

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.container_lib import ContainerTestLibUtils
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper
import pytest

from conftest import VARS


class TestMariaDBUpgradeContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        """
        Setup the test environment.
        """
        self.s2i_db = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.s2i_db.set_new_db_type(db_type="mariadb")
        self.tmpdir = tempfile.mkdtemp(prefix="/tmp/mariadb-upgrade")
        self.datadir = f"{self.tmpdir}/data"
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"mkdir -p {self.datadir}",
                f"chmod -R a+rwx {self.tmpdir}",
            ]
        )
        self.run_mysqld_cmd = "run-mysqld"

    def teardown_method(self):
        """
        Teardown the test environment.
        """
        self.s2i_db.cleanup()

    @pytest.mark.parametrize(
        "action",
        [
            "",
            "analyze",
            "optimize",
        ],
    )
    def test_upgrade_test(self, action):
        """
        Test container creation fails with invalid combinations of arguments.
        """
        mysql_user = "user"
        mysql_password = "foo"
        mysql_database = "db"
        self.upgrade_db(
            mysql_user=mysql_user, mysql_password=mysql_password, action=action
        )
        output = self.upgrade_db(
            mysql_user=mysql_user, mysql_password=mysql_password, action=action
        )
        assert output, "Version of the data could not be determined"
        assert not re.search("Running mysql_upgrade", output), (
            "mysql_upgrade did not run"
        )

        # Create version file that is too old
        # Testing upgrade from too old data"
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"echo '5.0.12' > {self.datadir}/mysql_upgrade_info",
            ]
        )
        container_args = [
            f"-e MYSQL_USER={mysql_user}",
            f"-e MYSQL_PASSWORD={mysql_password}",
            f"-e MYSQL_DATABASE={mysql_database}",
            f"-v {self.datadir}:/var/lib/mysql/data:Z",
            "-e MYSQL_DATADIR_ACTION=upgrade-auto",
        ]
        assert self.s2i_db.assert_container_creation_fails(
            cid_file_name="create_container_fails",
            container_args=container_args,
            command=self.run_mysqld_cmd,
        )

        # Testing upgrade from previous version
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"echo '{VARS.PREVIOUS_VERSION}.12' > {self.datadir}/mysql_upgrade_info",
            ]
        )
        output = self.upgrade_db(
            mysql_user=mysql_user, mysql_password=mysql_password, action="upgrade-auto"
        )
        assert re.search("Running mysql_upgrade", output), "mysql_upgrade did not run"

        # Testing upgrade from the same version
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"echo '{VARS.VERSION}.12' > {self.datadir}/mysql_upgrade_info",
            ]
        )
        output = self.upgrade_db(
            mysql_user=mysql_user, mysql_password=mysql_password, action="upgrade-auto"
        )
        assert not re.search("Running mysql_upgrade", output), (
            "mysql_upgrade did not run"
        )
        output = self.upgrade_db(
            mysql_user=mysql_user, mysql_password=mysql_password, action="upgrade-auto"
        )
        assert not re.search("Running mysql_upgrade", output), (
            "Upgrade happened but it should not when upgrading from current version"
        )
        output = self.upgrade_db(
            mysql_user=mysql_user, mysql_password=mysql_password, action="analyze"
        )
        assert re.search(r"--analyze --all-databases", output)

        output = self.upgrade_db(
            mysql_user=mysql_user, mysql_password=mysql_password, action="optimize"
        )
        assert re.search(r"--optimize --all-databases", output)

    def upgrade_db(self, mysql_user, mysql_password, action: str = "") -> str:
        """
        Test MariaDB upgrade.
        """
        cid_testupg = f"testupg-{mysql_user}-{mysql_password}"
        container_args = [
            f"-e MYSQL_USER={mysql_user}",
            f"-e MYSQL_PASSWORD={mysql_password}",
            "-e MYSQL_DATABASE=db",
            f"-v {self.datadir}:/var/lib/mysql/data:Z",
        ]
        if action:
            container_args.append(f"-e MYSQL_DATADIR_ACTION={action}")
        assert self.s2i_db.create_container(
            cid_file_name=cid_testupg,
            container_args=container_args,
            command=self.run_mysqld_cmd,
        )
        cip, cid = self.s2i_db.get_cip_cid(cid_file_name=cid_testupg)
        assert cip, cid
        assert self.s2i_db.test_db_connection(
            container_ip=cip, username=mysql_user, password=mysql_password
        )
        output = PodmanCLIWrapper.podman_logs(
            container_id=cid,
        )
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid}")
        return output
