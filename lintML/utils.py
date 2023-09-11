import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


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


async def async_runner(loop, func):
    _executor = ThreadPoolExecutor(1)
    return await loop.run_in_executor(_executor, func)
