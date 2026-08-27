# How to contribute to Elan?

First off, thanks for taking time to contribute!

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions. :tada:

We will try to give you a prompt feedback, review and merge your MR.

If you are making major changes to the code, you are encouraged to open an issue first to discuss the best way to integrate your code.

## Table of Contents

- [How to contribute to Elan?](#how-to-contribute-to-elan)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [I Have a Question](#i-have-a-question)
  - [I Want To Contribute](#i-want-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Enhancements](#suggesting-enhancements)
    - [Making Changes](#making-changes)
      - [Tooling](#tooling)
      - [CI/CD jobs](#cicd-jobs)
        - [Check and correct automatically CI issues with pre-commit](#check-and-correct-automatically-ci-issues-with-pre-commit)
      - [Tests](#tests)
      - [Documentation](#documentation)

## Code of Conduct

This project does not yet have Code of Conduct. :construction:

## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://elan-gis.org).

Before you ask a question, it is best to search for existing [Issues](https://gitlab.com/elan7835313/elan/-/work_items?sort=created_date&state=opened&first_page_size=20) that might help you. If you wish to report a bug, please refer to the section [Reporting Bugs](#reporting-bugs).

If you still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://gitlab.com/elan7835313/elan/-/work_items/new?type=Issue&initialCreationContext=list-route).
- Provide as much context as you can about what you're running into.
- Provide elan and QGIS versions.

## I Want To Contribute

### Reporting Bugs

If you find a bug, please report it by [creating an issue](https://gitlab.com/elan7835313/elan/-/work_items/new?type=Issue&initialCreationContext=list-route) and using the bug report template that can be found by selecting the appropriate template in the issue window.

### Suggesting Enhancements

If you have an idea for an enhancement, please open an issue with the following details:

- A clear and descriptive title.
- A detailed description of the proposed enhancement.
- Any relevant use cases or examples.
- Why you believe this enhancement would be beneficial.

### Making Changes

We welcome pull requests for bug fixes, new features, and documentation improvements. To submit a pull request, you must be member of the project and follow these steps:

1. Create an issue
2. Select create a merge request and create a dedicated branch
3. Make your changes
4. Commit your changes
5. Push the branch
6. Mark your merge request as ready

To be added as a member of the *elan* project, please [contact the owners of the repository](mailto:elan.support@listes.inrae.fr)

Elan has been developed using the following coding standards, please follow theses guidelines to ensure consistency and quality across the codebase:

#### Tooling

This project is configured with the following tools:

- [Black](https://black.readthedocs.io/en/stable/) to format the code without any existential question

- [iSort](https://pycqa.github.io/isort/) to sort the Python imports

Code rules are enforced with [pre-commit](https://pre-commit.com/) hooks.

Static code analysis is based on: [PyLint](https://pylint.readthedocs.io/en/stable/index.html).

#### CI/CD jobs

Each MR will execute a CI pipeline. The CI will check:
 - the syntax and the format of the code
 - that the tests pass

In order for a MR to be merged, the CI must pass completely. However, it is possible to ask for a broad review before the CI passes (but an in-depth review will need everything to be green beforehand).

Through the following sections, **we will see how to check and correct them beforehand**.

##### Check and correct automatically CI issues with pre-commit

Pre-commit is a tool that allows to run a set of checks and corrections before each commit (and push). This tool is not mandatory but highly recommended to simplify the development workflow.

With the pre-commit configuration, the following checks and corrections are made:
 - pyupgrade (corrects directly)
 - black (formats directly)
 - isort (formats directly)
 - pylint
 - large files
 - trailing whitespace
 - TOML/XML/YAML syntax

To use it, you must install the development dependencies:

`$ pip install requirements/development.txt`

Then you have to install pre-commit:

`$ pre-commit install`

If you want to commit without pre-commit verifications, you need to add the `-n` (or `--no-verify`) flag to the command `git commit`.

#### Tests

The tests are executed using pytest.

Pytest plugins used are:
 - pytest-cov for coverage results
 - pytest-mock for mocking Python objects
 - [pytest-qgis](https://github.com/GispoCoding/pytest-qgis) to facilitate QGIS initialization for tests

To launch the tests locally, you must run pytest from the root of the repository:

`$ pytest`

To launch a specific test:

`$ pytest tests/test_wetland_process.py::test_wetland_process_without_surface`

To launch tests matching a regular expression:

`$ pytest -k sewer_network`

#### Documentation

The documentation is generated using Sphinx and is automatically generated through the CI and published on Pages.

To update the `pot` and `po` translations files:

```bash
cd docs/
sphinx-build -b gettext . locales/pot \&\& sphinx-intl update -l en
```
Then use a software like [`poedit`](https://poedit.net) to write the translations.

To build the documentation with all languages:

```bash
cd docs/
./multi\_lang\_build.sh . ./\_build $(pwd)/\_build
```

and open the file `./docs/\_build/index.html`
