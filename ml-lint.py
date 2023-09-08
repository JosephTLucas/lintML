import asyncio
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
from semgrep import run_semgrep
from trufflehog import run_trufflehog
import docker
import logging
from fastavro import writer, reader, schema


class MLlint:
    def __init__(self, indir, outfile="obs/observation.avro"):
        self.indir = Path(indir)
        self.outfile = Path(outfile)

    async def get_container(self, client, func):
        _executor = ThreadPoolExecutor(1)
        return await loop.run_in_executor(_executor, func, client, self.indir)

    async def to_avro(self, observations):
        Path("obs").mkdir(parents=True, exist_ok=True)
        s = schema.load_schema("observation.avsc")
        with open(self.outfile, "wb") as out:
            writer(out, s, [dict(o) for o in observations])
        return

    def generate_report(self, trufflehog, semgrep):
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

    async def get_observations(self):
        try:
            client = docker.from_env()
        except docker.errors.DockerException:
            logging.exception(
                "Unable to resolve docker environment. Ensure user is logged into docker and a member of the docker group on the host."
            )
            exit()
        async with asyncio.TaskGroup() as tg:
            # trufflehog = tg.create_task(self.get_container(client, run_trufflehog))
            # semgrep = tg.create_task(self.get_container(client, run_semgrep))
            trufflehog = tg.create_task(run_trufflehog(client, self.indir))
            semgrep = tg.create_task(run_semgrep(client, self.indir))
        trufflehog = trufflehog.result()
        semgrep = semgrep.result()
        await self.to_avro(trufflehog + semgrep)

        return trufflehog, semgrep


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ml-lint",
        description="Linter for ML training code",
        epilog="Have any rules we should add?",
    )
    parser.add_argument("dir")
    args = parser.parse_args()

    if not Path(args.dir).is_dir():
        print("Provide a target directory")
    else:
        m = MLlint(indir=Path(args.dir).resolve())
        loop = asyncio.get_event_loop()
        creds, code_findings = loop.run_until_complete(m.get_observations())
        m.generate_report(creds, code_findings)
