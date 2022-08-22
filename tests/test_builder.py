import os
from pathlib import Path
from platform import python_version_tuple
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner


@patch.object(CliRunner, "invoke", Mock(return_value=Mock(exit_code=1)))
def test_build_fails_on_rc_1(hatch):
    builder = hatch()
    with pytest.raises(SystemExit):
        builder.build_standard(os.getcwd())


@patch.object(CliRunner, "invoke", Mock(return_value=Mock(exit_code=0)))
def test_build_with_no_dependencies(hatch):
    builder = hatch()
    project_root = Path(builder.root)
    requiremens_file = project_root / "src" / "lambda1" / "requirements.txt"
    builder.build_standard(os.getcwd())
    requirements = requiremens_file.read_text()

    assert requiremens_file.is_file()
    assert str(project_root) in requirements


@patch.object(CliRunner, "invoke", Mock(return_value=Mock(exit_code=0)))
def test_build_with_dependencies(hatch):
    dependencies = [
        "package1==5.10.1",
        "package2==22.6.0",
        "package3==2.14.5",
    ]
    builder = hatch(dependencies=dependencies)

    project_root = Path(builder.root)
    requiremens_file = project_root / "src" / "lambda1" / "requirements.txt"
    builder.build_standard(os.getcwd())
    requirements = requiremens_file.read_text()

    dependencies.append(builder.root)
    assert sorted(dependencies) == requirements.splitlines()


@patch.object(CliRunner, "invoke", Mock(return_value=Mock(exit_code=0)))
def test_build_with_optional_dependencies(hatch):
    dependencies = [
        "package1==5.10.1",
        "package2==22.6.0",
        "package3==2.14.5",
    ]
    optional_dependencies = {
        "lambda1": ["lambda1-specific", "another-lambda1-specific"],
        "lambda2": ["lambda2-specific", "another-lambda2-specific"],
    }
    builder = hatch(dependencies=dependencies, optional_dependencies=optional_dependencies)

    project_root = Path(builder.root)
    lamba1_requiremens_file = project_root / "src" / "lambda1" / "requirements.txt"
    lamba2_requiremens_file = project_root / "src" / "lambda2" / "requirements.txt"
    builder.build_standard(os.getcwd())
    lambda1_requirements = lamba1_requiremens_file.read_text()
    lambda2_requirements = lamba2_requiremens_file.read_text()

    lambda1_dependences = sorted([*dependencies, *optional_dependencies["lambda1"], builder.root])
    lambda2_dependences = sorted([*dependencies, *optional_dependencies["lambda2"], builder.root])

    assert lambda1_dependences == lambda1_requirements.splitlines()
    assert lambda2_dependences == lambda2_requirements.splitlines()


@pytest.mark.slow
def test_build_with_real_sam(hatch):

    major, minor, _patch = python_version_tuple()
    assert major == "3"

    parameters = [{"PythonVersion": f"{major}.{minor}"}]
    builder = hatch(use_container=False, parameter_overrides=parameters)
    result = builder.build_standard(directory=builder.config.directory)

    assert result == builder.config.directory


def test_clean_method(hatch):
    builder = hatch()

    build_dir = Path(builder.config.directory)
    build_dir.mkdir(parents=True, exist_ok=True)
    app_file = build_dir / "data" / "app.py"
    app_file.parent.mkdir(parents=True, exist_ok=True)
    app_file.touch()

    builder.clean(directory=builder.config.directory, _versions=None)

    assert not build_dir.exists()


@pytest.mark.parametrize("template", ["bla", "template.yaml", "sam-template.yaml"])
def test_sam_template_config_option(hatch, template):
    config = {
        "project": {
            "name": "my-app",
            "version": "0.0.1",
        },
        "tool": {"hatch": {"build": {"targets": {"aws": {"template-name": template}}}}},
    }
    builder = hatch(config=config)

    assert builder.config.template_name == Path(builder.root) / template
