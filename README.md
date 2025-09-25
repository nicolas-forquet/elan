# ELAN - QGIS Plugin

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pylint](https://client-projects.pages.oslandia.io/2010_09_inrae_assainissement/lint/pylint.svg)](https://client-projects.pages.oslandia.io/2010_09_inrae_assainissement/lint/)

## Plugin

Outil SIG d'aide à la décision pour la conception de réseaux de traitements des eaux usées.

Le plugin se subdivise en les modules suivants :
* Procédé
* Hydraulique
* ACV
* Économique
* Réseau
* Réutilisation

Le plugin fonctionne pour QGIS>=3.16.

## Tooling

This project is configured with the following tools:

- [Black](https://black.readthedocs.io/en/stable/) to format the code without any existential question
- [iSort](https://pycqa.github.io/isort/) to sort the Python imports

Code rules are enforced with [pre-commit](https://pre-commit.com/) hooks.  
Static code analisis is based on: PyLint

See also: [contribution guidelines](CONTRIBUTING.md).

## CI/CD

Plugin is linted, tested and packaged with GitLab.

## Documentation

The documentation is generated using Sphinx and is automatically generated through the CI and published on Pages.

- documentation=https://elan7835313.gitlab.io/elan/

To update the `po` translations files:

```bash
cd docs/
sphinx-intl update -l en
```

To build the documentation with all languages:

```bash
cd docs/
./multi_lang_build.sh . ./_build $(pwd)/_build
```

and open the file `./docs/_build/index.html`

----

## License

Distributed under the terms of the `GPLv2+` license.
