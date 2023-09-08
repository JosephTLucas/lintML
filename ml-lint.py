import asyncio
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
from semgrep import run_semgrep
from trufflehog import run_trufflehog
import docker
import logging
from fastavro import writer, reader, schema
from observation import Observation


class MLlint:
    def __init__(self, indir, outfile="obs/observation.avro"):
        self.indir = Path(indir)
        self.outfile = Path(outfile)

    async def to_avro(self, observations: list[Observation]):
        """
        Converts a list of observations into Avro format and writes it to a file.

        Args:
            observations (list): A list of observation objects to be converted.

        Returns:
            None

        Note:
            - The Avro schema file "observation.avsc" should be present for successful conversion.
            - Ensure `self.outfile` points to a valid file path.

        Raises:
            Any exceptions raised by schema.load_schema() or the Avro writer.

        """
        Path("obs").mkdir(parents=True, exist_ok=True)
        s = schema.load_schema("observation.avsc")
        with open(self.outfile, "wb") as out:
            writer(out, s, [dict(o) for o in observations])
        return

    def generate_report(
        self, trufflehog: list[Observation], semgrep: list[Observation]
    ):
        """
        Generates a report based on the findings from Trufflehog and Semgrep.

        Args:
            trufflehog (list): List of valid credentials identified by Trufflehog.
            semgrep (list): List of instances of vulnerable or risky code identified by Semgrep.

        Returns:
            None

        Prints:
            - Path where the findings are stored.
            - Number of valid credentials identified by Trufflehog.
            - Number of unique valid credentials identified by Trufflehog.
            - List of services represented by the valid credentials.
            - Number of instances of vulnerable or risky code identified by Semgrep.
        """
        print(f"Findings stored at: {self.outfile}")
        print(f"Trufflehog identified {len(trufflehog)} valid credentials")
        print(
            f" - {len(set([x.source_code for x in trufflehog]))} of these were unique"
        )
        print(
            f" - Representing the following services: {list(set([x.finder_rule for x in trufflehog]))}"
        )
        print(
            f"Semgrep identified {len(semgrep)} instances of vulnerable or risky code."
        )
        return

    async def get_observations(self) -> (list[Observation], list[Observation]):
        """
        Retrieves observations by running Trufflehog and Semgrep within Docker containers.

        This function performs the following steps:
        1. Attempts to establish a connection with the Docker environment.
        2. If unsuccessful, logs an error message and exits.
        3. Runs Trufflehog and Semgrep concurrently using asyncio.TaskGroup.
        4. Combines the results and converts them to Avro format.
        5. Returns the results.

        Returns:
            tuple: A tuple containing the Trufflehog and Semgrep observations.

        Raises:
            docker.errors.DockerException: If unable to connect to the Docker environment.
            Any exceptions raised by the underlying functions run_trufflehog and run_semgrep.
        """
        try:
            client = docker.from_env()
        except docker.errors.DockerException:
            logging.exception(
                "Unable to resolve docker environment. Ensure user is logged into docker and a member of the docker group on the host."
            )
            exit()
        async with asyncio.TaskGroup() as tg:
            trufflehog = tg.create_task(run_trufflehog(client, self.indir))
            semgrep = tg.create_task(run_semgrep(client, self.indir))
        trufflehog = trufflehog.result()
        semgrep = semgrep.result()
        await self.to_avro(trufflehog + semgrep)

        return trufflehog, semgrep


def is_valid_directory(path: str) -> bool:
    """
    Check if the given path is a valid directory.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is a valid directory, False otherwise.
    """
    path = Path(path)
    if path.is_dir():
        return path
    else:
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid directory.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ml-lint",
        description="Linter for ML training code",
        epilog="Have any rules we should add?",
    )
    parser.add_argument(
        "dir", type=is_valid_directory, help="The target directory to lint"
    )
    args = parser.parse_args()
    m = MLlint(indir=Path(args.dir).resolve())
    loop = asyncio.get_event_loop()
    creds, code_findings = loop.run_until_complete(m.get_observations())
    m.generate_report(creds, code_findings)
