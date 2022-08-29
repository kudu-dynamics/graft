# Graft

---

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

---

graft is a Python toolkit for working with different graph implementations.

- [docs/synapse.md](docs/synapse.md)

## Installation
```shell
$ pip install poetry

$ poetry install

# or

$ pip install -e .
```

Optional dependencies can be installed using the extras syntax.
``` shell
$ poetry install -E logging

# or

$ pip install -e .[logging]
```

## Usage
Tool endpoints will be added here as they are developed.

``` shell
# List all of the available tools.
$ python -m graft
```

``` shell
# Prints the schema and prompts the user to upload to a local Dgraph instance.
$ python -m graft.tools.schema
```

## Development
A test suite is available in the tests directory.

Each file named `test_{filename}` will be considered part of the test suite.

They are found and run with pytest.

```shell
$ py.test

# or

$ poetry run pytest
```

Configuration is found in the `pytest.ini` file.

### Coverage (`pytest-cov`)
The coverage information is retrieved by regex in the GitLab CI (check `.gitlab-ci.yml`).

### Formatting (`pytest-black`)
The code for graft is handled by the
[black](https://github.com/python/black) Python code formatter.

``` shell
$ black .
```

### Code Style (`pytest-flake8`)
Code is checked against the [flake8](http://flake8.pycqa.org/en/latest/) tool
as part of the test suite.

Add `# noqa` to the end of lines that should not be linted.

Add `# pragma: no cover` to the end of blocks/statements that should not be covered.

Distribution Statement "A" (Approved for Public Release, Distribution
Unlimited).
