Panorama question du centralisé / décentralisé
========================================================

.. mermaid::
    :zoom:

    flowchart TB
        A[<a href="https://elan-gis.org/preparation.html#routes">Routes et bâtiments</a>]
        B[<a href="https://elan-gis.org/preparation.html#population">Population</a>]
        C[Projection]:::class1
        D[<a href="https://elan-gis.org/scenario_prb1.html#reseau">Réseau</a>]:::class3
        B:::class3 --centroïdes--> C --centroïdes projetés--> D
        B --centroïdes--> D
        F@{ shape: circle, label: <a href="https://elan-gis.org/preparation.html#_entrees_reseau">MNT</a> }
        G@{ shape: circle, label: <a href="https://elan-gis.org/preparation.html#_entrees_reseau">exutoires</a> }
        H@{ shape: circle, label: <a href="https://elan-gis.org/preparation.html#_entrees_reseau">routes</a> }
        I@{ shape: circle, label: <a href="https://elan-gis.org/preparation.html#_entrees_reseau">bâtiments</a> }
        A:::class1 --polygones--> I:::class0 --> B
        A --> H:::class0 --> D
        F:::class0 --> D
        G:::class0 --> D
        J[<a href="https://elan-gis.org/scenario_prb1.html#visualisation-profils">Profils de canalisations</a>]:::class1
        K[<a href="https://elan-gis.org/scenario_prb1.html#procedes">Procédés</a>]:::class3
        L[<a href="https://elan-gis.org/scenario_prb1.html#creer-scenario">Créer un scénario</a>]:::class3
        M[Plots]:::class3
        N@{ shape: circle, label: <a href="https://elan-gis.org/scenario_prb1.html#sorties_reseau">réseau pré <br/> dimensionné</a> }
        D --> N:::class2
        N --canalisations--> J
        N --STEU--> Q --> K
        K --filières--> M 
        N --> L
        O@{ shape: framed-circle, label: "Stop" }
        P@{ shape: hex, label: <a href="https://elan-gis.org/scenario_prb1.html#selection">Sélection</a> }
        M --> P:::class2 --> L
        L -- objet scénario --> O
        Q@{ shape: hex, label: <a href="https://elan-gis.org/scenario_prb1.html#set_concentrations">Précision C_in <br/> et C_obj</a> }
        classDef class0 fill:##E6E6FA, stroke:#9932CC
        classDef class1 fill:#FFE4B5, stroke:#FFE4B5
        classDef class2 fill:#F0FFF0, stroke:#2E8B57
        classDef class3 fill:#FFF5EE, stroke:#FF8C00

**Légende**

.. mermaid::

    flowchart TB
        A[facultatif]:::class1
        C[obligatoire]:::class3
        B@{ shape: rect, label: "relatif aux entrées" }
        B:::class0
        D@{ shape: rect, label: "relatif aux sorties" }
        D:::class2
        P@{ shape: hex, label: "action utilisateur" }
        P:::class4
        A ~~~ C ~~~ P
        B ~~~ D ~~~ P
        classDef class0 fill:##E6E6FA, stroke:#9932CC
        classDef class1 fill:#FFE4B5, stroke:#FFE4B5
        classDef class2 fill:#F0FFF0, stroke:#2E8B57
        classDef class3 fill:#FFF5EE, stroke:#FF8C00
        classDef class4 fill:#f8f8ff , stroke:#000000