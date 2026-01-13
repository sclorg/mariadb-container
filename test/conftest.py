import os
import sys

from pathlib import Path
from collections import namedtuple

from container_ci_suite.utils import check_variables

if not check_variables():
    sys.exit(1)

TAGS = {
    "rhel8": "-el8",
    "rhel9": "-el9",
    "rhel10": "-el10",
}

MARIADB_PREVIOUS_VERSIONS = {
    "10.3": "10.2",
    "10.5": "10.3",
    "10.11": "10.5",
    "11.8": "10.11",
}
TEST_DIR = Path(__file__).parent.absolute()
Vars = namedtuple(
    "Vars",
    [
        "OS",
        "VERSION",
        "IMAGE_NAME",
        "TEST_DIR",
        "TAG",
        "TEST_APP",
        "VERY_LONG_DB_NAME",
        "VERY_LONG_USER_NAME",
        "SSL_OPTION",
        "PREVIOUS_VERSION",
    ],
)
VERSION = os.getenv("VERSION")
OS = os.getenv("TARGET").lower()
TEST_APP = TEST_DIR / "test-app"
VERY_LONG_DB_NAME = "very_long_database_name_" + "x" * 20
VERY_LONG_USER_NAME = "very_long_user_name_" + "x" * 20
# MariaDB 11.3+ enforces stricter SSL/TLS verification (certificate & hostname checks),
# so tests may require this option for compatibility.
# https://mariadb.org/mission-impossible-zero-configuration-ssl/
SSL_OPTION = "--disable-ssl-verify-server-cert" if VERSION == "11.8" else ""
VARS = Vars(
    OS=OS,
    VERSION=VERSION,
    IMAGE_NAME=os.getenv("IMAGE_NAME"),
    TEST_DIR=Path(__file__).parent.absolute(),
    TAG=TAGS.get(OS),
    TEST_APP=TEST_APP,
    VERY_LONG_DB_NAME=VERY_LONG_DB_NAME,
    VERY_LONG_USER_NAME=VERY_LONG_USER_NAME,
    SSL_OPTION=SSL_OPTION,  # used for tests that require SSL verification to be disabled
    PREVIOUS_VERSION=MARIADB_PREVIOUS_VERSIONS.get(VERSION),
)
