<div align="center">
    <a href="https://gitlab.com/elan7835313/elan">
        <img alt="elan logo" src="./docs/_static/logo.png" height="175">
    </a>
</div>

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat\&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit\&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pylint](https://client-projects.pages.oslandia.io/2010\_09\_inrae\_assainissement/lint/pylint.svg)](https://client-projects.pages.oslandia.io/2010\_09\_inrae\_assainissement/lint/)

## Elan QGIS plugin

Elan is a QGIS decision-support plugin that aims to facilitate integrated urban water management by nature-based solutions currently under development.

The user can create and compare different urban water management scenarios (wastewater and stormwater) to support informed decision making.

## Features

The plugin includes several modules:

- `Roads and buildings`, `Population` and `RoadProjection` to prepare the geographical data

- `Sewer network` and `Processes` to investigate and presize scenarios

- `Longitudinal sewer profile` to better visualize sewer pre-sizing

- `Create a scenario` to create a scenario item that can be further compare to others

And customized plots to better compare presized treatment train options.

## For whom ?

Urban water professionals and stakeholders with a GIS skill

## For what ?

* To connect an area with no sanitation network (wastewater)

* To reduce existing stormwater overflows (stormwater)

* Find the optimum degree of decentralization

**Disclaimer**

At this stage of development, only the wastewater issue can be addressed by Elan.

## When to use it ?

At an early stage in urban water management projects to explore multiple scenarios based on nature-based solutions and pre-select the ones to consider in the preliminary design phase. It can be part of a participatory process.

## How to use it ?

On QGIS >=3.40

Following the steps explained in the online documentation : elan-gis.org

## License

The project is developped under the terms of the `GPLv2+` license.

## Development and contribution

Development currently involves :

<div align="center">
  <a href="https://reversaal.lyon-grenoble.hub.inrae.fr/">
    <img alt="reversaal logo" src="./docs/_static/reversaal.jpg" height="100">
  </a>
</div>

<div align="center">
  <a href="https://oslandia.com/">
    <img alt="oslandia logo" src="./docs/_static/oslandia.png" height="100">
  </a>
</div>

It is an open project ! Good to know if you want to help :

### Tooling

This project is configured with the following tools:

- [Black](https://black.readthedocs.io/en/stable/) to format the code without any existential question

- [iSort](https://pycqa.github.io/isort/) to sort the Python imports

Code rules are enforced with [pre-commit](https://pre-commit.com/) hooks.  

Static code analisis is based on: PyLint

See also: [contribution guidelines](CONTRIBUTING.md).

### CI/CD

Plugin is linted, tested and packaged with GitLab.

### Documentation

The documentation is generated using Sphinx and is automatically generated through the CI and published on Pages.

- documentation= https://elan-gis.org/

To update the `pot` and `po` translations files:

```bash
cd docs/
sphinx-build -b gettext . locales/pot \&\& sphinx-intl update -l en
```

To build the documentation with all languages:

```bash
cd docs/
./multi\_lang\_build.sh . ./\_build $(pwd)/\_build
```

and open the file `./docs/\_build/index.html`

## Citation

If you use elan, please cite the following ressource :

> Gabrielle Favreau, Nicolas Forquet, Jacky Volpes, Sophie Aubier, Pascal Molle (laste update mentionned). Elan : a QGIS decision-support plugin for integrated urban water management by nature-based solutions. https://elan-gis.org/

## Acknowledgments

### Open source research projects integrated to elan

* **pysewer**, Python library developed by UFZ : https://git.ufz.de/despot/pysewer

> Sanne et al., (2024). Pysewer: A Python Library for Sewer Network Generation in Data Scarce Regions. Journal of Open Source Software, 9(104), 6430, https://doi.org/10.21105/joss.06430

* **wetlandoptimizer**, Python package developed by REVERSAAL (INRAE) : https://forgemia.inra.fr/reversaal/nature-based-solutions/caribsan/wetlandoptimizer

> Legeai et al. (2025). Regression-Based Design Optimization of French Treatment Wetlands. Water Science and Technology, wst2025071, https://doi.org/10.2166/wst.2025.071.

* **pysheds**, Python Library developed by UT Austin : https://github.com/mdbartos/pysheds

> Bartos et al. (2020). Pysheds: simple and fast watershed delineation in Python. Zenodo repository, 10.5281/zenodo.3822494.

### QGSI plugins required for elan 

* **DataPlotly** : https://github.com/ghtmtt/DataPlotly

### Funding 

This project is made possible through funding from :

<div align="center">
  <a href="https://ofb.gouv.fr/">
    <img alt="ofb logo" src="./docs/_static/ofb.png" height="100">
  </a>
</div>

<div align="center">
  <a href="https://www.caribsan.eu/">
    <img alt="caribsan logo" src="./docs/_static/caribsan.png" height="100">
  </a>
</div>

<div align="center">
  <a href="https://www.afd.fr/fr">
    <img alt="afd logo" src="./docs/_static/afd.png" height="100">
  </a>
</div>

<div align="center">
  <a href="https://www.eaurmc.fr/">
    <img alt="rmc logo" src="./docs/_static/rmc.png" height="100">
  </a>
</div>

<div align="center">
  <a href="https://eau-grandsudouest.fr/">
    <img alt="adour logo" src="./docs/_static/adour.png" height="100">
  </a>
</div>