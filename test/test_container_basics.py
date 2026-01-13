import shutil
import tempfile

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.container_lib import ContainerTestLibUtils
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper
from pathlib import Path

from conftest import VARS


def build_s2i_app(app_path: Path) -> ContainerTestLib:
    container_lib = ContainerTestLib(VARS.IMAGE_NAME)
    app_name = app_path.name
    s2i_app = container_lib.build_as_df(
        app_path=app_path,
        s2i_args="--pull-policy=never",
        src_image=VARS.IMAGE_NAME,
        dst_image=f"{VARS.IMAGE_NAME}-{app_name}",
    )
    return s2i_app


class TestMariaDBBasicsContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        """
        Setup the test environment.
        """
        self.app_image = build_s2i_app(app_path=VARS.TEST_DIR / "test-app")
        self.app_image.set_new_db_type(db_type="mariadb")

    def teardown_method(self):
        """
        Teardown the test environment.
        """
        self.app_image.cleanup()

    def test_s2i_usage(self):
        """
        Test if the MariaDB container works properly
        Steps are:
        1. Test if the container creation fails with invalid combinations of arguments
        2. Test if the container creation succeeds with valid combinations of arguments
        3. Test if the database connection works
        """
        cid_config_build = "s2i_usage_build"
        self.app_image.assert_container_creation_fails(
            cid_file_name=cid_config_build,
            command="",
            container_args=[
                "-e MYSQL_USER=root",
                "-e MYSQL_PASSWORD=pass",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=pass",
            ],
        )
        assert self.app_image.create_container(
            cid_file_name=cid_config_build,
            container_args=[
                "-e MYSQL_USER=config_test_user",
                "-e MYSQL_PASSWORD=config_test_user",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_OPERATIONS_USER=operations_user",
                "-e MYSQL_OPERATIONS_PASSWORD=operations_user",
            ],
        )
        cip, cid = self.app_image.get_cip_cid(cid_file_name=cid_config_build)
        assert cip, cid
        assert self.app_image.test_db_connection(
            container_ip=cip, username="operations_user", password="operations_user"
        )
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid}")

    def test_s2i_usage_with_mount(self):
        """
        Test if the MariaDB container works properly with mounted application directory.
        Steps are:
        1. Copy the test-app directory to a temporary directory
        2. Create a container with the mounted application directory
        3. Test if the container creation succeeds with valid combinations of arguments
        4. Test if the database connection works with the operations user
        5. Stop the container
        6. Remove the temporary directory
        """
        data_dir = tempfile.mkdtemp(prefix="/tmp/mariadb-test_data")
        shutil.copytree(VARS.TEST_DIR / "test-app", f"{data_dir}/test-app")
        assert ContainerTestLibUtils.commands_to_run(
            commands_to_run=[
                f"chown -R mysql:mysql {data_dir}/test-app",
            ]
        )
        cid_s2i_test_mount = "s2i_test_mount"
        assert self.app_image.create_container(
            cid_file_name=cid_s2i_test_mount,
            container_args=[
                "-e MYSQL_USER=config_test_user",
                "-e MYSQL_PASSWORD=config_test_user",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_OPERATIONS_USER=operations_user",
                "-e MYSQL_OPERATIONS_PASSWORD=operations_pass",
                f"-v {data_dir}/test-app:/opt/app-root/src/:z",
            ],
        )
        cip, cid = self.app_image.get_cip_cid(cid_file_name=cid_s2i_test_mount)
        assert cip, cid
        assert self.app_image.test_db_connection(
            container_ip=cip,
            username="operations_user",
            password="operations_pass",
            max_attempts=10,
        )
        PodmanCLIWrapper.call_podman_command(cmd=f"stop {cid}")
        shutil.rmtree(data_dir)
