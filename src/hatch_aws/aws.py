from dataclasses import dataclass
from os import sep
from pathlib import Path
from subprocess import run  # nosec
from typing import Dict, List, Optional

import yaml


@dataclass
class AwsLambda:
    name: str
    path: Path


class Sam:  # pylint: disable=too-few-public-methods
    def __init__(self, template: Path):
        self.template_path = template
        self.template = self._parse_sam_template()
        self.lambdas = self._get_aws_lambdas()

    def _get_aws_lambdas(self) -> List[AwsLambda]:
        resources = self.template["Resources"]
        lambdas = {
            resource: {
                **self.template.get("Globals", {}).get("Function", {}),
                **resources[resource]["Properties"],
            }
            for resource, param in resources.items()
            if param["Type"] == "AWS::Serverless::Function"
        }
        return [
            AwsLambda(
                name=resource,
                path=Path(param["Handler"].replace(".", sep)).parent.parent,
            )
            for resource, param in lambdas.items()
            if param.get("Runtime", "").lower().startswith("python")
        ]

    def _parse_sam_template(self) -> Dict:
        yaml.SafeLoader.add_multi_constructor("!", lambda *args: None)
        return yaml.safe_load(self.template_path.read_text(encoding="utf-8"))

    def invoke_sam_build(self, build_dir: str, params: Optional[List[str]] = None):
        def_params = ["--template", str(self.template_path), "--build-dir", build_dir]
        if not params:
            params = []
        params.extend(def_params)

        return run(
            ["sam", "build"] + params, text=True, encoding="utf-8", capture_output=True, check=False
        )
