Préparation des données question du centralisé / décentralisé
===============================================================

.. mermaid::
    :zoom:

    mermaid.initialize({
        theme: 'neutral',
    });

    flowchart TB
        A["J'ai les couches raster (MNT) et vecteurs (routes et bâtiments) nécessaires ?"]
        B1[Je suis en contexte français ?]
        B2[J'utilise *BD TOPO extractor* pour récupérer les routes et les bâtiments]
        B3[Je télécharge le MNT à 5m sur *RGE Alti*]
        C[Je sais où trouver les couches nécessaires dans mon contexte local ?]
        D1[Je cherche sur *alaska.edu* pour trouver du MNT à 12,5m]
        D2[Ma zone est située dans l'hémisphère Sud ?]
        D3[Je télécharge mes bâtiments sur *OpenBuildings*]
        E1[Je créé une couche polygone qui délimite ma zone d'étude]
        E2[J'utilise le module *Routes et bâtiments* d'Elan pour récupérer]
        E3[mes routes]
        E4[mes routes et mes bâtiments]
        F1[Mon MNT est constitué d'une seule dalle ?]
        A --> F1
        A -- non --> B1
        B1 -- oui --> B2 --> B3 --> F1
        B1 -- non --> C -- oui --> F1
        C -- non OU oui en partie --> D1 --> D2
        D2 -- oui --> D3 --> E2 --> E3 --> F1
        D2 -- non --> E1 --> E2 --> E4 --> F1
        G[J'utilise l'outil *Fusion* de GDAL]
        F2[Mon MNT a des pixels manquants ?]
        F3["Mes couches vecteurs retranscrivent bien la réalité du terrain (bâtiments à raccorder, chemins autorisés) ?"]
        H[J'édite manuellement mes couches : ajout/suppression de routes et bâtiments en m'aidant éventuellement d'images satellitaires]
        F4[Toutes mes couches sont dans le même SCR ?]
        I1[Je définis le SCR du projet à partir du MNT]
        I2[Je projette mes couches routes et bâtiments dans ce SCR avec l'outil Reprojection d'une couche de vecteur de QGIS]
        F5[J'ai connaissance des exutoires possibles ?]
        F1 -- oui --> F2
        F1 -- non --> G --> F2
        F2 -- oui --> F3
        F2 -- non --> F3
        F3 -- oui --> F4
        F3 -- non --> H --> F4
        F4 -- oui --> F5
        F4 -- non --> I1 --> I2 --> F5
        F6[Je créé une couche point dans le SCR du projet avec tous les exutoires possibles]
        J[Je continue : Elan positionnera l'exutoire sur le pixel le plus bas de ma zone]
        F7["Je vérifie que toutes mes entités (routes, bâtiments, exutoires) sont sur le MNT"]
        F8["Je connais la population à raccorder (nombre total d'habitants) ?"]
        K[Je fais des recherches]
        F9["Une répartition uniforme de la population me convient (nombre moyen d'habitant/bâtiment) ?"]
        L["J'utilise le module *Population (répartition surfacique)* pour avoir un nombre ajusté d'habitants par bâtiment"]
        M1[J'estime un nombre d'habitant/bâtiment]
        M2["J'utilise le module *Population (répartition uniforme)*"]
        F10[J'obtiens une couche de bâtiments sous forme de centroïdes avec un attribut population]
        F11["Je vérifie que mes centroïdes sont bien dans le bon SCR (SCR du projet)"]
        F12[Je connais mes contraintes de dimensionnement ? <br/> - consommation moyenne d'eau/habitant/jour <br/> - profondeur min et max autorisées <br/> - diamètres possibles]
        N[Je fais des recherches/des hypothèses]
        F13[Je suis prêt.e à créer un scénario]
        F5 -- oui --> F6 --> F7
        F5 -- non --> J --> F7
        F7 --> F8
        F8 -- oui --> F9
        F8 -- non --> K --> F9
        F9 -- oui --> M1 --> M2 --> F10
        F9 -- non --> L --> F10
        F10 --> F11 --> F12
        F12 -- oui --> F13
        F12 -- non --> N --> F13
