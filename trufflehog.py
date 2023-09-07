import docker


def run_trufflehog(dir):
    client = docker.from_env()
    container_out = client.containers.run(
        "trufflesecurity/trufflehog:latest",
        command="filesystem /pwd --json --only-verified",
        stdout=True,
        stderr=True,
        volumes={dir: {"bind": "/pwd", "mode": "ro"}},
    )
    return container_out
