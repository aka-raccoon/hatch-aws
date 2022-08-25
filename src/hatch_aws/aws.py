import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generator, List, Optional, Union

from click.testing import CliRunner, Result
from samcli.commands.build.command import cli
from samcli.yamlhelper import yaml_parse

from hatch_aws.exceptions import ParameterIsMissing, UnsupportedTypeForParameter


@dataclass
class AwsLambda:
    default_code_uri: Union[str, Dict, None]
    default_handler: Union[str, Dict, None]
    resource: Dict
    name: str
    code_uri: Path = field(init=False)
    handler: Path = field(init=False)
    module: Path = field(init=False)

    def __post_init__(self):
        self.code_uri = self._set_code_uri()
        self.handler = self._set_handler()
        self.module = self.handler.parent.parent

    def _get_property_value(self, default_val: Union[str, Dict, None], param: str) -> str:
        try:
            value = self.resource["Properties"][param]
        except KeyError as error:
            if not default_val:
                raise ParameterIsMissing(lambda_name=self.name, parameter=param) from error
            value = default_val

        if not isinstance(value, str):
            raise UnsupportedTypeForParameter(lambda_name=self.name, parameter=param)
        return value

    def _set_handler(self) -> Path:
        value = self._get_property_value(default_val=self.default_handler, param="Handler")
        value = value.replace(".", "/")
        return Path(value)

    def _set_code_uri(self) -> Path:
        value = self._get_property_value(default_val=self.default_code_uri, param="CodeUri")
        return Path(value)


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
                default_code_uri=self._get_global_code_uri(),
                default_handler=self._get_global_handler(),
            )
            for resource, param in resources.items()
            if param["Type"] == "AWS::Serverless::Function"
        ]

    @staticmethod
    @contextmanager
    def disable_sam_logging() -> Generator[None, None, None]:
        logging.disable(logging.CRITICAL)
        yield
        logging.disable(logging.NOTSET)

    def _parse_sam_template(self) -> Dict:
        return yaml_parse(self.template_path.read_text(encoding="utf-8"))

    def invoke_sam_build(self, build_dir: str, params: Optional[List[str]] = None) -> Result:
        def_params = ["--template", str(self.template_path), "--build-dir", build_dir]
        if not params:
            params = []
        params.extend(def_params)

        with self.disable_sam_logging():
            return CliRunner().invoke(cli, params, catch_exceptions=False)

    def _get_global_code_uri(self) -> Union[Dict, str, None]:
        try:
            return self.template["Globals"]["Function"]["CodeUri"]
        except KeyError:
            return None

    def _get_global_handler(self) -> Union[Dict, str, None]:
        try:
            return self.template["Globals"]["Function"]["Handler"]
        except KeyError:
            return None
