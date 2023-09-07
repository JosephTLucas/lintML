from observation import Observation
import json


def create_trufflehog_observation(finding):
    return Observation(
        category="Verified Credential",
        source_file=finding["SourceMetadata"]["Data"]["Filesystem"]["file"],
        source_code=finding["Raw"],
        finder="TruffleHog",
        finder_rule=finding["DetectorName"],
    )


async def run_trufflehog(client, dir):
    container_bytes = client.containers.run(
        "trufflesecurity/trufflehog:latest",
        command="filesystem /pwd --json --only-verified",
        stdout=True,
        stderr=True,
        volumes={dir: {"bind": "/pwd", "mode": "ro"}},
    )
    container_str = container_bytes.decode("utf8")
    findings = container_str.split("\n")
    observations = [
        create_trufflehog_observation(json.loads(f))
        for f in findings
        if "SourceMetadata" in f
    ]
    return observations
