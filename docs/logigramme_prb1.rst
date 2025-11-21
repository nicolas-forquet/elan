Logigramme question du centralisé / décentralisé
=================================================

.. mermaid::
    :zoom:

    flowchart TB
        A[<a href="https://elan-gis.org/preparation.html#routes">Routes et bâtiments</a>]
        B[Population]:::class3
        C[Projection]:::class3
        D[Réseau]:::class3
        E[Grouping]:::class1
        E --polygones groupés--> B
        B --centroïdes--> C --centroïdes projetés--> D
        F@{ shape: circle, label: "MNT" }
        G@{ shape: circle, label: "exutoires" }
        H@{ shape: circle, label: "routes" }
        I@{ shape: circle, label: "bâtiments" }
        A:::class1 --polygones--> I --> B
        I:::class0 --> E
        A --> H:::class0 --> D
        F:::class0 --> D
        E --> G:::class0 --> D
        J[Profils de canalisations]:::class1
        K[Procédés]:::class3
        L[Créer un scénario]:::class3
        M[Plots]:::class3
        N@{ shape: circle, label: "réseau pré <br/> dimensionné"}
        D --> N:::class2
        N --canalisations--> J
        N --STEU--> Q --> K
        K --filières--> M 
        N --> L
        O@{ shape: framed-circle, label: "Stop" }
        P@{ shape: hex, label: "Sélection" }
        M --> P:::class2 --> L
        L -- objet scénario --> O
        Q@{ shape: hex, label: "Précision C_in <br/> et C_out" }
        classDef class0 fill:##E6E6FA, stroke:#9932CC
        classDef class1 fill:#FFE4B5, stroke:#FFE4B5
        classDef class2 fill:#F0FFF0, stroke:#2E8B57
        classDef class3 fill:#FFF5EE, stroke:#FF8C00