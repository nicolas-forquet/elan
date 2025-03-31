.. _prb1:

Création d'un scénario pour la question du centralisé / décentralisé
=====================================================================

La création d'un scénario pour la question du centralisé / décentralisé implique trois temps :

**1. Tracer un réseau d'assainissement.**

**2. Pré-dimensionner les filières de traitement pour les stations.**

**3. Pré-sélectionner une filière pour chaque station.**

Pour une même zone, vous pouvez créer successivement autant de scénarios que vous le souhaitez.

Étape 1 : Tracer le réseau d'assainissement (module ``Réseau``)
-----------------------------------------------------------------

Préalable
^^^^^^^^^^

1. Avoir installé **la librairie pysewer** comme expliqué dans :ref:`Installation des dépendances <dependances>`.

2. Disposer de **4 couches géographiques** :

* ``STEU`` : couche vecteur qui contient l'ensemble des **emplacements envisagés comme exutoires** (station de traitement des eaux usées existante ou projet possible), type : *point*.

* ``bâtiments`` : couche vecteur qui rassemble les **bâtiments à raccorder**, type : *point* (centroïdes des bâtiments). 

* ``routes`` : couche vecteur indiquant les **routes empruntables** pour le raccordement, type : *ligne*.

* ``MNT`` : couche raster (.tif, .asc, .vrt) du **modèle numérique de terrain** de la zone d'intérêt.

.. attention::
   **Les 4 couches doivent être dans le même SCR (système de coordonnées de référence).**

Si vous ne disposez pas de ces couches, vous pouvez vous rendre à la page :ref:`Obtention et préparation des données géographiques <preparation>`
pour quelques astuces et explications.

Utilisation du module ``Réseau``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Chercher ``ELAN`` dans la boîte à outils de traitements et sélectionner ``Réseau``.

.. image:: _static/start-reseau.png
    :width: 251

.. tip::
    Pour afficher le panneau ``Boîte à outils de traitements`` s'il n'apparaît pas dans votre espace de travail : *Vue* - *Panneaux* - *Boîte à outils de traitements*.

.. image:: _static/boite-outils.png
     :width: 633

2. **Renseigner les 4 couches géographiques**. 

.. note::
    Pour les exutoires, vous pouvez sélectionner au préalable celui ou ceux que vous souhaiter considérer parmi l'ensemble des possibilités envisagées puis cocher *Entités sélectionnées uniquement* dans le module.

Si le nombre d'individus par bâtiment est connu et renseigné dans un attribut (*population* par exemple), 
l'indiquer dans l'encart mis en évidence. A défaut, un nombre moyen d'individus par bâtiment sera considéré.

.. image:: _static/couches-reseau.png
    :width: 677

3. Faire coulisser l'ascenseur et **ajuster les différents paramètres** (encart 5) afin que le pré-dimensionnement du réseau soit le plus adapté à votre contexte : 

* ``nombre moyen de personnes par foyer`` : à renseigner dans le cas où la population n'est pas discrétisée à l'échelle du bâtiment.

* ``volume moyen d'eaux usées produit par jour par personne`` : [m3].

* ``coefficient de pointe journalier`` : [m3/j].

* ``pente minimale permettant l'autocurrage`` : [m/m].

* ``profondeur max autorisée de canalisation`` : [m], dépend du contexte géologique.

* ``profondeur min autorisée de canalisation`` : [m], généralement conditionnée par le risque de gel.

* ``rugosité canalisation`` : [mm], dépend du matériau utilisé pour les canalisations.

* ``diamètre autorisé sous pression`` : [m], un seul diamètre autorisé.

* ``diamètres autorisés en gravitaire`` : [m], à choisir parmi les options proposées (0.1, 0.15, 0.2, 0.25, 0.3 et 0.4). Les 6 options peuvent être considérées ou seulement une partie d'entre elles.

