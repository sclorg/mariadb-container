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
        "DB_NAME",
    ],
)
VERSION = os.getenv("VERSION")
OS = os.getenv("TARGET").lower()
TEST_APP = TEST_DIR / "test-app"
VERY_LONG_DB_NAME = "very_long_database_name_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
VERY_LONG_USER_NAME = "very_long_user_name_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# MariaDB 11.3+ enforces stricter SSL/TLS verification (certificate & hostname checks),
# so tests may require this option for compatibility.
# https://mariadb.org/mission-impossible-zero-configuration-ssl/
DB_NAME = "--disable-ssl-verify-server-cert db" if VERSION == "11.8" else "db"
VARS = Vars(
    OS=OS,
    VERSION=VERSION,
    IMAGE_NAME=os.getenv("IMAGE_NAME"),
    TEST_DIR=Path(__file__).parent.absolute(),
    TAG=TAGS.get(OS),
    TEST_APP=TEST_APP,
    VERY_LONG_DB_NAME=VERY_LONG_DB_NAME,
    VERY_LONG_USER_NAME=VERY_LONG_USER_NAME,
    DB_NAME=DB_NAME,
)


def get_previous_major_version():
    version_dict = {
        "10.3": "10.2",
        "10.5": "10.3",
        "10.11": "10.5",
        "11.8": "10.11",
    }
    return version_dict.get(VARS.VERSION)
