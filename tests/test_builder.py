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
        builder.build_standard(builder.config.directory)


@pytest.mark.slow
def test_build_with_real_sam(hatch):

    major, minor, _patch = python_version_tuple()
    assert major == "3"
    build_conf = {"sam-params": ["--parameter-overrides", f"PythonVersion={major}.{minor}"]}
    builder = hatch(build_conf=build_conf)
    builder.build_standard(directory=builder.config.directory)

    dist = Path(f"{builder.root}/.aws-sam")

    assert (dist / "build.toml").is_file()
    assert (dist / "build" / "template.yaml").is_file()
    assert Path(
        f"{builder.root}/.aws-sam/build/MyLambda1Func/my_app/lambdas/lambda1/main.py"
    ).is_file()


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
        "tool": {"hatch": {"build": {"targets": {"aws": {"template": template}}}}},
    }
    builder = hatch(config=config)

    assert builder.config.template == Path(builder.root) / template


@pytest.mark.slow
@pytest.mark.parametrize(
    "build_conf, expected_files",
    (
        (
            {"include": ["src/my_app/common", "src/my_app/utils/logger.py"]},
            [
                "my_app/lambdas/lambda1/main.py",
                "my_app/lambdas/lambda1/db.py",
                "my_app/common/config.py",
                "my_app/common/models.py",
                "my_app/utils/logger.py",
            ],
        ),
        (
            None,
            [
                "my_app/lambdas/lambda1/main.py",
                "my_app/lambdas/lambda1/db.py",
            ],
        ),
        (
            {"include": ["void/null/nothing"]},
            [
                "my_app/lambdas/lambda1/main.py",
                "my_app/lambdas/lambda1/db.py",
            ],
        ),
    ),
)
def test_build_lambda(hatch, build_conf, expected_files, aws_lambda):
    builder = hatch(build_conf=build_conf)
    builder.build_lambda(aws_lambda=aws_lambda)
    dist_folder = Path(f"{builder.root}/.aws-sam/build/MyLambdaFunc")

    expected = sorted([str(dist_folder / file) for file in expected_files])
    files_in_dist = []
    for root, _dirs, files in os.walk(dist_folder):
        for file in files:
            files_in_dist.append(os.path.join(root, file))

    assert sorted(files_in_dist) == expected


@pytest.mark.slow
@pytest.mark.parametrize(
    "deps", [{"dependencies": ["pytest"]}, {"optional_dependencies": {"lambda1": ["pytest"]}}]
)
def test_build_lambda_with_pip_requirements(hatch, aws_lambda, deps):
    builder = hatch(**deps)

    builder.build_lambda(aws_lambda=aws_lambda)
    dist_folder = Path(f"{builder.root}/.aws-sam/build/MyLambdaFunc")
    assert (dist_folder / "pytest").is_dir()
