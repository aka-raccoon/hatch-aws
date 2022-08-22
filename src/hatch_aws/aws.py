import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generator, List, Optional, Union

from click.testing import CliRunner, Result
from samcli.commands.build.command import cli
from samcli.yamlhelper import yaml_parse

from hatch_aws.exceptions import CodeUriMissing, CodeUriUnsupportedType


@dataclass
class AwsLambda:
    default_path: Union[str, Dict, None]
    resource: Dict
    name: str
    path: Path = field(init=False)
    module: str = field(init=False)

    def __post_init__(self):
        self.path = self._get_path()
        self.module = self.path.name

    def _get_path(self) -> Path:
        try:
            path = self.resource["Properties"]["CodeUri"]
        except KeyError as error:
            if not self.default_path:
                raise CodeUriMissing(lambda_name=self.name) from error
            path = self.default_path

        if not isinstance(path, str):
            raise CodeUriUnsupportedType(lambda_name=self.name)
        return Path(path)


class Sam:
    def __init__(self, template: Path):
        self.template_path = template
        self.template = self._parse_sam_template()
        self.lambdas = self._get_aws_lambdas()

    def _get_aws_lambdas(self) -> List[AwsLambda]:
        resources = self.template["Resources"]
        return [
            AwsLambda(
                name=resource,
                resource=resources[resource],
                default_path=self._get_global_code_uri(),
            )
            for resource, param in resources.items()
            if param["Type"] == "AWS::Serverless::Function"
        ]

    @staticmethod
    @contextmanager
    def disable_sam_logging() -> Generator[None, None, None]:
        logging.getLogger("aws_lambda_builders").setLevel(logging.WARNING)
        logging.getLogger("samcli").setLevel(logging.WARNING)
        yield
        logging.getLogger("aws_lambda_builders").setLevel(logging.INFO)
        logging.getLogger("samcli").setLevel(logging.INFO)

    def _parse_sam_template(self) -> Dict:
        return yaml_parse(self.template_path.read_text(encoding="utf-8"))

    def invoke_sam_build(
        self, use_container: bool, parameter_overrides: Optional[List] = None
    ) -> Result:
        params = ["--template", str(self.template_path)]
        if use_container:
            params.append("--use-container")
        if parameter_overrides:
            args = []
            for parameters in parameter_overrides:
                for key, value in parameters.items():
                    args.append(f"{key}={value}")
            params.append("--parameter-overrides")
            params.append(" ".join(args))

        with self.disable_sam_logging():
            return CliRunner().invoke(cli, params, catch_exceptions=False)

    def _get_global_code_uri(self) -> Union[Dict, str, None]:
        try:
            return self.template["Globals"]["Function"]["CodeUri"]
        except KeyError:
            return None
