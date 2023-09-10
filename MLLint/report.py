from observation import Observation
from pathlib import Path
from fastavro import schema, writer, reader
from typing import List, Dict
from itertools import chain
from importlib_resources import files
import schemas


class Report:
    def __init__(
        self, observations: Dict[str, List[Observation]], outfile: Path, full: bool
    ) -> str:
        self.observations = observations
        self.outfile = outfile
        self.full_report = full

    def __str__(self):
        """
        Generates a report based on the findings from Trufflehog and Semgrep.
        """
        if self.full_report:
            with open(self.outfile, "rb") as f:
                contents = reader(f)
                return "\n".join([str(r) for r in contents])

        else:
            if (
                len(
                    list(
                        chain(
                            *[
                                observations
                                for finder, observations in self.observations.items()
                            ]
                        )
                    )
                )
                == 0
            ):
                return "\U0001f680 LGTM"
            finding_location = f"Findings stored at: {self.outfile}"
            valid_credentials = f"Trufflehog identified {len(self.observations['trufflehog'])} valid credentials"
            unique_valid_credentials = f" - {len(set([x.source_code for x in self.observations['trufflehog']]))} of these were unique"
            credential_services = f" - Representing the following services: {list(set([x.finder_rule for x in self.observations['trufflehog']]))}"
            semgrep_observation_count = f"Semgrep identified {len(self.observations['semgrep'])} instances of vulnerable or risky code."
            return "\n".join(
                [
                    finding_location,
                    valid_credentials,
                    unique_valid_credentials,
                    credential_services,
                    semgrep_observation_count,
                ]
            )

    def to_avro(self) -> None:
        """
        Converts a list of observations into Avro format and writes it to a file.

        Raises:
            Any exceptions raised by schema.load_schema() or the Avro writer.
        """
        Path("obs").mkdir(parents=True, exist_ok=True)
        inp_file = files(schemas).joinpath("observation.avsc")
        s = schema.load_schema(inp_file)
        with open(self.outfile, "wb") as out:
            writer(
                out,
                s,
                [
                    dict(observation)
                    for finder, observation_list in self.observations.items()
                    for observation in observation_list
                ],
            )
