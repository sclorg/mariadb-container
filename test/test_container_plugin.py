import re

from container_ci_suite.container_lib import ContainerTestLib
from container_ci_suite.container_lib import DatabaseWrapper
from container_ci_suite.engines.podman_wrapper import PodmanCLIWrapper

from conftest import VARS


class TestMariaDBPluginContainer:
    """
    Test MariaDB container configuration.
    """

    def setup_method(self):
        """
        Setup the test environment.
        """
        self.s2i_db = ContainerTestLib(image_name=VARS.IMAGE_NAME)
        self.s2i_db.set_new_db_type(db_type="mysql")
        self.dw_api = DatabaseWrapper(image_name=VARS.IMAGE_NAME)

    def teardown_method(self):
        """
        Teardown the test environment.
        """
        self.s2i_db.cleanup()

    def test_plugin_installation(self):
        """
        Test plugin installation.
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
        self.dw_api.run_sql_command(
            container_ip=cip,
            username="root",
            password="rootpass",
            container_id=VARS.IMAGE_NAME,
            database=VARS.DB_NAME,
            sql_cmd='INSTALL PLUGIN SQL_ERROR_LOG SONAME "sql_errlog" \\G',
        )
        # should fail, deliberately not checking return status
        sql_cmd = "select * from mysql.IdonotExist;"
        self.dw_api.run_sql_command(
            container_ip=cip,
            username="root",
            password="rootpass",
            container_id=VARS.IMAGE_NAME,
            database=VARS.DB_NAME,
            sql_cmd=sql_cmd,
            ignore_error=True,
        )
        output = PodmanCLIWrapper.podman_get_file_content(
            cid_file_name=cid,
            filename="/var/lib/mysql/data/sql_errors.log",
        )
        assert re.search("IdonotExist", output)
