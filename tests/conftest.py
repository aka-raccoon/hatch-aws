from pathlib import Path
from shutil import copy
from tempfile import TemporaryDirectory
from typing import Any, Callable, Dict, Generator, List, Optional

# pylint: disable=redefined-outer-name
import pytest
import tomli_w

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
        use_container: bool = False,
        parameter_overrides: Optional[List] = None,
    ):
        if not config:
            config = default_config
        if dependencies:
            config["project"]["dependencies"] = dependencies
        if optional_dependencies:
            config["project"]["optional-dependencies"] = optional_dependencies

        build_conf = config["tool"]["hatch"]["build"]["targets"]["aws"]

        if use_container:
            build_conf["use-container"] = use_container

        if parameter_overrides:
            build_conf["parameter-overrides"] = parameter_overrides

        builder = AwsBuilder(str(temp_dir), config=config)

        copy(src=asset(template), dst=temp_dir / "template.yml")

        test_folder = temp_dir / "tests" / "test_app.py"
        test_folder.parent.mkdir(parents=True, exist_ok=True)
        test_folder.touch()
        scripts_folder = temp_dir / "scripts" / "something.sh"
        scripts_folder.parent.mkdir(parents=True, exist_ok=True)
        scripts_folder.touch()

        pyproject = temp_dir / "pyproject.toml"
        with open(pyproject, mode="wb") as file:
            tomli_w.dump(config, file)
        src_root = temp_dir / "src" / "my_app" / "__init__.py"
        src_root.parent.mkdir(parents=True, exist_ok=True)
        src_root.touch()

        lambda1_app = temp_dir / "src" / "lambda1" / "__init__.py"
        lambda1_app.parent.mkdir(parents=True, exist_ok=True)
        lambda1_app.touch()
        lambda2_app = temp_dir / "src" / "lambda2" / "__init__.py"
        lambda2_app.parent.mkdir(parents=True, exist_ok=True)
        lambda2_app.touch()
        return builder

    return _make_project
