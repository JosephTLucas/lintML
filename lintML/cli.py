from lintML.lintML import lintML
import argparse
from lintML.utils import is_valid_directory
import os
from pathlib import Path
import asyncio

def run():
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