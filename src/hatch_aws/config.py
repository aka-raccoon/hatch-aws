from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from hatchling.builders.config import BuilderConfig

DEFAULT_TEMPLATE = "template.yml"


class AwsBuilderConfig(BuilderConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__directory = None
        self.__template = None
        self.__sam_exec = "sam"
        self.__use_sam = False
        self.__sam_params = None

    def default_exclude(self) -> list:
        return ["tests/"]

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
    def sam_exec(self) -> str:
        self.__sam_exec = self.target_config.get("sam_exec", self.__sam_exec)
        self.__sam_exec = os.getenv("HATCH_SAM_EXEC", self.__sam_exec)
        if not isinstance(self.__sam_exec, str):
            raise TypeError(
                f"Field `tool.hatch.build.targets.{self.plugin_name}.sam_exec` " "must be a string."
            )
        return self.__sam_exec

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
    def only_packages(self) -> bool:
        return True

    def default_include(self):
        return list(self.force_include.keys())
