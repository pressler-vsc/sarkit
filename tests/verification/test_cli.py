import subprocess

import pytest


@pytest.mark.parametrize(
    "cmd", ("cphd-consistency", "crsd-consistency", "sicd-consistency")
)
def test_consistency_cli(cmd):
    subprocess.run([cmd, "-h"], check=True)
