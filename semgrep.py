from observation import Observation
import json
from tempfile import TemporaryDirectory
from ipynb_convert import get_ipynb_code


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
    container_bytes = client.containers.run(
        "returntocorp/semgrep:latest",
        command="semgrep --config 'p/trailofbits' --config 'p/python' --json /pwd --metrics=off -q --exclude-rule trailofbits.python.automatic-memory-pinning.automatic-memory-pinning",
        stdout=True,
        stderr=True,
        volumes={dir: {"bind": "/pwd", "mode": "ro"}},
    )
    container_str = container_bytes.decode("utf8")
    container_json = json.loads(container_str)
    observations = [create_semgrep_observation(f) for f in container_json["results"]]
    tmpdir.cleanup()
    return observations
