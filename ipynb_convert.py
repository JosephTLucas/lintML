from nbconvert import PythonExporter
from pathlib import Path
from typing import Iterable
from tempfile import TemporaryDirectory


def filter_comments(code: str) -> str:
    """
    Remove comments from strings by splitting on newlines and removing any lines that start with `#`
    """
    return "\n".join(
        list(filter(lambda x: x.startswith("#") == False, code.split("\n")))
    )


async def get_ipynb_code(ipynb_iter: Iterable[Path], tmpdir: TemporaryDirectory):
    """
    Convert a collection of Jupyter notebooks to Python files.

    Args:
        ipynb_iter (Iterable[Path]): An iterable containing paths to Jupyter notebook files.
        tmpdir (TemporaryDirectory): A temporary directory where the Python files will be stored.

    Returns:
        None

    Converts each notebook to a Python file using the nbconvert library and stores it in the
    temporary directory. Comments in the generated Python code are filtered out before writing.

    Raises:
        Any exceptions raised by nbconvert.exporters.PythonExporter or file operations.
    """
    exporter = PythonExporter(exclude_markdown=True, exclude_raw=True)
    for f_nb in ipynb_iter:
        with open(f_nb, "r") as infile:
            with open(
                tmpdir.name + f"/{f_nb.name.replace('.ipynb', '.py')}", "w"
            ) as outfile:
                outfile.write(filter_comments(exporter.from_file(infile)[0]))
