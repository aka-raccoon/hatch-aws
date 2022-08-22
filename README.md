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

### Options

Following table contains available customization of builder behavior. You can see example of `pyproject.toml` in [tests/assets/pyproject.toml](https://github.com/aka-raccoon/hatch-aws/blob/first_release/tests/assets/pyproject.toml).

| Option                | Type                       | Default        | Description                                            |
| --------------------- | -------------------------- | -------------- | ------------------------------------------------------ |
| `template-name`       | `str`                      | `template.yml` | The filename of a SAM template.                        |
| `use-container`       | `bool`                     | `false`        | Make build inside an AWS Lambda-like Docker container. |
| `parameter-overrides` | `array` of `inline tables` |                | Override SAM template parameter                        |

## License

Plugin `hatch-aws` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
