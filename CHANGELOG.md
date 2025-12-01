# CHANGELOG

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [CalVer](https://calver.org/).

<!--

Unreleased

## version_tag - YYYY-DD-mm

### Added

- awesome feature
- yet another button

### Changed

- every colour is now green

### Removed

- all color that was not green

### Fixed

- that big annoying bug
- and that other one too
-->

## 2025.12.91-beta - 2025-12-01

### Added

- New module: Snap on roads
- New module: Population (uniform distribution)

### Changed

- Roads and buildings module: removed centroid outputs
- Processes and Sewer network modules: inflow concentrations can be given
- Processes module: concentrations are in advanced parameters
- Sewer network module: some parameters are now in the advanced section
- Improved color range for plots

### Removed

- Sewer network module: removed the average population input

### Fixed

- Typos
- Radar plot threshold was not correct in French

## 2025.10.92 - 2025-10-02

### Added

- Plot visualization for treatment train layer: toolbar with 2 buttons (bar & radar plot)
- PyQt6 compatibility (ready for QGIS 4!)
- Processes module: new test
- Documentation menu

### Changed

- Processes module: renamed attributes (P -> TP, coliforms -> e.coli, NO3 -> NO3-N)
- Update translations
- Update metadata: contact email and home page

### Fixed

- Typos
- wetlandoptimizer don't need to be re-installed on every startup
- Proper error message if other ELAN dependencies are not found at startup

## 2025.7.25 - 2025-07-25

### Changed

- update documentation: installation page
- miscellaneous tips

### Fixed

- Sewer network module: fix crash when there is no station in the output network

## 2025.6.25 - 2025-06-25

### Changed

- Bump minimal QGIS version to 3.40

## 2025.6.13 - 2025-06-13

### Added

- CI: Stable versions are uploaded to QGIS official plugin repository

### Changed

- Documentation update

### Fixed

- Only load layers that the user wants to load
- Fixed error on pysewer installation about directory not found

## 2025.5.27 - 2025-05-27

### Added

- New module: Create scenario
- Processes module: add normalized concentrations
- Processes module: add phosphor and coliforms (not mature yet)
- Sewer network module: add roads and buildings to output GeoPackage
- Sewer network module: add 3 new diameters (0.6 m, 0.8 m, 1 m)
- Functional and unit tests

### Changed

- Experimental features are shown only in experimental version
- Updated plugin tags and description
- Processes module: maximum stages number between 1 and 3
- Processes module: keep all treatment chains even if they don't conform to requirements
- Refactorization of how external libraries are installed

### Removed

- Sewer network module: removed inflow trench depth and min trench depth

### Fixed

- Processes module: TKN can be None

## 2025.4.2 - 2025-04-02

### Added

- Official ELAN logo!

### Fixed

- Processes module: fix table column orders
- Processes module: better error message when an objective is NULL

## 2025.3.27 - 2025-03-27

### Fixed

- Processes module: fixed crash on Windows
- Processes module: fill hydraulic loading rate attribute
- Sewer network module: fixed crash on Windows
- Sewer network module: WWTP output layer now has upstream_pe and trench_profile columns back
- Sewer network module: WWTP output layer has TP column removed
- Sewer network module: minor wording changes
- Trench profile module: sewers are visible again with gravity-driven style
- Roads and buildings module: fixed wrong parameter names

## 2025.3.14 - 2025-03-14

### Added

- Sewer network module: symbol for WWTP layer
- Sewer network module: WWTP output layer now has NO3, TN, and TP columns
- Processes module: added stages max, climate, NO3, TN inputs

### Changed

- Trench profile module: GeoPackage output for the layers and their styles
- Processes module: parallelization of computation
- Use Calendar Versioning (CalVer)
- Minimum needed QGIS version is now 3.36.0
- CI/CD pipelines for automatic deployment and release notes on GitLab

## 0.16.0 - 2025-02-25

### Added

- French translations
- Processes module: new output attribute hydraulic load rate
- Processes module: possibility to cancel the process
- Globally more checks for input layers in modules (CRS, areas, progress)
- Sewer network module: possibility to cancel the process

### Changed

- English is now the official language
- Sewer network module: available surface is now an optional polygon layer
- Trench profile module: 3D sewer pipe gravity and diameter styles are the same as 2D sewer pipe styles
- Python API factorization (class and module names)
- Update pre-commit hooks

### Removed

- Unused attributes in many output layers

### Fixed

- Sewer network module: mean trench depth value is corrected
- Processes module: white text for red background in attribute table

## 0.15.0 - 2024-12-16

### Added

- Module Profil de canalisations : canalisations 3D
- Module Profil de canalisations : altitude des pompes

### Changed

- Mise à jour de pysewer
- Renommage du module Extraction en "Routes et bâtiments"
- Module Population : sortie en géométrie Point
- Module Population : nombre d'habitants en chiffre flottant
- Module Profil de canalisations : canalisations en refoulement le long du terrain

### Removed

- Suppression du champ private_pumps de la table info_sewer (sommé avec pumping stations)

### Fixed

- Module Réseau : correction du calcul de hauteur relevées


## 0.14.0 - 2024-10-22

### Added

- Module Profil de canalisations : créer des couches utiles à la visualisation des profils de profondeur
- Module Population : attribuer un nombre d'habitant à des polygones
- Module Procédé : refactorisation complète pour utiliser la librairie wetlandoptimizer
- Module Réseau : style sens d'écoulement
- Module Réseau : attribut total_static_head pour les stations de relevage et de pompage
- Module Réseau : lancer le module seulement sur les entités sélectionnées
- Module Réseau : ajout de 4 champs de concentrations de polluants à la couche de sortie WWTP
- Module Extraction : nouvelles couches de sortie pour investigation (surfaces des bâtiments + bâtiments fusionnés + leurs centroïdes)
- Familles de modules : Exploration des résultats, Préparation des données, Traitements

### Changed

- Module Extraction : délimitation de la zone d'extraction à partir d'une couche polygone
- Module Réseau : mise à jour de la version de pysewer
- Module Réseau : style 0 du style diamètres

### Removed

- Module Réseau : style altitude

### Fixed

- Module Réseau : correction de la sélection des attributs de couche
- Module Réseau : pysewer a fixé le bug des sous-graphes
- Module Réseau : assigner un SCR persistant aux couches de sortie
- Module Réseau : pré-processing du MNT pour éviter des crash de noData ou de bandes de couleurs
- Module Réseau : les catégories du style flux de pointe sont calculées et non plus fixées en dur


## 0.13.1 - 2024-07-09

### Changed

- Module Réseau : Precision SCR identiques et ajout aide dans la fenêtre du traitement

## 0.13.0 - 2024-07-05

### New

- Module Réseau : styles profondeur, altitude, sous-réseaux
- Module Réseau : compatibilité multi-formats de couche en entrée
- Module Réseau : gestion des profils de bâtiment (nombre d'habitant)
- Module Réseau : gestion des profils de bâtiment (nombre d'habitant)
- Création du module Extraction (pour extraire bâtiments et routes de OpenStreetMap)
- Installation de pysewer via un menu des paramètres (multiplateforme)

### Changed

- Module Réseau : style gravitaire par défaut
- Module Réseau : ordre de chargement des couches

### Removed

- Code et modules obsolètes (SQL)

## 0.12.0 - 2024-04-05

### New

- Ajout du module de calcul de réseaux (via pysewer)

## 0.11.1 - 2023-12-08

### New

- Ajout du module de calcul de bassins versants urbains (via pysheds)

### Changed

- Ajout de la documentation du module de calcul de bassins versants urbains

## 0.10.1 - 2023-04-13

### Changed

- Doc : utiliser Postgresql 15

### Fixed

- Module Hydraulique : message d'erreur si pas de données dans le projet (#133)
- Module Hydraulique : suppression de la contrainte not null des numero de sbv (seront mis à la main) (#133)

## 0.10.0 - 2023-05-30

- Fonctions coût de test
- Compatibilité base de données France métropolitaine
- Module hydraulique INSA indépendant

## 0.9.0 - 2022-12-22

- Schéma "metadata" pour la gestion des projets (#106)
- Création et suppression de projet via les processing ELAN (#107)
- Module Réutilisation : identification des zones éligibles pour l'installation d'un Procédé (#103)
- Module Hydraulique (pré-traitement) : calcul des bassins versants topologiques, à partir du MNT (#99)
- Module Hydraulique : calcul des bassins versants à partir de points d'entrée dans le réseau (#99, #100)
- Module Hydraulique : panneau de seuil de perméabilité (#88)
- Module Hydraulique : quantifier les volumes par bassin versant (#98), pour l'instant un champ nb_habitant dans la table

## 0.8.1 - 2022-11-10

- Ajout des statistiques descriptives du réseau

## 0.7.0 - 2022-11-08

- Ajout de la gestion multi projets
- Ajout de l'initialisation de bdd locale via python

## 0.6.0 - 2022-10-10

- Maturation du module Réseau
- Gestion de plusieurs méthodes d'optimisation
- Gestion de l'altitude et des pentes

## 0.5.0 - 2022-07-12

- Ajout d'un module dédié au pré-processing du module réseau
- Possibilité d'arrêter le calcul de tracé du module réseau en cours
- Passage à pylint pour la qualité de code

## 0.4.1 - 2022-04-06

- Fix bug

## 0.4.0 - 2022-04-04

- Ajout d'une première version du module procédé

## 0.3.0 - 2022-03-14

- Ajout de nouvelles méthodes d'optimisation du module réseau

## 0.2.0 - 2021-11-18

- Ajout du module réseau avec pgrouting

## 0.1.0 - 2021-08-31

- Première release generée à partir du [QGIS Plugin templater](https://oslandia.gitlab.io/qgis/template-qgis-plugin/).
- Stockage des résultats de l'étude préliminaire dans un sous-répertoire dédié.
