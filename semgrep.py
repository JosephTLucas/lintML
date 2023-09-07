import docker


def run_semgrep(dir):
    client = docker.from_env()
    container_out = client.containers.run(
        "returntocorp/semgrep:latest",
        command="semgrep --config 'p/python' --json /pwd --metrics=off",
        stdout=True,
        stderr=True,
        volumes={dir: {"bind": "/pwd", "mode": "ro"}},
    )
    return container_out
