from observation import Observation
import json
from tempfile import TemporaryDirectory
from ipynb_convert import get_ipynb_code
from pathlib import Path
import os


def create_semgrep_observation(finding):
    return Observation(
        category=finding["extra"]["metadata"]["vulnerability_class"][0],
        source_file=finding["path"],
        source_code=finding["extra"]["lines"],
        finder="Semgrep",
        finder_rule=finding["check_id"],
    )


async def semgrep_prep(dir):
    tmpdir = TemporaryDirectory(dir=dir, ignore_cleanup_errors=True)
    ipynb_files = dir.rglob("*.ipynb")
    await get_ipynb_code(ipynb_files, tmpdir)
    return tmpdir


async def run_semgrep(client, dir):
    tmpdir = await semgrep_prep(dir)
    rules = Path('semgrep_rules/ready')
    container_bytes = client.containers.run(
        "returntocorp/semgrep:latest",
        command="semgrep --config '/rules/' --json /pwd --metrics=off -q",
        stdout=True,
        stderr=True,
        volumes={dir: {"bind": "/pwd", "mode": "ro"},
                 rules.resolve(): {"bind": "/rules", "mode": "ro"}},
    )
    container_str = container_bytes.decode("utf8")
    container_json = json.loads(container_str)
    observations = [create_semgrep_observation(f) for f in container_json["results"]]
    tmpdir.cleanup()
    return observations