4. Indiquer un emplacement et un nom pour la couche .gpkg en sortie (bulle 6) puis exécuter (bulle 7).

.. image:: _static/entrees-reseau.png
    :width: 682

5. Après exécution du module, vous disposez de **1 fichier au format .gpkg qui contient 5 couches** :

* ``STEU`` (carré jaune) : couche de type *point* avec le ou les exutoires considérés pour la simulation. 

* ``Stations de relevage`` (triangle vert) : couche de type *point* qui contient les stations de relevage du réseau d'assainissement pré-dimensionné.

* ``Stations de pompage`` (triangle rouge) : couche de type *point* qui contient les stations de pompage du réseau d'assainissement pré-dimensionné (stations privées et non privées).

* ``Canalisations`` : couche de type *ligne* qui contient les canalisations pré-dimensionnées.

* ``Informations sur le réseau`` : couche non géométrique qui regroupe différentes métriques sous forme d'attributs.

.. _attributs-reseau:

**Chaque couche vecteur est caractérisée par des attributs.**

* ``STEU`` : *altitude terrain* [m], *coordonnées gps* (identifiant unique pour chaque exutoire), *débit de pointe* [m3/j], *débit moyen journalier* [m3/j], *habitants raccordés* [nb], *profondeur tranchée* [m], *profondeur canas entrantes* [m], *diamètres entrants* [m].

.. note::
    En sortie de module ``Réseau``, la couche STEU compte aussi des attributs non renseignés : *niveau rejet MES* [mg/L], *niveau rejet DBO5* [mg/L], *niveau rejet NTK* [mg/L], *niveau rejet DCO* [mg/L], *niveau rejet NO3* [mg/L], *niveau rejet TN* [mg/L]. Ces attributs sont à renseigner manuellement 
    pour chaque exutoire selon vos contraintes de rejet. Ils servent d'entrées pour le module ``Procédés``. Certains peuvent être renseignés à *NULL*.

* ``Stations de relevage`` : *altitude terrain* [m], *débit de pointe* [m3/j], *débit moyen journalier* [m3/j], *habitants raccordés* [nb], *profondeur canas entrantes* [m], *charge hydrostatique* [m].

* ``Stations de pompage`` : *altitude terrain* [m], *débit de pointe* [m3/j], *débit moyen journalier* [m3/j], *habitants raccordés* [nb], *profondeur canas entrantes* [m], *charge hydrostatique* [m].

* ``Canalisations`` : *longueur* [m], *profil de terrain* [liste de points échantillonnés tous les 10 m], *avec pompe* [booléen], *sous pression* [booléen], *profils de canalisations* [liste de points échantillonnés tous les 10 m], *profondeur moyenne tranchée* [m], *diamètre* [m], *débit de pointe* [m3/j], *coordonnées STEU* [identifiant STEU exutoire].

* ``Informations sur le réseau`` : *nombre bâtiments* [nb], *longueur réseau sous pression* [mètre linéaire], *longueur réseau gravitaire* [mètre linéaire], *nombre stations pompage* [nb], *nombre stations relevage* [nb], *date simulation* [datetime].

**Plusieurs styles sont proposés pour la couche** ``Canalisations``.

* **Diamètres** : symbologie catégorisée sur l'attribut *diamètre* pour visualiser la répartition des diamètres au sein du réseau.

* **Débit de pointe** : symbologie catégorisée sur l'attribut *débit de pointe* pour visionner la variation du débit de pointe selon les tronçons réseau.

* **Gravitaire** : symbologie catégorisée sur l'attribut *sous pression* pour distinguer facilement les sections gravitaires des sections pressurisées. Il s'agit du style par défault en sortie de module ``Réseau``.

* **Profondeur** : symbologie catégorisée sur l'attribut *profondeur moyenne tranchée* pour mieux visualiser les variations de profondeur au sein du réseau.

