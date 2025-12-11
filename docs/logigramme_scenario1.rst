.. _flowchart-scenario:

Création d'un scénario question du centralisé / décentralisé
============================================================

**Préalable :**
* Avoir préparé vos données en vous aidant du :ref:`logigramme précédent <_flowchart-prepa>`
* Installer *pysewer*, *wetlandoptimizer* et *DataPlotly* (voir :ref:`la page Installation, rubrique dépendances externes <_dependances>`)
* Recueillir les informations suivantes pour le prédimensionnement du réseau :
    - consommation journalière d'eau par personne (en L)
    - profondeurs minimum et maximum (pour les canalisations) envisageables dans votre contexte
    - diamètres usuels pour les canalisations
* Recueillir les informations suivantes pour le prédimensionnement des filières de traitement :
    - les concentrations usuelles d'un effluent domestique dans votre contexte (MES, DCO, DBO5, NTK, TN, N-NO3, TP, e.coli)
    - les niveaux de rejet imposés par votre réglementation (MES, DCO et DBO5)

Ce logigramme vise à vous guider à la création de scénarios sur votre zone d'étude.

Il est interactif : vous pouvez zoomer et cliquer sur certains blocs pour être renvoyé aux rubriques correspondantes dans la documentation. 

.. mermaid:: create_scenario_flowchart.mmd
    :zoom: