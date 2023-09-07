import asyncio
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
from semgrep import run_semgrep
from trufflehog import run_trufflehog


async def get_container(dir, func):
    _executor = ThreadPoolExecutor(1)
    return await loop.run_in_executor(_executor, func, dir)


async def main():
    parser = argparse.ArgumentParser(
        prog="ml-lint",
        description="Linter for ML training code",
        epilog="Have any rules we should add?",
    )
    parser.add_argument("dir")
    args = parser.parse_args()
    async with asyncio.TaskGroup() as tg:
        trufflehog = tg.create_task(get_container(args.dir, run_trufflehog))
        semgrep = tg.create_task(get_container(args.dir, run_semgrep))
    return trufflehog.result(), semgrep.result()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(main()))