* **Sens d'écoulement** : symbologie avec flèches pour mieux appréhender le sens d'écoulement à l'intérieur du réseau.

* **Sous-réseaux** : symbologie catégorisée sur l'attribut *coordonnées STEU* pour bien identifier les différents réseaux dans le cas de figure où la zone est raccordée à plusieurs stations (gestion décentralisée).

.. attention::
    Si, pour enregistrer les sorties de simulation, vous passez par un couche temporaire que vous enregistrez ensuite, les mises en forme proposées (symbologies, styles, noms des couches) ne seront pas conservées.
    Seul le passage par *Enregistrer un fichier* lors du lancement du module et l'enregistrement dans votre projet QGIS permet de les conserver.

Application à l'exemple de :ref:`Petite-Anse <petite-anse>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Le scénario que nous allons créer dans ce pas à pas va considérer un raccordement du quartier à l'un des emplacements possibles : celui au Sud de la zone. 

.. image:: _static/reseau-exemple-scenario.png
    :width: 600

.. note::
    Pour reproduire ce pas à pas, vous pouvez : soit utiliser les données que vous avez préparé en suivant la page :ref:`Obtention et préparation des données géographiques <preparation>`, soit télécharger les données :download:`ici <_static/donnees_petite_anse.zip>`.

**1. Utilisation du module** ``Réseau``

* Sélectionner la station au Sud (bulles 1 à 3).

* Chercher ``ELAN`` dans la boîte à outils de traitements (bulle 4) et sélectionner ``Réseau`` (bulle 5).

.. image:: _static/etape1.png
    :width: 700

* Indiquer les 4 couches géographiques (bulles 1 à 4). **Bien cocher Entité(s) sélectionnée(s) uniquement pour considérer uniquement la STEU au Sud de la zone.**

* Laisser le champ *Nombre d'habitants* vide si vous avez choisi de travailler avec la couche *shape1_batiments.shp* (obtenue avec le plugin BD TOPO® Extractor, voir :ref:`Obtention et préparation des données géographiques <preparation>`).

.. note::
    Si vous préférez travailler avec la couche *bati_avec_population.gpkg* (obtenue avec le module ``Routes et bâtiments`` suivi du module ``Population``, voir :ref:`Obtention et préparation des données géographiques <preparation>`), indiquer *population* pour le champ à considérer.

.. image:: _static/etape2a.png
    :width: 500

* Laisser les valeurs par défaut pour les différents paramètres techniques.

* Sélectionner toutes les options possibles pour les diamètres gravitaires (bulle 5).

* Sélectionner un nom et un emplacement pour le fichier (bulle 6).

* Exécuter (bulle 7).

.. image:: _static/etape2b.png
    :width: 500

**2. Résultats en sortie de module** ``Réseau``

Après exécution, vous obtenez la vue suivante :

.. image:: _static/vue-gravitaire.png
    :width: 700

5 couches ont été chargées dans votre espace de travail avec des symbologies propres à chacune (pour les couches géométriques) :

    * carré jaune pour la STEU
    * triangles verts pour les stations de relevage
    * triangles rouges pour les stations de pompage (privées et non privées)
    * lignes bleues pour les sections en gravitaire et lignes rouges pour les sections en refoulement

D'autres styles sont disponibles pour la couche ``Canalisations``. Pour y accéder :

1. Sélectionner la couche ``Canalisations`` et **cliquer droit**.

2. Aller dans *Styles*. 

3. Sélectionner le style de votre choix parmi les 5 autres proposés. 

.. image:: _static/reseau-styles.png
    :width: 500

**Style diamètres**

.. image:: _static/vue-diametres.png
    :width: 700

**Style débit de pointe**

.. image:: _static/vue-debit.png
    :width: 400

**Style profondeur**

.. image:: _static/vue-profondeur.png
    :width: 700

**Style sens d'écoulement**

.. image:: _static/vue-ecoulement.png
    :width: 700

