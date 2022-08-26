import sys
from pathlib import Path
from shlex import quote
from shutil import copy, copytree, rmtree
from subprocess import PIPE, check_call  # nosec
from typing import Callable, Dict, List, Optional

from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface

from hatch_aws.aws import AwsLambda, Sam

DEFAULT_TEMPLATE = "template.yml"


class AwsBuilderConfig(BuilderConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__directory = None
        self.__template = None
        self.__use_sam = False
        self.__sam_params = None
        self.__include = None

    @property
    def directory(self) -> str:
        if self.__directory is None:
            if "directory" in self.target_config:
                directory = self.target_config["directory"]
                if not isinstance(directory, str):
                    raise TypeError(
                        f"Field `tool.hatch.build.targets.{self.plugin_name}.directory` "
                        "must be a string"
                    )
            else:
                directory = self.build_config.get(
                    "directory", str(Path(self.root) / ".aws-sam/build")
                )
                if not isinstance(directory, str):
                    raise TypeError("Field `tool.hatch.build.directory` must be a string")
            self.__directory = self.normalize_build_directory(str(directory))

        return self.__directory

    @property
    def template(self) -> Path:
        if self.__template is None:
            template = Path(self.target_config.get("template", DEFAULT_TEMPLATE))
            if not template.is_absolute():
                template = self.root / template

            self.__template = template

        return self.__template

    @property
    def use_sam(self) -> bool:
        self.__use_sam = self.target_config.get("use-sam", self.__use_sam)
        if not isinstance(self.__use_sam, bool):
            raise TypeError(
                f"Field `tool.hatch.build.targets.{self.plugin_name}.use-sam` " "must be a boolean."
            )
        return self.__use_sam

    @property
    def sam_params(self) -> Optional[List[str]]:
        self.__sam_params = self.target_config.get("sam-params")
        if self.__sam_params is not None and not isinstance(self.__sam_params, list):
            raise TypeError(
                f"Field `tool.hatch.build.targets.{self.plugin_name}.sam-params` "
                "must be an array."
            )
        return self.__sam_params

    @property
    def include(self) -> Optional[List]:
        if self.__include is None:
            self.__include = self.target_config.get("include")
            if self.__include is not None and not isinstance(self.__include, List):
                raise TypeError(
                    f"Field `tool.hatch.build.targets.{self.plugin_name}.include` "
                    "must be an array."
                )
        return self.__include


class AwsBuilder(BuilderInterface):
    """
    Build AWS Lambda Functions source code
    """

    PLUGIN_NAME = "aws"

    def get_version_api(self) -> Dict:
        return {"standard": self.build_standard}

    def clean(self, directory: str, _versions):
        rmtree(directory)

    def build_lambda(self, aws_lambda: AwsLambda):
        build_dir = Path(self.config.directory) / aws_lambda.name
        if build_dir.exists():
            rmtree(build_dir)
        build_dir.mkdir(parents=True)
        lambda_dir = self.root / aws_lambda.code_uri / aws_lambda.module
        dist_lambda = build_dir / aws_lambda.module
        copytree(src=lambda_dir, dst=dist_lambda)
        if self.config.include:
            for thing in self.config.include:
                thing_as_path = Path(f"{self.root}/{thing}")
                thing = thing.replace("src/", "")
                dist = build_dir / thing
                if thing_as_path.is_file():
                    dist.parent.mkdir(parents=True, exist_ok=True)
                    copy(src=thing_as_path, dst=dist)
                if thing_as_path.is_dir():
                    copytree(src=thing_as_path, dst=dist)

        deps = self.get_dependencies(module_name=aws_lambda.module.name)
        if deps:
            requirements_file = dist_lambda / "requirements.txt"
            requirements_file.write_text(data="\n".join(deps), encoding="utf-8")
            check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "--disable-pip-version-check",
                    "--no-python-version-warning",
                    "-r",
                    quote(str(requirements_file)),
                    "-t",
                    quote(str(build_dir)),
                ],
                stdout=PIPE,
                stderr=PIPE,
                shell=False,
            )

    def build_standard(self, directory: str, **_build_data) -> str:
        self.config: AwsBuilderConfig
        sam = Sam(template=self.config.template)

        self.app.display_waiting("Building lambda functions ...")
        result = sam.invoke_sam_build(
            build_dir=self.config.directory, params=self.config.sam_params
        )
        if result.exit_code != 0:
            self.app.display_error(result.output)
            self.app.abort("SAM build failed!")

        if not self.config.use_sam:
            for aws_lambda in sam.lambdas:
                self.app.display_info(f"{aws_lambda.name} ...", end=" ")
                self.build_lambda(aws_lambda=aws_lambda)
                self.app.display_success("success")

        self.app.display_success("Build successfull 🚀")
        return directory

    def get_dependencies(self, module_name: str) -> List[str]:
        return sorted(
            [
                *self.metadata.core.dependencies,
                *self.metadata.core.optional_dependencies.get(module_name, []),
            ]
        )

    @classmethod
    def get_config_class(cls) -> Callable[..., AwsBuilderConfig]:
        return AwsBuilderConfig
