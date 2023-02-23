import os
from pathlib import Path
from platform import python_version_tuple

import pytest
from hatchling.builders.plugin.interface import IncludedFile


@pytest.mark.slow
def test_build_with_real_sam(hatch):
    major, minor, _patch = python_version_tuple()
    assert major == "3"
    minor = min(int(minor), 9)
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
    "force_include, expected_files",
    (
        (
            {
                "src/my_app/common": "my_app/common",
                "src/my_app/utils/logger.py": "my_app/utils/logger.py",
            },
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
            {"void/null/nothing": "void/null/nothing"},
            [
                "my_app/lambdas/lambda1/main.py",
                "my_app/lambdas/lambda1/db.py",
            ],
        ),
    ),
)
def test_build_lambda(hatch, force_include, expected_files, aws_lambda):
    builder = hatch(force_include=force_include, build=True)

    shared_files = []

    if force_include:
        for rel, dist in force_include.items():
            absolute_path = Path(builder.root) / rel
            if absolute_path.is_file():
                shared_files.append(
                    IncludedFile(distribution_path=dist, relative_path=rel, path=str(absolute_path))
                )
            for path in absolute_path.rglob("*"):
                if path.is_file():
                    shared_files.append(
                        IncludedFile(
                            distribution_path=dist, relative_path=rel, path=str(absolute_path)
                        )
                    )

    builder.build_lambda(aws_lambda=aws_lambda, shared_files=shared_files)
    dist_folder = Path(f"{builder.root}/.aws-sam/build/MyLambda1Func")

    expected = sorted([str(dist_folder / file) for file in expected_files])
    files_in_dist = [str(path) for path in dist_folder.rglob("*") if path.is_file()]

    assert sorted(files_in_dist) == expected


@pytest.mark.slow
@pytest.mark.parametrize(
    "deps", [{"dependencies": ["pytest"]}, {"optional_dependencies": {"mylambda1func": ["pytest"]}}]
)
def test_build_lambda_with_pip_requirements(hatch, aws_lambda, deps):
    builder = hatch(build=True, **deps)

    builder.build_lambda(aws_lambda=aws_lambda, shared_files=[])
    dist_folder = Path(f"{builder.root}/.aws-sam/build/MyLambda1Func")
    assert (dist_folder / "pytest").is_dir()


@pytest.mark.slow
def test_build_lambda_limited_src(hatch, limited_src_lambda):
    builder = hatch(build=True)

    builder.build_lambda(aws_lambda=limited_src_lambda, shared_files=[])

    dist_folder = Path(f"{builder.root}/.aws-sam/build/MyLambda3Func")
    files = os.listdir(dist_folder)
    assert sorted(files) == ["db.py", "main.py"]
