import sys
from contextlib import suppress
from os import sep
from pathlib import Path
from shlex import quote
from shutil import copy, rmtree
from subprocess import PIPE, check_call  # nosec
from typing import Dict, List

from hatchling.builders.plugin.interface import BuilderInterface, IncludedFile
from hatchling.metadata.utils import normalize_project_name

from hatch_aws.aws import AwsLambda, Sam
from hatch_aws.config import AwsBuilderConfig


def matches_shared_file(path: Path, build_dir: Path, shared_files: List[IncludedFile]):
    dist_path = (build_dir / file.distribution_path for file in shared_files)
    return any(file in path.parents or file == path for file in dist_path)


class AwsBuilder(BuilderInterface):
    """
    Build AWS Lambda Functions source code
    """

    PLUGIN_NAME = "aws"

    def get_version_api(self) -> Dict:
        return {"standard": self.build_standard}

    def clean(self, directory: str, _versions):
        rmtree(directory)

    def build_lambda(self, aws_lambda: AwsLambda, shared_files: List[IncludedFile]) -> None:
        build_dir = Path(self.config.directory) / aws_lambda.name
        target = build_dir / aws_lambda.path
        dirs: List[Path] = []
        for path in build_dir.rglob("*"):
            if path.is_dir():
                dirs.append(path)
                continue
            if not any(
                (
                    target in path.parents,
                    matches_shared_file(build_dir=build_dir, path=path, shared_files=shared_files),
                )
            ):
                path.unlink(missing_ok=True)
        for folder in sorted(dirs, reverse=True):
            with suppress(OSError):
                folder.rmdir()
        deps = self.get_dependencies(module_name=normalize_project_name(aws_lambda.name))

        if not deps:
            return
        requirements_file = target / "requirements.txt"
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
        try:
            sam = Sam(template=self.config.template)
        except AttributeError:
            self.app.abort(
                "Unsupported type for a 'CodeUri' or 'Handler'. Only string is supported."
                "Functions !Sub, !Ref and others are not supported yet. "
            )
            raise
        self.app.display_waiting("Building lambda functions ...")
        result = sam.invoke_sam_build(
            build_dir=self.config.directory, params=self.config.sam_params
        )
        if result.returncode != 0:
            self.app.display_error(result.stderr)
            self.app.abort("SAM build failed!")

        if self.config.use_sam:
            return directory

        shared_files = list(self.recurse_included_files())
        for aws_lambda in sam.lambdas:
            self.app.display_info(f"{aws_lambda.name} ...", end=" ")
            self.build_lambda(aws_lambda=aws_lambda, shared_files=shared_files)
            self.app.display_success("success")

        if self.config.force_include:
            build_dir = Path(self.config.directory)
            for file in shared_files:
                if not "*" in file.distribution_path:
                    copy(src=file.path, dst=build_dir / file.distribution_path)
                    continue
                *glob, filename = file.distribution_path.rpartition("*")
                for path in build_dir.glob(pattern="".join(glob)):
                    if path.is_file():
                        continue
                    if filename.startswith(sep):
                        filename = filename[1:]
                    target = path / filename
                    target.parent.mkdir(exist_ok=True, parents=True)
                    if not target.exists():
                        copy(src=file.path, dst=target)
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
    def get_config_class(cls):
        return AwsBuilderConfig
