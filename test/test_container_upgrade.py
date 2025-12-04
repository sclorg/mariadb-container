import re
import tempfile

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.container_lib import ContainerTestLibUtils
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper

from conftest import VARS, get_previous_major_version


class TestMariaDBUpgradeContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        self.s2i_db = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.s2i_db.set_new_db_type(db_type="mysql")

    def teardown_method(self):
        self.s2i_db.cleanup()

    def test_upgrade_test(self):
        """
        Test container creation fails with invalid combinations of arguments.
        """
        mysql_cmd = "run-mysqld"
        cid_testupg1 = "testupg1"
        tmpdir = tempfile.mkdtemp(prefix="/tmp/mariadb-upgrade")
        datadir = f"{tmpdir}/data"
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"mkdir -p {datadir}",
                f"chmod -R a+rwx {tmpdir}",
            ]
        )
        mysql_user = "user"
        mysql_password = "foo"
        mysql_database = "db"
        assert self.s2i_db.create_container(
            cid_file_name=cid_testupg1,
            container_args=[
                f"-e MYSQL_USER={mysql_user}",
                f"-e MYSQL_PASSWORD={mysql_password}",
                f"-e MYSQL_DATABASE={mysql_database}",
                f"-v {datadir}:/var/lib/mysql/data:Z",
            ],
            command=mysql_cmd,
        )
        cip1 = self.s2i_db.get_cip(cid_file_name=cid_testupg1)
        assert cip1
        assert self.s2i_db.test_db_connection(
            container_ip=cip1, username=mysql_user, password=mysql_password
        )
        cid1 = self.s2i_db.get_cid(cid_file_name=cid_testupg1)
        assert cid1
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid1}")

        cid_testupg2 = "testupg2"
        assert self.s2i_db.create_container(
            cid_file_name=cid_testupg2,
            container_args=[
                f"-e MYSQL_USER={mysql_user}",
                f"-e MYSQL_PASSWORD={mysql_password}",
                f"-e MYSQL_DATABASE={mysql_database}",
                f"-v {datadir}:/var/lib/mysql/data:Z",
            ],
            command=mysql_cmd,
        )
        cip2 = self.s2i_db.get_cip(cid_file_name=cid_testupg2)
        assert cip2
        assert self.s2i_db.test_db_connection(
            container_ip=cip2, username=mysql_user, password=mysql_password
        )
        cid2 = self.s2i_db.get_cid(cid_file_name=cid_testupg2)
        assert cid2
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid2}")
        output = PodmanCLIWrapper.podman_logs(
            container_id=cid2,
        )
        assert output, "Version of the data could not be determined"
        assert not re.search("Running mysql_upgrade", output), (
            "mysql_upgrade did not run"
        )

        # Create version file that is too old
        # Testing upgrade from too old data"
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"echo '5.0.12' > {datadir}/mysql_upgrade_info",
            ]
        )

        assert self.s2i_db.assert_container_creation_fails(
            cid_file_name="create_container_fails",
            container_args=[
                f"-e MYSQL_USER={mysql_user}",
                f"-e MYSQL_PASSWORD={mysql_password}",
                f"-e MYSQL_DATABASE={mysql_database}",
                f"-v {datadir}:/var/lib/mysql/data:Z",
                "-e MYSQL_DATADIR_ACTION=upgrade-auto",
            ],
            command=mysql_cmd,
        )

        # Testing upgrade from previous version
        previous_major_version = get_previous_major_version()
        assert previous_major_version
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"echo '{previous_major_version}.12' > {datadir}/mysql_upgrade_info",
            ]
        )
        cid_testupg3 = "testupg3"
        assert self.s2i_db.create_container(
            cid_file_name=cid_testupg3,
            container_args=[
                f"-e MYSQL_USER={mysql_user}",
                f"-e MYSQL_PASSWORD={mysql_password}",
                f"-e MYSQL_DATABASE={mysql_database}",
                f"-v {datadir}:/var/lib/mysql/data:Z",
                "-e MYSQL_DATADIR_ACTION=upgrade-auto",
            ],
            command=mysql_cmd,
        )
        cip3 = self.s2i_db.get_cip(cid_file_name=cid_testupg3)
        assert cip3
        assert self.s2i_db.test_db_connection(
            container_ip=cip3, username=mysql_user, password=mysql_password
        )
        cid3 = self.s2i_db.get_cid(cid_file_name=cid_testupg3)
        assert cid3
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid3}")
        output = PodmanCLIWrapper.podman_logs(
            container_id=cid3,
        )
        print(output)
        assert re.search("Running mysql_upgrade", output), "mysql_upgrade did not run"

        # Testing upgrade from the same version
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"echo '{VARS.VERSION}.12' > {datadir}/mysql_upgrade_info",
            ]
        )
        cid_testupg4 = "testupg4"
        assert self.s2i_db.create_container(
            cid_file_name=cid_testupg4,
            container_args=[
                f"-e MYSQL_USER={mysql_user}",
                f"-e MYSQL_PASSWORD={mysql_password}",
                f"-e MYSQL_DATABASE={mysql_database}",
                f"-v {datadir}:/var/lib/mysql/data:Z",
                "-e MYSQL_DATADIR_ACTION=upgrade-auto",
            ],
            command=mysql_cmd,
        )
        cip4 = self.s2i_db.get_cip(cid_file_name=cid_testupg4)
        assert cip4
        assert self.s2i_db.test_db_connection(
            container_ip=cip4, username=mysql_user, password=mysql_password
        )
        cid4 = self.s2i_db.get_cid(cid_file_name=cid_testupg4)
        assert cid4
        output = PodmanCLIWrapper.podman_logs(
            container_id=cid4,
        )
        print(output)
        assert not re.search("Running mysql_upgrade", output), (
            "Upgrade happened but it should not when upgrading from current version"
        )
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid4}")

        cid_testupg5 = "testupg5analyze"
        assert self.s2i_db.create_container(
            cid_file_name=cid_testupg5,
            container_args=[
                f"-e MYSQL_USER={mysql_user}",
                f"-e MYSQL_PASSWORD={mysql_password}",
                f"-e MYSQL_DATABASE={mysql_database}",
                f"-v {datadir}:/var/lib/mysql/data:Z",
                "-e MYSQL_DATADIR_ACTION=analyze",
            ],
            command=mysql_cmd,
        )
        cip5 = self.s2i_db.get_cip(cid_file_name=cid_testupg5)
        assert cip5
        assert self.s2i_db.test_db_connection(
            container_ip=cip5, username=mysql_user, password=mysql_password
        )
        cid5 = self.s2i_db.get_cid(cid_file_name=cid_testupg5)
        assert cid5
        output = PodmanCLIWrapper.podman_logs(
            container_id=cid5,
        )
        print(output)
        assert re.search(r"--analyze --all-databases", output)
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid5}")

        cid_testupg6 = "testupg6optimize"
        assert self.s2i_db.create_container(
            cid_file_name=cid_testupg6,
            container_args=[
                "-e MYSQL_USER=user",
                "-e MYSQL_PASSWORD=foo",
                "-e MYSQL_DATABASE=db",
                f"-v {datadir}:/var/lib/mysql/data:Z",
                "-e MYSQL_DATADIR_ACTION=optimize",
            ],
            command=mysql_cmd,
        )
        cip6 = self.s2i_db.get_cip(cid_file_name=cid_testupg6)
        assert cip6
        assert self.s2i_db.test_db_connection(
            container_ip=cip6, username="user", password="foo"
        )
        cid6 = self.s2i_db.get_cid(cid_file_name=cid_testupg6)
        assert cid6
        output = PodmanCLIWrapper.podman_logs(
            container_id=cid6,
        )
        assert re.search(r"--optimize --all-databases", output)
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid6}")
