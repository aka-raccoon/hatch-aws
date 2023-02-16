<!-- markdownlint-disable-file no-inline-html first-line-h1 -->
<div align="center">

# hatch-aws

[![PyPI - Version](https://img.shields.io/pypi/v/hatch-aws.svg)](https://pypi.org/project/hatch-aws) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-aws.svg)](https://pypi.org/project/hatch-aws) [![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch) [![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![types - mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy) [![imports - isort](https://img.shields.io/badge/imports-isort-ef8336.svg)](https://github.com/pycqa/isort)

AWS builder plugin for **[Hatch 🥚🐍](<https://hatch.pypa.io/latest/>)**.
*Hatch is modern, extensible Python project manager.*

</div>

---

Checkout my other plugin [hatch-aws-publisher](https://github.com/aka-raccoon/hatch-aws-publisher).

## Table of Contents

- [hatch-aws](#hatch-aws)
   - [Table of Contents](#table-of-contents)
   - [Global dependency](#global-dependency)
   - [Builder](#builder)
      - [How to use it](#how-to-use-it)
      - [Options](#options)
   - [License](#license)

## Global dependency

Add `hatch-aws` within the `build-system.requires` field in your `pyproject.toml` file.

```toml
[build-system]
requires = ["hatchling", "hatch-aws"]
build-backend = "hatchling.build"
```

## Builder

The [builder plugin](https://hatch.pypa.io/latest/plugins/builder/reference/) name is called `aws`.

To enable it, include following configuration in you config file:

- **pyproject.toml**

    ```toml
    [tool.hatch.build.targets.aws]
    ```

- **hatch.toml**

    ```toml
    [build.targets.aws]
    ```

### How to use it

1. Put your module and lambdas inside of `src` folder.

   ```shell
   .
   ├── pyproject.toml
   ├── src
   │   └── my_app
   │       ├── __init__.py
   │       ├── common
   │       │   ├── __init__.py
   │       │   ├── config.py
   │       │   └── models.py
   │       └── lambdas
   │           ├── lambda1
   │           │   ├── __init__.py
   │           │   └── main.py
   │           └── lambda2
   │               ├── __init__.py
   │               └── main.py
   └── template.yml
   ```

2. Specify common requirements for your project in `pyproject.toml` as dependencies.

   ```toml
   [project]
   dependencies = ["boto3"]
   ```

3. Specify requirements for your lambda functions in `pyproject.toml` as optional dependencies. Use module (folder) name.

   ```toml
   [project.optional-dependencies]
   lambda1 = ["pyaml"]
   lambda2 = ["request", "pydantic"]
   ```

4. Specify additional folders and files you want to copy to the build folder.

   ```toml
   [tool.hatch.build.targets.aws]
   include = ["src/my_app/common"]
   ```

5. Set the `CodeUri` and `Handler` parameter pointing to your lambdas in SAM template.

   ```yaml
   Resources:
    Lambda1:
      Type: AWS::Serverless::Function
      Properties:
        FunctionName: lambda1-function
        CodeUri: src
        Handler: my_app.lambdas.lambda1.main.app
        ...

    Lambda2:
      Type: AWS::Serverless::Function
      Properties:
        FunctionName: lambda2-function
        CodeUri: src
        Handler: my_app.lambdas.lambda2.main.app
        ...
   ```

6. Run `hatch build` command.

   ```shell
   ❯ hatch build
   [aws]
   Building lambda functions ...
   Lambda1 ... success
   Lambda2 ... success
   Build successfull 🚀
   /path/to/projects/.aws-sam/build
   ```

### Options

Following table contains available customization of builder behavior. You can find example of `pyproject.toml` in [tests/assets/pyproject.toml](https://github.com/aka-raccoon/hatch-aws/blob/main/tests/assets/pyproject.toml).

| Option       | Type    | Default        | Description                                             |
| ------------ | ------- | -------------- | ------------------------------------------------------- |
| `template`   | `str`   | `template.yml` | The filename of a SAM template.                         |
| `use-sam`    | `bool`  | `false`        | Use only SAM for build. Do not run custom copy actions. |
| `sam-params` | `array` |                | Pass additional options to a SAM build command          |

## License

Plugin `hatch-aws` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