**Style sous-réseaux**

.. image:: _static/vue-sous-reseau.png
    :width: 400

.. note::
    Le style *Sous-réseaux* est ici uniforme car ce scénario considère une seule station donc un seul réseau d'assainissement (pas de sous-réseaux).

.. astuce::
    Pour organiser votre espace avec les différentes couches, vous pouvez créer des groupes (ici *Préparation de données*, *Données mises à disposition* et *STEU Sud*.)
    
    Pour cela, il vous suffit de cliquer sur l'icône *Ajouter un groupe* et d'y glisser les couches que vous souhaitez rassembler.

            .. image:: _static/ajout-groupe.png
                :width: 130

**3. Consulation de la couche** ``Informations sur le réseau`` **et des attributs des autres couches**

* Sélectionner la couche ``Informations sur le réseau`` (bulle 1).

* Cliquer que l'icône *Ouvrir la table attributaire* (bulle 2).

* Une fenêtre s'ouvre et vous permet d'accéder à l'ensemble des informations de la couche (bulle 3).

.. image:: _static/informations-table.png
    :width: 700

Pour consulter les attributs des 4 autres couches obtenues en sortie, procéder de même en sélectionnant la couche
dont vous souhaitez consulter les attributs. 

L'ensemble des attributs disponibles pour chaque couche est détaillé :ref:`plus haut <attributs-reseau>`.

Exploration des résultats (module ``Profils de canalisations``)
------------------------------------------------------------------

Pour explorer le pré-dimensionnement proposé par le module ``Réseau``, en plus des différents styles proposés pour la couche ``Canalisations``, le module ``Profils de canalisations`` et la visualisation
de ses sorties par l'outil *Profil d'élévation* de QGIS vous permet de visualiser le profil souterrain d'une succession de tuyaux.

Préalable
^^^^^^^^^^

Disposer d'une couche ``Canalisations`` issue du module ``Réseau``.

Utilisation du module
^^^^^^^^^^^^^^^^^^^^^^

1. Chercher ``ELAN`` dans la boîte à outils de traitements et sélectionner ``Profils de canalisations``.

.. image:: _static/start-profils.png
    :width: 277

2. Renseigner la couche de canalisations (bulle 1), choisir un emplacement et un nom pour le fichier de sortie (bulle 2) avant d'exécuter (bulle 3).

.. image:: _static/use-profils.png
    :width: 680

3. En sortie de module, vous obtenez **1 fichier .gpkg qui contient 3 couches** :

* ``Profil de terrain`` : couche de type *point* qui contient un échantillonnage des valeurs du MNT (altitude du profil de terrain) le long des canalisations.

* ``Profil de canalisations`` : couche de type *point* dont les points se supperposent à ceux de ``Profil de terrain`` dans le plan xy, mais qui correspondent à l'altitude des canalisations.

* ``Canalisations 3D`` : couche de type *ligne Z* créée à partir d'un échantillonnage de la couche ``Canalisations`` (conservation des styles et des attributs).

Visualisation (illustration sur notre exemple)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Pour afficher un profil de canalisations dans un plan xz, commencer par ouvrir l'outil **Profil d'élévation** : *Vue* - *Profil d'élévation*.

.. image:: _static/start-profil-elevation.png
    :width: 431

2. Dans la fenêtre *Profil d'élévation*, cocher les couches que vous souhaitez voir apparaître sur votre coupe. Par exemple : ``Stations de relevage``, ``Stations de pompage``, ``Profil de terrain``, ``Profil de canalisations`` et ``Canalisation 3D`` (bulle 1).

3. Sélectionner les canalisations dont vous souhaitez afficher le profil souterrain. Pour cela :

* Sélectionner la couche ``Canalisations 3D`` (bulle 2). 

* Activer l'accrochage (bulle 3a) sur la couche active (bulle 3b).

* Activer le tracé (bulle 4).

