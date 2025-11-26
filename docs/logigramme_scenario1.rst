Création d'un scénario question du centralisé / décentralisé
============================================================

.. mermaid::
    :zoom:

    flowchart TB
        A1[Je vérifie que : <br/> - mes couches sont dans le même SCR <br/> -les dépendances externes sont bien installées]
        A2[J'ai une couche avec les exutoires possibles ?]
        B1[Pour mon scénario, je veux en considérer uniquement certains ?]
        B2[Je sélectionne ceux que je veux considérer]
        A3[Je lance le module *Réseau*]
        C1[J'indique ma couche steu et je coche *entités sélectionnées uniquement*]
        C2[J'indique ma couche steu]
        C3[Je n'indique pas de couche steu]
        A4[- Je renseigne mes couches MNT, bâtiments et routes. <br/> - Je change les valeurs par défaut des paramètres que je connais. <br/> - Je sélectionne la gamme de diamètres gravitaires autorisée. <br/> - J'enregistre vers un fichier. <br/> - J'exécute. ]
        A5[J'obtiens 7 couches]
        A6[Je les regroupe dans un groupe]
        A7[Je veux explorer le prédimensionnement proposé ?]
        D[Je change les styles. <br/> Je regarde les attributs. <br/> J'utilise le module *Profils de canalisations*.]
        A8[Je suis satisfait.e du prédimensionnement ?]
        A1 --> A2
        A2 -- oui --> B1
        B1 -- oui --> B2 --> A3
        B1 -- non --> A3
        A2 -- non --> A3
        A3 --> C1 --> A4
        A3 --> C2 --> A4
        A3 --> C3 --> A4
        A4 --> A5 --> A6 --> A7
        A7 -- oui --> D --> A8
        A7 -- non --> A8
        E["J'édite mes couches routes et bâtiments voire exutoires (ajout/suppression) pour ajuster le prédimensionnement"]
        A9[J'édite ma couche STEU obtenue pour renseigner mes concentrations d'entrées et mes contraintes de rejets pour les différents exutoires. <br/> Pour les paramètres sans contrainte, je laisse à NULL.]
        A10[J'ai une contrainte de surface à respecter pour mes exutoires ?]
        F1[Je créé 1 couche de type polygone où je délimite les surfaces mobilisables]
        F2[Je vérifie que mes points exutoires sont bien dans les surfaces délimitées]
        A11[Je lance le module *Procédés*]
        G1[Je renseigne la couche avec les surfaces disponibles]
        G2[Je laisse vide l'emplacement *surface disponible*]
        A12["Je choisis entre climat *Tempéré* ou *Tropical* (>= 25°C en moyenne annuelle)"]
        A13[J'indique ma couche *STEU*. <br/> Je vérifie que les paramètres ont bien été détectés. <br/> J'exécute.]
        A14[J'obtiens 1 couche filières avec différentes possibilités]
        A15[J'explore/je compare les propositions à l'aide des outils graphiques proposés]
        A16[Pour chaque exutoire, je préselectionne une option parmi celles proposées]
        A17[Plusieurs options/combinaisons me semblent envisageables/pertinentes ?]
        A8 -- oui --> A9 --> A10
        A8 -- pas tout à fait --> E --> A3
        A10 -- oui --> F1 --> F2 --> A11
        A10 -- non --> A11
        A11 --> G1 --> A12
        A11 --> G2 --> A12
        A12 --> A13 --> A14 --> A15 --> A16 --> A17
        H1[Je créé plusieurs scénarios pour cette configuration de réseau]
        H2[Je créé un seul scénario pour cette configuration de réseau]
        A18[Je lance le module *Créer un scénario*]
        A19["Je renseigne le réseau et les filières associées (celles choisies sont à présélectionner). <br/> J'exécute."]
        A20[J'obtiens 1 gpkg avec toutes les composantes de mon scénario pour mieux le comparer aux autres scénarios envisagés par la suite]
        A17 -- oui --> H1 -- pour chaque cas envisagé --> A18
        A17 -- non --> H2 --> A18
        A18 --> A19 --> A20