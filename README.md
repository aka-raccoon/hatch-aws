<!-- markdownlint-disable-file no-inline-html first-line-h1 -->
<div align="center">

# hatch-aws

[![PyPI - Version](https://img.shields.io/pypi/v/hatch-aws.svg)](https://pypi.org/project/hatch-aws) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-aws.svg)](https://pypi.org/project/hatch-aws) [![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![types - mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy) [![imports - isort](https://img.shields.io/badge/imports-isort-ef8336.svg)](https://github.com/pycqa/isort)

AWS builder plugin for **[Hatch 🥚🐍](<https://hatch.pypa.io/latest/>)**.
*Hatch is modern, extensible Python project manager.*

</div>

---

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
   │   ├── lambda1
   │   │   ├── __init__.py
   │   │   └── app.py
   │   ├── lambda2
   │   │   ├── __init__.py
   │   │   └── app.py
   │   └── my_app # Code from within this module will be available for lambdas
   │       ├── __init__.py
   │       ├── config.py
   │       └── models.py
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
   lambda2 = ["requrest", "pydantic"]
   ```

4. Point the `CodeUri` parameter in a SAM template to a `src/<lambda_name>`.

   ```yaml
   Resources:
    Lambda1:
      Type: AWS::Serverless::Function
      Properties:
        FunctionName: lambda1-function
        CodeUri: src/lambda1
        Handler: app.lambda_handler
        ...

    Lambda2:
      Type: AWS::Serverless::Function
      Properties:
        FunctionName: lambda2-function
        CodeUri: src/lambda2
        Handler: app.lambda_handler
        ...
   ```

5. Run `hatch build` command 🚀.

   ```shell
   ❯ hatch build
   [aws]
   Creating requirement file for Lambda1...
   Creating requirement file for Lambda2...
   Building lambda functions with SAM...
   Build successfull.

   /path/to/.aws/build
   ```

AWS builder automatically adds the main module (`my_app` in our example) to the lambdas requirements. It enables you to use it as a place for common code.

```python
# content of src.lambda1.app
from my_app.config import Settings
from my_app.models import Batman
```

### Options

Following table contains available customization of builder behavior. You can find example of `pyproject.toml` in [tests/assets/pyproject.toml](https://github.com/aka-raccoon/hatch-aws/blob/main/tests/assets/pyproject.toml).

| Option                | Type                       | Default        | Description                                            |
| --------------------- | -------------------------- | -------------- | ------------------------------------------------------ |
| `template-name`       | `str`                      | `template.yml` | The filename of a SAM template.                        |
| `use-container`       | `bool`                     | `false`        | Make build inside an AWS Lambda-like Docker container. |
| `parameter-overrides` | `array` of `inline tables` |                | Override SAM template parameter                        |

## License

Plugin `hatch-aws` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
