import re

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper

from conftest import VARS


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
        cid_file_name = "plugin_install"

        assert self.s2i_db.create_container(
            cid_file_name=cid_file_name,
            container_args=[
                "-e MYSQL_USER=user",
                "-e MYSQL_PASSWORD=foo",
                "-e MYSQL_DATABASE=db",
                "-e MYSQL_ROOT_PASSWORD=rootpass",
            ],
        )
        cip = self.s2i_db.get_cip(cid_file_name=cid_file_name)
        assert cip
        assert self.s2i_db.test_db_connection(
            container_ip=cip, username="root", password="rootpass"
        )
        cid = self.s2i_db.get_cid(cid_file_name=cid_file_name)
        assert cid
        output = self.s2i_db.test_db_connection(
            container_ip=cip,
            username="root",
            password="rootpass",
        )
        assert output, "Database connection should not fail"
        sql_cmd = "INSTALL PLUGIN SQL_ERROR_LOG SONAME 'sql_errlog'"
        podman_cmd = f"run --rm {VARS.IMAGE_NAME} mysql --host {cip} -u root -prootpass"
        output = PodmanCLIWrapper.call_podman_command(
            cmd=f'{podman_cmd} -e "{sql_cmd}  \\G" {VARS.DB_NAME}',
        )
        # should fail, deliberately not checking return status
        PodmanCLIWrapper.call_podman_command(
            cmd=f'{podman_cmd} -e "select * from mysql.IdonotExist;" {VARS.DB_NAME}',
            ignore_error=True,
        )
        output = PodmanCLIWrapper.podman_get_file_content(
            cid_file_name=cid,
            filename="/var/lib/mysql/data/sql_errors.log",
        )
        assert re.search("IdonotExist", output)
