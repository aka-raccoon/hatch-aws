from pathlib import Path
from shutil import copy
from tempfile import TemporaryDirectory
from typing import Any, Callable, Dict, Generator, List, Optional

# pylint: disable=redefined-outer-name
import pytest
import tomli_w

from hatch_aws.aws import AwsLambda
from hatch_aws.builder import AwsBuilder


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with TemporaryDirectory() as directory:
        yield Path(directory).resolve()


@pytest.fixture
def asset() -> Callable:
    def _locate_asset(file: str) -> Path:
        return Path(__file__).parent.resolve() / "assets" / file

    return _locate_asset


def make_files(root: Path, files: List[str]) -> None:
    for file in files:
        path = root / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()


@pytest.fixture
def hatch(temp_dir, asset) -> Callable:
    default_config: Dict[str, Any] = {
        "project": {
            "name": "my-app",
            "version": "0.0.1",
        },
        "tool": {"hatch": {"build": {"only-packages": False, "targets": {"aws": {}}}}},
    }

    def _make_project(
        config: Optional[Dict] = None,
        dependencies: Optional[List] = None,
        optional_dependencies: Optional[Dict] = None,
        template: str = "sam-template.yml",
        build_conf: Optional[Dict] = None,
        files: Optional[List[str]] = None,
    ):
        if not config:
            config = default_config
        if dependencies:
            config["project"]["dependencies"] = dependencies
        if optional_dependencies:
            config["project"]["optional-dependencies"] = optional_dependencies

        if build_conf:
            config["tool"]["hatch"]["build"]["targets"]["aws"] = build_conf

        builder = AwsBuilder(str(temp_dir), config=config)

        copy(src=asset(template), dst=temp_dir / "template.yml")

        pyproject = temp_dir / "pyproject.toml"
        with open(pyproject, mode="wb") as file:
            tomli_w.dump(config, file)

        if not files:
            files = [
                "tests/test_app.py",
                "scripts/something.sh",
                "src/my_app/lambdas/lambda1/main.py",
                "src/my_app/lambdas/lambda1/db.py",
                "src/my_app/lambdas/lambda2/main.py",
                "src/my_app/common/config.py",
                "src/my_app/common/models.py",
                "src/my_app/utils/storage.py",
                "src/my_app/utils/logger.py",
            ]

        make_files(root=temp_dir, files=files)

        return builder

    return _make_project


@pytest.fixture
def aws_lambda() -> AwsLambda:
    return AwsLambda(
        default_code_uri=None,
        default_handler=None,
        resource={
            "Properties": {
                "CodeUri": "src",
                "Handler": "my_app.lambdas.lambda1.main.app",
                "Policies": "AWSLambdaExecute",
                "Events": {
                    "CreateThumbnailEvent": {
                        "Type": "S3",
                        "Properties": {"Bucket": "SrcBucket", "Events": "s3:ObjectCreated:*"},
                    }
                },
            }
        },
        name="MyLambdaFunc",
    )
