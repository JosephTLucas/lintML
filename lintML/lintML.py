import asyncio
from pathlib import Path
import argparse
from semgrep import run_semgrep
from trufflehog import run_trufflehog
import docker
import logging
from observation import Observation
import os
from report import Report
from utils import is_valid_directory


class lintML:
    def __init__(self, indir, outfile="obs/observation.avro"):
        self.indir = Path(indir)
        self.outfile = Path(outfile)
        self.report = None

    def generate_report(
        self, trufflehog: list[Observation], semgrep: list[Observation], full=False
    ) -> str:
        r = Report({"trufflehog": trufflehog, "semgrep": semgrep}, self.outfile, full)
        r.to_avro()
        return r

    async def get_observations(self) -> (list[Observation], list[Observation]):
        """
        Retrieves observations by running Trufflehog and Semgrep within Docker containers.

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
        return trufflehog, semgrep


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="lintML",
        description="Linter for ML training code",
        epilog="Have any rules we should add?",
    )
    parser.add_argument(
        "dir",
        type=is_valid_directory,
        default=os.getcwd(),
        nargs="?",
        help="The target directory to lint",
    )
    parser.add_argument(
        "--full-report", action="store_true", help="Generate a full report"
    )
    args = parser.parse_args()
    m = lintML(indir=Path(args.dir).resolve())
    loop = asyncio.get_event_loop()
    creds, code_findings = loop.run_until_complete(m.get_observations())
    print(m.generate_report(creds, code_findings, args.full_report))
