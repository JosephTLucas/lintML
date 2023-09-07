from dataclasses import dataclass
from fastavro import writer, reader, schema
from pathlib import Path
from uuid import uuid5
from hashlib import md5


@dataclass
class Observation:
    category: str
    source_file: str
    source_code: str
    finder: str
    finder_rule: str

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value
