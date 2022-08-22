from pathlib import Path
from shutil import rmtree
from typing import Callable, Dict, List, Optional

from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface

from hatch_aws.aws import AwsLambda, Sam

DEFAULT_BUILD_DIR = ".aws/build"
DEFAULT_TEMPLATE_NAME = "template.yml"
DEFAULT_USE_CONTAINER = False


class AwsBuilderConfig(BuilderConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__directory = None
        self.__template_name = None
        self.__use_container = None
        self.__parameter_overrides = None

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
                directory = self.build_config.get("directory", DEFAULT_BUILD_DIR)
                if not isinstance(directory, str):
                    raise TypeError("Field `tool.hatch.build.directory` must be a string")

            self.__directory = self.normalize_build_directory(directory)

        return self.__directory

    @property
    def template_name(self) -> Path:
        if self.__template_name is None:
            template = Path(self.target_config.get("template-name", DEFAULT_TEMPLATE_NAME))
            if not template.is_absolute():
                template = self.root / template

            self.__template_name = template

        return self.__template_name

    @property
    def use_container(self) -> bool:
        if self.__use_container is None:
            self.__use_container = self.target_config.get("use-container", DEFAULT_USE_CONTAINER)
            if not isinstance(self.__use_container, bool):
                raise TypeError(
                    f"Field `tool.hatch.build.targets.{self.plugin_name}.use-container` "
                    "must be a boolean"
                )
        return self.__use_container

    @property
    def parameter_overrides(self) -> Optional[List]:
        if self.__parameter_overrides is None:
            self.__parameter_overrides = self.target_config.get("parameter-overrides")
            if self.__parameter_overrides is not None and not isinstance(
                self.__parameter_overrides, List
            ):
                raise TypeError(
                    f"Field `tool.hatch.build.targets.{self.plugin_name}.parameter-overrides` "
                    "must be a list of inline tables"
                )
        return self.__parameter_overrides


class AwsBuilder(BuilderInterface):
    """
    Build AWS Lambda Functions source code
    """

    PLUGIN_NAME = "aws"

    def get_version_api(self) -> Dict:
        return {"standard": self.build_standard}

    def clean(self, directory: str, _versions):
        rmtree(directory)

    def build_standard(self, directory: str, **_build_data) -> str:
        self.config: AwsBuilderConfig
        sam = Sam(template=self.config.template_name)

        for aws_lambda in sam.lambdas:
            self.app.display_waiting(f"Creating requirement file for {aws_lambda.name}...")
            self.create_requirements_file(aws_lambda=aws_lambda)

        self.app.display_waiting("Building lambda functions with SAM...")
        result = sam.invoke_sam_build(
            use_container=self.config.use_container,
            parameter_overrides=self.config.parameter_overrides,
        )
        if result.exit_code != 0:
            self.app.display_error(result.output)
            self.app.abort("SAM build failed!")

        self.app.display_success("Build successfull.")
        return directory

    def get_dependencies(self, module_name: str) -> List[str]:
        return sorted(
            [
                *self.metadata.core.dependencies,
                *self.metadata.core.optional_dependencies.get(module_name, []),
                self.root,
            ]
        )

    def create_requirements_file(self, aws_lambda: AwsLambda):
        dependencies = self.get_dependencies(module_name=aws_lambda.module)
        requirements_file = self.root / aws_lambda.path / "requirements.txt"
        requirements_file.write_text(
            data="\n".join(dependencies),
            encoding="utf-8",
        )

    @classmethod
    def get_config_class(cls) -> Callable[..., AwsBuilderConfig]:
        return AwsBuilderConfig