* Dans la fenêtre *Profil d'élévation*, cliquer sur l'icône *Dessiner une courbe* (bulle 5).

* Cliquer sur le premier point (bulle 6).

* Cliquer sur le dernier point (bulle 7).

* Puis cliquer droit pour activer le tracé entre ces deux points (bulle 7).

.. image:: _static/use-profil-elevation.png
    :width: 597

6. Votre profil s'affiche dans la fenêtre profil d'élévation.

.. image:: _static/profil-exemple.png
    :width: 700

Cette vue montre le relief du terrain et le profil de canalisations échantillonnées. Elle permet de bien
visualiser les chutes au niveau des regards. En revanche, elle ne permet pas de distinguer clairement les portions en gravitaire
de celles en refoulement, ni d'omettre les points qui arrivent d'autres plans au niveau des regards.

7. En décochant ``Canalisations 3D``, vous obtenez cette vue.

.. image:: _static/profil-style-gravitaire.png
    :width: 700

Ici les chutes au niveaux des regards ne sont pas représentées (discontinutés dans le tracé). En revanche, les sections
en refoulement (en rouge) se distinguent clairement de celles en gravitaire (en bleu) et les points arrivant d'autres plans ne viennent pas 
perturber l'interprétation du profil.

8. Vous pouvez également obtenir une vue en fonction des diamètres.

.. image:: _static/profil-style-diametre.png
    :width: 700

Pour cela :

* Cliquer droit sur ``Canalisations 3D`` dans la fenêtre *Profil d'élévation* puis cliquer sur *Propriétés*.

.. image:: _static/profil-chgt-style.png
    :width: 300

* Dans la fenêtre qui s'ouvre, cliquer sur *Style* (en bas) et sélectionner *Diamètres*.

.. image:: _static/profil-changement-style.png
    :width: 700

.. tip::
    Vous pouvez également obtenir cette vue en fonction des diamètres en passant par le panneau *Couches* :
        * Cliquer droit sur ``Canalisations 3D``.
        * *Styles*.
        * Choisir *Diamètres*.
        * Décocher puis recocher la couche ``Canalisations 3D`` dans la fenêtre *Profil d'élévation* pour que le nouveau style s'applique.

Étape 2 : Pré-dimensionner la ou les STEU (module ``Procédés``)
----------------------------------------------------------------

Pour compléter votre scénario, il reste à pré-dimensionner la ou les stations qui constituent les points exutoires de votre réseau d'assainissement.

Le module ``Procédés`` permet, pour chaque station, de **tester et pré-dimensionner différentes filières de traitement de filtres plantés de végétaux (FPV)**.

Les filières peuvent être constituées de **1 à n étages de traitement** et impliquer **différents procédés** : :download:`filtre à écoulement vertical (système français)<_static/CARIBSAN_Fiche01_V1-FR.pdf>` (VdNS1), 
:download:`filtre à écoulement vertical avec sable <_static/CARIBSAN_Fiche02_V1-FR.pdf>` (VdNS2) et :download:`filtre à écoulement vertical avec couche saturée <_static/CARIBSAN_Fiche03_V1-FR.pdf>` (VdNSS).

Préalable 
^^^^^^^^^^^^

1. Avoir installé **la librairie wetlandoptimizer** comme expliqué dans :ref:`Installation des dépendances <dependances>`.

2. Disposer **d'une couche de type point avec le ou les emplacements de stations envisagés**.

Cette couche doit contenir **8 attributs** : *coordonnées gps*, *niveau rejet MES* [mg/L], *niveau rejet DBO5* [mg/L], *niveau rejet NTK* [mg/L], *niveau rejet DCO* [mg/L], *niveau rejet NO3* [mg/L], *niveau rejet NT* [mg/L], *débit journalier* [m3/j].

