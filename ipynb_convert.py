from nbconvert import PythonExporter
from pathlib import Path


def filter_comments(code: str) -> str:
    return "\n".join(
        list(filter(lambda x: x.startswith("#") == False, code.split("\n")))
    )


async def get_ipynb_code(ipynb_iter, tmpdir):
    exporter = PythonExporter(exclude_markdown=True, exclude_raw=True)
    for f_nb in ipynb_iter:
        with open(f_nb, "r") as infile:
            with open(
                tmpdir.name + f"/{f_nb.name.replace('.ipynb', '.py')}", "w"
            ) as outfile:
                outfile.write(filter_comments(exporter.from_file(infile)[0]))
