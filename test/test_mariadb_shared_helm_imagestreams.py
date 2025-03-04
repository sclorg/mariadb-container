import os

import pytest
from pathlib import Path

from container_ci_suite.helm import HelmChartsAPI

test_dir = Path(os.path.abspath(os.path.dirname(__file__)))


class TestHelmRHELMariadbImageStreams:

    def setup_method(self):
        package_name = "redhat-mariadb-imagestreams"
        path = test_dir
        self.hc_api = HelmChartsAPI(path=path, package_name=package_name, tarball_dir=test_dir, shared_cluster=True)
        self.hc_api.clone_helm_chart_repo(
            repo_url="https://github.com/sclorg/helm-charts", repo_name="helm-charts",
            subdir="charts/redhat"
        )

    def teardown_method(self):
        self.hc_api.delete_project()

    @pytest.mark.parametrize(
        "version,registry,expected",
        [
            ("10.11-el9", "registry.redhat.io/rhel9/mariadb-1011:latest", True),
            ("10.11-el8", "registry.redhat.io/rhel8/mariadb-1011:latest", True),
            ("10.5-el9", "registry.redhat.io/rhel9/mariadb-105:latest", True),
            ("10.3-el8", "registry.redhat.io/rhel8/mariadb-103:latest", True),
            ("10.5-el8", "registry.redhat.io/rhel8/mariadb-105:latest", True),
        ],
    )
    def test_package_imagestream(self, version, registry, expected):
        assert self.hc_api.helm_package()
        assert self.hc_api.helm_installation()
        assert self.hc_api.check_imagestreams(version=version, registry=registry) == expected