Pour les **niveaux de rejet**, **3 doivent obligatoirement être renseignés** avec une valeur numérique : **niveau rejet MES** [mg/L], **niveau rejet DBO5** [mg/L], **niveau rejet DCO** [mg/L]. 
Les autres peuvent être renseignés à *NULL* selon votre contexte (tout ou partie d'entre eux).

Cette couche peut-être obtenue en **sortie de module** ``Réseau``. Le débit journalier et les coordonnées GPS sont alors renseignés. 
Les attributs relatifs aux niveaux de rejet sont présents mais à renseigner manuellement selon votre contexte.

3. Avoir délimité et enregistré les **surfaces disponibles pour chaque station** au sein d'une couche de type *polygone*. 

Ce point est **facultatif** et n'intervient pas dans le pré-dimensionnement :
il permet de vous aider à identifier quelles filières, parmi celles qui permettent d'atteindre vos contraintes de rejet, coïncident avec vos contraintes en termes de surface.

Utilisation du module
^^^^^^^^^^^^^^^^^^^^^^

1. Chercher ``ELAN`` dans la boîte à outils de traitements et sélectionner ``Procédés``.

.. image:: _static/start-procedes.png
    :width: 271

2. Indiquer si votre zone se situe en climat *Tempéré* ou *Tropical* (bulle 1). Ce choix impacte le pré-dimensionnement des filières en termes de surface et de volume (surface et volume réduits en climat tropical).

.. note::
    Choisissez *Tropical* si la température est supérieure ou égale à 25°C toute l'année.

Pour plus d'informations sur la bonne prise en compte du climat tropical lors du dimensionnement de filtres plantés de végétaux :
    Lombard-Latune et Molle (2017). Les filtres plantés de végétaux pour le traitement des eaux usées domestiques en milieu tropical : Guide de dimensionnement de la filière tropicalisée. Guides et protocoles. 72 pages. Agence française de la biodiversité.

3. Renseigner la couche STEU (bulle 2) et éventuellement la couche de surfaces disponibles (bulle 3).

4. Assurer vous que les champs détectés pour les 8 attributs sont bien corrects : coordonnées GPS, niveaux de rejet et débit journalier (encart 4). 

5. Pour le nombre d'étages maximum, nous vous conseillons de laisser la valeur 3 qui est la valeur par défaut.

6. Choisir un emplacement et un nom pour le fichier de sortie (bulle 5) avant d'exécuter (bulle 6).

.. image:: _static/use-procedes.png
    :width: 662

7. Après exécution du module, vous obtenez une couche nommée ``Couche de filières`` (couche de type *point*).

Cette couche possède de nombreux attributs :

    * **id filière** : identifiant numérique de la filière pré-dimensionnée.
    * **description filière** : détails de la filière pré-dimensionnée (procédé étage 1 - ... - procédé étage n). 
    * **coordonnées gps** : identifiant STEU pour laquelle la filière a été pré-dimensionnée.
    * **taux de charge MES par étape de traitement** [%] : taux de charge en MES par étage [taux étage 1,..., taux étage n].
    * **taux de charge DBO5 par étape de traitement** [%] : taux de charge en DBO5 par étage [taux étage 1,..., taux étage n].
    * **taux de charge NTK par étape de traitement** [%] : taux de charge en NTK par étage [taux étage 1,..., taux étage n].
    * **taux de charge DCO par étape de traitement** [%] : taux de charge en DCO par étage [taux étage 1,..., taux étage n].
    * **taux de charge hydraulique par étape de traitement** [%] : taux de charge hydraulique par étage [taux étage 1,..., taux étage n].
    * **surface disponible** [m²] : calculée à partir de la couche *polygone* indiquée lors du lancement du module (couche optionnelle).
    * **surface totale** [m²] : surface de l'ensemble de la filière (somme des surfaces des étages 1 à n). 

    La valeur de la surface totale conditionne sa mise en forme : si elle est **inférieure ou égale à la surface disponible**, la case est **verte** ; **sinon**, elle apparaît **rouge**.

    * **surface par étage de traitement** [m²] : détail des surfaces pour chaque étage [surface étage 1,..., surface étage n].
    * **volume total** [m3] : volume de l'ensemble de la filière (somme des volumes des étages 1 à n). 
    * **profondeur saturée par étage** [m] : détail de la profondeur saturée pour chaque étage [profondeur saturée étage 1,..., profondeur saturée étage n]. 
    
    Cette profondeur est nulle pour les procédés VdNS1 et VdNS2 qui sont dépourvus de couche saturée.

    * **profondeur désaturée par étage** [m] : détail de la profondeur désaturée pour chaque étage [profondeur désaturée étage 1,..., profondeur désaturée étage n]. 
    * **concentration MES effluent** [mg/L] : concentration en MES en sortie de filière de traitement.
    * **concentration DBO5 effluent** [mg/L] : concentration en DBO5 en sortie de filière de traitement.
    * **concentration NTK effluent** [mg/L] : concentration en NTK en sortie de filière de traitement.
    * **concentration DCO effluent** [mg/L] : concentration en DCO en sortie de filière de traitement.
    * **concentration NT effluent** [mg/L] : concentration en NT en sortie de filière de traitement.
    * **concentration NO3 effluent** [mg/L] : concentration en NO3 en sortie de filière de traitement.
    
Chaque entité de la couche ``Couche de filières`` est une filière de traitement qui permet d'atteindre les niveaux de rejet indiqués dans les attributs de la couche STEU : les concentrations 
dans l'effluent sont donc inférieures ou égales aux niveaux de rejet imposés.

La **succession de procédés** (*descriptif filière*) varie d'une filière de traitement à une autre. 

Pour chaque filière de traitement, en plus des **concentrations de sortie atteintes** dans l'effluent, des **caractéristiques géométriques** sont indiquées 
(*surface totale*, *surface par étage de traitement*, *volume total*, *profondeur saturée*, *profondeur désaturée*)  ainsi que des **caractéristiques de 
fonctionnement** (*taux de charge par étape de traitement* pour les différents polluants et *taux de charge hydraulique par étape de traitement*).

Les taux de charge par étage de traitement peuvent constituer des indicateurs intéressants selon les projections futures faites pour la zone et ainsi orienter
votre choix de filière. Par exemple, si une forte augmentation de population est planifiée sur la zone, il sera préférable d'opter pour une filière de traitement qui 
n'est pas au maximum de sa charge en termes de polluants dans la configuration actuelle.

Application à l'exemple de :ref:`Petite-Anse <petite-anse>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**1. Renseigner les contraintes de rejet dans la couche** ``STEU``

Les niveaux de rejet à respecter dans le cas d'une station au Sud de la zone sont les suivants :

    * MES : 35 mg/L 
    * DBO5 : 35 mg/L 
    * NTK : 20 mg/L 
    * DCO : 125 mg/L

* Sélectionner la couche ``STEU`` (bulle 1).

* Basculer en mode édition (bulle 2) puis ouvrir la table attributaire (bulle 3).

* Renseigner les valeurs numériques indiquées pour les niveaux de rejet en MES, DBO5, NTK et DCO (encart 4).

* Sortir du mode édition (bulle 5) et fermer la table attributaire (bulle 6).

.. image:: _static/edit-attributs-steu.png
    :width: 700

**2. Délimitation de la surface disponible** (facultatif)

* Créer une nouvelle couche (.gpkg ou .shp) de type *polygone*.

.. image:: _static/nouvelle-couche.png
     :width: 600

.. image:: _static/couche-surface.png
     :width: 400

* L'éditer et délimiter la surface disponible.

.. image:: _static/delimitation-surface.png
     :width: 700

* Enregistrer et sortir du mode édition.

.. image:: _static/save.png
     :width: 196

**3. Utilisation du module** ``Procédés``

* Cherche ``ELAN`` dans la Boîte à outils de traitements et sélectionner ``Procédés`` (bulles 1 et 2).

* Choisir *Tropical* pour le climat (bulle 3).

* Indiquer la couche ``STEU`` dont vous avez renseigné les attributs (bulle 4) et la couche ``surface-dispo`` que vous venez de créer (bulle 5).

.. image:: _static/ex-procedes.png
     :width: 600

* Vérifier que les champs identifiés pour les niveaux de rejets et le débit journalier sont corrects.

* Indiquer un nom et un emplacement pour l'enregistrement du fichier de sortie (bulle 6), pusi exécuter (bulle 7).

.. image:: _static/ex-procedes-suite.png
     :width: 600

**4. Consultation des caractéristiques des filières de traitement pré-dimensionnées**

Après exécution du module, vous obtenez un visuel de ce type (couche *point*) :

.. image:: _static/sortie-procedes-ex.png
     :width: 600

Pour consulter les attributs de cette couche : 

* Sélectionner la couche ``Couche de filières`` (bulle 1).

* Cliquer que l'icône Ouvrir la table attributaire (bulle 2).

* Une fenêtre s'ouvre et vous permet d'accéder à l'ensemble des informations de la couche (bulle 3).

.. image:: _static/attributs-procedes-ex.png
     :width: 700

**5. Pré-sélection d'une filière de traitement**

Ici, 6 filières permettent d'atteindre les niveaux de rejets imposés :
    
    * VdNS1-VdNS2
    * VdNS1-VdNS2-VdNS2
    * VdNSS-VdNS2
    * VdNSS-VdNS2-VdNS2
    * VdNS1
    * VdNSS

La surface totale apparaît en rouge pour la filière VdNS1-VdNS2-VdNS2 car elle est supérieure à la surface disponible.

Les filières à étage unique (VdNS1 et VdNSS) permettent ici d'atteindre les niveaux de rejets et sont généralement moins 
coûteuses que les filières multi-étages. Au vu des taux de charge en polluants et du taux de charge hydraulique, elles 
pourraient constituer deux filières de traitement intéressantes.

Un premier scénario pourrait donc être : le réseau d'assainissement obtenu à l'étape 1 couplé à une filière VdNS1. Le couplage avec une filière 
VdNSS pourrait constitué un second scénario.

Cette étape de pré-sélection d'une filière de traitement correspond au troisième temps de la création d'un scénario.

.. note::
   Des représentations graphiques pour mieux visualiser les attributs des différentes filières retenues seront bientôt disponibles
   en sortie de module ``Procédés``. Il sera ainsi plus simple d'identifier leurs points forts et leurs points faibles respectifs.

Exercice : Création d'un second scénario pour :ref:`Petite-Anse <petite-anse>`
-------------------------------------------------------------------------------

Pour mettre en pratique le contenu de cette page, vous pouvez essayez de suivre les différentes étapes décrites
mais cette fois-ci en considérant 2 emplacements possibles : celui au Sud de la zone et celui au Nord.

.. image:: _static/illustration-exercice.png
     :width: 500

Les niveaux de rejet pour l'emplacement au Nord de la zone sont moins contraignants (pas de contrainte sur l'azote) :

    * MES : 35 mg/L 
    * DBO5 : 35 mg/L 
    * DCO : 125 mg/L

.. note::
    L'aspect itératif de la définition d'un scénario n'est pas évoqué dans ce pas à pas, mais il s'agit d'une pratique possible.
    Par exemple : si vous jugez que certains bâtiments sont trop "coûteux" à raccorder (plus de 40 mètre linéaire pour un bâtiment), 
    vous pouvez éditer la couche bâtiment et supprimer ces bâtiments pour voir quel serait l'impact de leur maintien en assainissement 
    non collectif sur le pré-dimensionnement du réseau proposé.