.. _prb1:

Création d'un scénario pour la question du centralisé / décentralisé
=====================================================================

La création d'un scénario pour la question du centralisé / décentralisé implique quatre temps :

**1. Tracer un réseau d'assainissement.**

**2. Pré-dimensionner les filières de traitement pour les stations.**

**3. Pré-sélectionner une filière pour chaque station**

**4. Créer un objet scénario.**

Pour une même zone, vous pouvez créer successivement autant de scénarios que vous le souhaitez.

Étape 1 : Tracer le réseau d'assainissement (module ``Réseau``)
-----------------------------------------------------------------

Préalable
^^^^^^^^^^

**1.** Avoir installé **la librairie pysewer** comme expliqué dans :ref:`Installation des dépendances <dependances>`.

**2.** Disposer de **4 couches géographiques** :

* ``STEU`` : couche vecteur qui contient l'ensemble des **emplacements envisagés comme exutoires** (station de traitement des eaux usées existante ou projet possible), type : *point*.

* ``bâtiments`` : couche vecteur qui rassemble les **bâtiments à raccorder**, type : *point* (centroïdes des bâtiments). 

* ``routes`` : couche vecteur indiquant les **routes empruntables** pour le raccordement, type : *ligne*.

* ``MNT`` : couche raster (.tif, .asc, .vrt) du **modèle numérique de terrain** de la zone d'intérêt.

.. attention::
   **Les 4 couches doivent être dans le même SCR (système de coordonnées de référence).**

Si vous ne disposez pas de ces couches pour votre zone d'étude, vous pouvez vous rendre à la page :ref:`Obtention et préparation des données géographiques <preparation>`
pour quelques astuces et explications.

Utilisation du module
^^^^^^^^^^^^^^^^^^^^^^^

**1.** Chercher ``ELAN`` dans la boîte à outils de traitements et sélectionner ``Réseau``.

.. image:: _static/start-reseau.png
    :width: 251

.. tip::
    Pour afficher le panneau ``Boîte à outils de traitements`` s'il n'apparaît pas dans votre espace de travail : *Vue* - *Panneaux* - *Boîte à outils de traitements*.

.. image:: _static/boite-outils.png
     :width: 633

**2.** **Renseigner les 4 couches géographiques**. 

.. tip::
    Pour les exutoires, vous pouvez sélectionner au préalable celui ou ceux que vous souhaitez considérer parmi l'ensemble des possibilités envisagées puis cocher *Entités sélectionnées uniquement* dans le module.
    Cette option est également proposée pour les routes et les bâtiments à considérer.

Si le nombre d'individus par bâtiment est connu et renseigné dans un attribut (*population* par exemple), 
l'indiquer dans l'encart mis en évidence. Sinon, un nombre moyen d'individus par bâtiment sera considéré 
(valeur ajustable selon votre contexte).

.. note::
    Si vous avez eu recours au module ``Population`` pour préparer vos données géographiques, l'attribut à indiquer est *population*.

.. image:: _static/couches-reseau.png
    :width: 677

**3.** Faire coulisser l'ascenseur et **ajuster les différents paramètres** (encart 5) afin que le pré-dimensionnement du réseau soit le plus adapté à votre contexte : 

* ``nombre moyen de personnes par foyer`` : à renseigner dans le cas où la population n'est pas discrétisée à l'échelle du bâtiment.

* ``volume moyen d'eaux usées produit par jour par personne`` : [m3].

* ``coefficient de pointe journalier`` : [m3/j].

* ``pente minimale permettant l'autocurrage`` : [m/m].

* ``profondeur max autorisée de canalisation`` : [m], dépend du contexte géologique.

* ``profondeur min autorisée de canalisation`` : [m], généralement conditionnée par le risque de gel.

* ``rugosité canalisation`` : [mm], dépend du matériau utilisé pour les canalisations.

* ``diamètre autorisé sous pression`` : [m], un seul diamètre autorisé.

* ``diamètres autorisés en gravitaire`` : [m], à choisir parmi les options proposées (0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.6, 0.8 ou 1.0). Les 9 options peuvent être considérées ou seulement une partie d'entre elles.

.. attention::
    Il a été constaté que **les modifications des profondeurs max et min autorisées ne sont actuellement pas prises 
    en compte** (valeurs bloquées aux valeurs par défaut 0.25 m et 8 m). Le bug doit d'abord être corrigé sur pysewer
    avant que la correction puisse être intégrée à ELAN.

**4.** Indiquer un emplacement et un nom pour la couche .gpkg en sortie (bulle 6) puis exécuter (bulle 7).

.. image:: _static/entrees-reseau.png
    :width: 700

**5.** Après exécution du module, vous disposez de **1 fichier au format .gpkg qui contient 7 couches** :

* ``STEU`` (carré jaune) : couche de type *point* avec le ou les exutoires considérés pour la simulation. 

* ``Bâtiments`` : couche de type *point* avec les bâtiments pris en compte pour la simulation.

* ``Routes`` : couche de type *ligne* avec les routes considérées comme empruntables lors de la simulation.

* ``Stations de relevage`` (triangle vert) : couche de type *point* qui contient les stations de relevage du réseau d'assainissement pré-dimensionné.

* ``Stations de pompage`` (triangle rouge) : couche de type *point* qui contient les stations de pompage du réseau d'assainissement pré-dimensionné (stations privées et non privées).

* ``Canalisations`` : couche de type *ligne* qui contient les canalisations pré-dimensionnées.

* ``Informations sur le réseau`` : couche non géométrique qui regroupe différentes métriques sous forme d'attributs.

.. note::

    Les couches ``STEU``, ``Bâtiments`` et ``Routes`` permettent de garder trace des éléments fournis en entrée de simulation. Cela s'avère
    particulièrement utile si vous avez recours à l'option *Entités sélectionnées uniquement*, mais également pour ne pas perdre le fil dans la démarche
    itérative qu'implique l'exploration de différents scénarios (affinage des bâtiments à raccorder, redéfinition des routes
    empruntables par suppression et/ou ajout).


.. _attributs-reseau:

**Chaque couche vecteur est caractérisée par des attributs.**

* ``STEU`` : *altitude terrain* [m], *coordonnées gps* (identifiant unique pour chaque exutoire), *débit de pointe* [m3/j], *débit moyen journalier* [m3/j], *habitants raccordés* [nb], *profondeur tranchée* [m], *profondeur canas entrantes* [m], *diamètres entrants* [m].

.. note::
    En sortie de module ``Réseau``, la couche STEU compte aussi des attributs non renseignés : *niveau rejet MES* [mg/L], *niveau rejet DBO5* [mg/L], *niveau rejet NTK* [mg/L], *niveau rejet DCO* [mg/L], *niveau rejet NO3* [mg/L], *niveau rejet NT* [mg/L], *niveau rejet PT* [mg/L], *niveau rejet coliformes* [UFC/100mL]. Ces attributs sont à renseigner manuellement 
    pour chaque exutoire selon vos contraintes de rejet. Ils servent d'entrées pour le module ``Procédés``. Certains peuvent être renseignés à *NULL*.

* ``Stations de relevage`` : *altitude terrain* [m], *débit de pointe* [m3/s], *débit moyen journalier* [m3/j], *habitants raccordés* [nb], *profondeur canas entrantes* [m], *charge hydrostatique* [m].

* ``Stations de pompage`` : *altitude terrain* [m], *débit de pointe* [m3/s], *débit moyen journalier* [m3/j], *habitants raccordés* [nb], *profondeur canas entrantes* [m], *charge hydrostatique* [m].

.. note::
    ``Stations de pompage`` peut indiquer des charges hydrostatiques négatives pour certaines des stations pré-dimensionnées. Il ne s'agit pas d'une erreur :
    cela signifie que, pour ces stations, le point d'arrivée du tronçon en refoulement se situe plus bas que le point de départ. En d'autres termes : la station
    de pompage se comporte comme un siphon.

    Par exemple, la station de pompage est ici caractérisée par une charge hydrostatique de -19,25 m.
            
            .. image:: _static/siphon.png
                :width: 700

* ``Canalisations`` : *longueur* [m], *profil de terrain* [liste de points échantillonnés tous les 10 m], *avec pompe* [booléen], *sous pression* [booléen], *profils de canalisations* [liste de points échantillonnés tous les 10 m], *profondeur moyenne tranchée* [m], *diamètre* [m], *débit de pointe* [m3/s], *coordonnées STEU* [identifiant STEU exutoire].

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
    Pour reproduire ce pas à pas, vous pouvez : soit utiliser les données que vous avez préparé en suivant la page :ref:`Obtention et préparation des données géographiques <preparation>`, soit télécharger les données :download:`ici <_static/couches_petite_anse.zip>`.

**1. Utilisation du module** ``Réseau``

* Sélectionner la station au Sud (bulles 1 à 3).

* Chercher ``ELAN`` dans la boîte à outils de traitements (bulle 4) et sélectionner ``Réseau`` (bulle 5).

.. image:: _static/etape1.png
    :width: 700

* Indiquer les 4 couches géographiques (bulles 1 à 4). **Bien cocher Entité(s) sélectionnée(s) uniquement pour considérer uniquement la STEU au Sud de la zone.**

* Si vous souhaitez travailler en considérant un nombre variable d'habitants par bâtiment, indiquer l'attribut correspondant à la population parmi les attributs de votre couche bâtiments (menu déroulant) pour *Nombre d'habitants*. Sinon laisser le champ vide.

.. image:: _static/etape2a.png
    :width: 611

* Laisser les valeurs par défaut pour les différents paramètres techniques.

* Sélectionner les 6 premiers diamètres (0,1 à 0,4) parmi les options possibles pour les diamètres gravitaires (bulle 5).

* Sélectionner un nom et un emplacement pour le fichier (bulle 6).

* Exécuter (bulle 7).

.. image:: _static/etape2b.png
    :width: 500

**2. Résultats en sortie de module** ``Réseau``

Après exécution, vous obtenez la vue suivante :

.. image:: _static/vue-gravitaire.png
    :width: 700

.. note::

    Les couches relatives aux routes et aux bâtiments n'apparaissent pas sur cette vue et les suivantes pour plus de lisibilité.

6 couches géométriques ont été chargées dans votre espace de travail, chacune avec une symbologie qui lui est propre :

    * carré jaune pour la STEU
    * lignes de couleur aléatoire pour les routes
    * points de couleur aléatoire pour les bâtiments
    * triangles verts pour les stations de relevage
    * triangles rouges pour les stations de pompage (privées et non privées)
    * lignes bleues pour les sections en gravitaire et lignes rouges pour les sections en refoulement

D'autres styles sont disponibles pour la couche ``Canalisations``. Pour y accéder :

**1.** Sélectionner la couche ``Canalisations`` et **cliquer droit**.

**2.** Aller dans *Styles*. 

**3.** Sélectionner le style de votre choix parmi les 5 autres proposés. 

.. image:: _static/reseau-styles.png
    :width: 500

**Style diamètres**

.. image:: _static/vue-diametres.png
    :width: 700

.. tip::
    Pour savoir exactement combien d'entités correspondent à chaque diamètre : cliquer droit sur la couche ``Canalisations`` et cocher ``Afficher le nombre d'entités``. 
    Vous obtiendrez quelque chose de ce type : 

                .. image:: _static/afficher_entites.png
                    :width: 162

    Cette astuce peut être appliquée à n'importe quelle couche vecteur.

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
    En considérant 2 stations possibles, une vue de ce type sera obtenue :

                .. image:: _static/vue_2_reseaux.png
                    :width: 200

.. astuce::
    Pour organiser votre espace avec les différentes couches, vous pouvez créer des groupes (ici *Préparation de données*, *Données mises à disposition* et *STEU Sud*.)
    
    Pour cela, il vous suffit de cliquer sur l'icône *Ajouter un groupe* et d'y glisser les couches que vous souhaitez rassembler.

            .. image:: _static/ajout-groupe.png
                :width: 130

**3. Consultation de la couche** ``Informations sur le réseau`` **et des attributs des autres couches**

* Sélectionner la couche ``Informations sur le réseau`` (bulle 1).

* Cliquer que l'icône *Ouvrir la table attributaire* (bulle 2).

* Une fenêtre s'ouvre et vous permet d'accéder à l'ensemble des informations de la couche (bulle 3).

.. image:: _static/informations-table.png
    :width: 700

Pour consulter les attributs des 4 autres couches obtenues en sortie, procéder de même en sélectionnant la couche
dont vous souhaitez consulter les attributs. 

L'ensemble des attributs disponibles pour chaque couche est détaillé :ref:`plus haut <attributs-reseau>`.

.. tip::
    Si vous êtes amenés à charger le géopackage contenant les 7 couches dans un autre projet, vous pouvez l'ouvrir directement
    dans un groupe en suivant la démarche suivante (ouverture des 7 couches placées dans un groupe commun) :

    - Glisser le .gpkg depuis *Explorateur* dans votre fichier QGIS.
    - Dans la fenêtre qui s'ouvre, dérouler *Options* et cocher *Afficher des couches à un groupe* (bulle 1).
    - Cliquer sur *Ajouter une couche* (bulle 2).

                    .. image:: _static/ouverture_gpkg.png
                        :width: 500

Exploration des résultats (module ``Profils de canalisations``)
------------------------------------------------------------------

Pour explorer le pré-dimensionnement proposé par le module ``Réseau``, en plus des différents styles proposés pour la couche ``Canalisations``, le module ``Profils de canalisations`` et la visualisation
de ses sorties par l'outil *Profil d'élévation* de QGIS vous permet de visualiser le profil souterrain d'une succession de tuyaux.

Préalable
^^^^^^^^^^

Disposer d'une couche ``Canalisations`` issue du module ``Réseau``.

Utilisation du module
^^^^^^^^^^^^^^^^^^^^^^

**1.** Chercher ``ELAN`` dans la boîte à outils de traitements et sélectionner ``Profils de canalisations``.

.. image:: _static/start-profils.png
    :width: 277

**2.** Renseigner la couche de canalisations (bulle 1), choisir un emplacement et un nom pour le fichier de sortie (bulle 2) avant d'exécuter (bulle 3).

.. image:: _static/use-profils.png
    :width: 680

**3.** En sortie de module, vous obtenez **1 fichier .gpkg qui contient 3 couches** :

* ``Profil de terrain`` : couche de type *point* qui contient un échantillonnage des valeurs du MNT (altitude du profil de terrain) le long des canalisations.

* ``Profil de canalisations`` : couche de type *point* dont les points se supperposent à ceux de ``Profil de terrain`` dans le plan xy, mais qui correspondent à l'altitude des canalisations.

* ``Canalisations 3D`` : couche de type *ligne Z* créée à partir d'un échantillonnage de la couche ``Canalisations`` (conservation des styles et des attributs).

Visualisation (illustration sur notre exemple)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**1.** Pour afficher un profil de canalisations dans un plan xz, commencer par ouvrir l'outil **Profil d'élévation** : *Vue* - *Profil d'élévation*.

.. image:: _static/start-profil-elevation.png
    :width: 431

**2.** Dans la fenêtre *Profil d'élévation*, cocher les couches que vous souhaitez voir apparaître sur votre coupe. Par exemple : ``Stations de relevage``, ``Stations de pompage``, ``Profil de terrain``, ``Profil de canalisations`` et ``Canalisation 3D`` (bulle 1).

**3.** Sélectionner les canalisations dont vous souhaitez afficher le profil souterrain. Pour cela :

* Sélectionner la couche ``Canalisations 3D`` (bulle 2). 

* Activer l'accrochage (bulle 3a) sur la couche active (bulle 3b).

.. tip::
     Si *Accrochage* n'est pas visible : activez-le via *Vue - Barres d'outils - Accrochage*.

* Activer le tracé (bulle 4).

* Dans la fenêtre *Profil d'élévation*, cliquer sur l'icône *Dessiner une courbe* (bulle 5).

* Cliquer sur le premier point (bulle 6).

* Cliquer sur le dernier point (bulle 7).

* Puis cliquer droit pour activer le tracé entre ces deux points (bulle 7).

.. image:: _static/use-profil-elevation.png
    :width: 597

**4.** Votre profil s'affiche dans la fenêtre profil d'élévation.

.. image:: _static/profil-exemple.png
    :width: 700

Cette vue montre le relief du terrain et le profil de canalisations échantillonnées. Elle permet de bien
visualiser les chutes au niveau des regards. En revanche, elle ne permet pas de distinguer clairement les portions en gravitaire
de celles en refoulement, ni d'omettre les points qui arrivent d'autres plans au niveau des regards.

**5.** En décochant ``Canalisations 3D``, vous obtenez cette vue.

.. image:: _static/profil-style-gravitaire.png
    :width: 700

Ici les chutes au niveaux des regards ne sont pas représentées (discontinutés dans le tracé). En revanche, les sections
en refoulement (en rouge) se distinguent clairement de celles en gravitaire (en bleu) et les points arrivant d'autres plans ne viennent pas 
perturber l'interprétation du profil.

**6.** Vous pouvez également obtenir une vue en fonction des diamètres.

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

Les filières peuvent être constituées de **1 à n étages de traitement** (au maximum, n = 3) et impliquer **différents procédés** : :download:`filtre à écoulement vertical (système français)<_static/CARIBSAN_Fiche01_V1-FR.pdf>` (VdNS1), 
:download:`filtre à écoulement vertical avec sable <_static/CARIBSAN_Fiche02_V1-FR.pdf>` (VdNS2) et :download:`filtre à écoulement vertical avec couche saturée <_static/CARIBSAN_Fiche03_V1-FR.pdf>` (VdNSS).

Préalable 
^^^^^^^^^^^^

**1.** Avoir installé **la librairie wetlandoptimizer** comme expliqué dans :ref:`Installation des dépendances <dependances>`.

**2.** Disposer **d'une couche de type point avec le ou les emplacements de stations envisagés**.

Cette couche doit contenir **10 attributs** : *coordonnées gps*, *niveau rejet MES* [mg/L], *niveau rejet DBO5* [mg/L], *niveau rejet NTK* [mg/L], *niveau rejet DCO* [mg/L], *niveau rejet NO3* [mg/L], *niveau rejet NT* [mg/L], *niveau rejet PT* [mg/L], *niveau rejet coliformes* [UFC/100mL], *débit journalier* [m3/j]. 

Pour les **niveaux de rejet**, **3 doivent obligatoirement être renseignés** avec une valeur numérique strictement supérieure à 0 : **niveau rejet MES** [mg/L], **niveau rejet DBO5** [mg/L], **niveau rejet DCO** [mg/L]. 
Les autres peuvent être renseignés à *NULL* selon votre contexte (tout ou partie d'entre eux).

.. attention::
    Les niveaux de rejets relatifs au phosphore total (PT) et aux pathogènes (coliformes) ne sont actuellement pas pris en compte dans l'optimisation réalisée par *wetlandoptimizer* (valeurs par défaut considérées : *NULL*).
    Leur prise en compte sera intégrée dans une version future. 

Cette couche peut-être obtenue en **sortie de module** ``Réseau``. Le débit journalier et les coordonnées GPS sont alors renseignés. 
Les attributs relatifs aux niveaux de rejet sont présents mais à renseigner manuellement selon votre contexte.

**3.** Avoir délimité et enregistré les **surfaces disponibles pour chaque station** au sein d'une couche de type *polygone*. 

Ce point est **facultatif** et n'intervient pas dans le pré-dimensionnement :
il permet de vous aider à identifier quelles filières, parmi celles qui permettent d'atteindre vos contraintes de rejet, coïncident avec vos contraintes en termes de surface.

Utilisation du module
^^^^^^^^^^^^^^^^^^^^^^

**1.** Chercher ``ELAN`` dans la boîte à outils de traitements et sélectionner ``Procédés``.

.. image:: _static/start-procedes.png
    :width: 271

**2.** Indiquer si votre zone se situe en climat *Tempéré* ou *Tropical* (bulle 1). Ce choix impacte le pré-dimensionnement des filières en termes de surface et de volume (surface et volume réduits en climat tropical).

.. note::
    Choisissez *Tropical* si la température est supérieure ou égale à 25°C toute l'année.

Pour plus d'informations sur la bonne prise en compte du climat tropical lors du dimensionnement de filtres plantés de végétaux :

    *Lombard-Latune et Molle (2017). Les filtres plantés de végétaux pour le traitement des eaux usées domestiques en milieu tropical : Guide de dimensionnement de la filière tropicalisée. Guides et protocoles. 72 pages. Agence française de la biodiversité.*

**3.** Renseigner la couche STEU (bulle 2) et éventuellement la couche de surfaces disponibles (bulle 3).

**4.** Assurez vous que les champs détectés pour les 10 attributs sont bien corrects : coordonnées GPS, niveaux de rejet et débit journalier (encart 4). 

**5.** Pour le nombre d'étages maximum, nous vous conseillons de laisser la valeur 3 qui est la valeur par défaut.

**6.** Choisir un emplacement et un nom pour le fichier de sortie (bulle 5) avant d'exécuter (bulle 6).

.. image:: _static/use-procedes.png
    :width: 662

**7.** Après exécution du module, vous obtenez une couche nommée ``Couche de filières`` (couche de type *point*).

Cette couche contient toutes les filières de traitement testées lors de l'optimisation (une entité = une filière de traitement).
Chaque entité possède de nombreux attributs :

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

    * **profondeur non saturée par étage** [m] : détail de la profondeur non saturée pour chaque étage [profondeur non saturée étage 1,..., profondeur non saturée étage n]. 
    * **concentration MES effluent** [mg/L] : concentration en MES en sortie de filière de traitement.
    * **concentration DBO5 effluent** [mg/L] : concentration en DBO5 en sortie de filière de traitement.
    * **concentration NTK effluent** [mg/L] : concentration en NTK en sortie de filière de traitement.
    * **concentration DCO effluent** [mg/L] : concentration en DCO en sortie de filière de traitement.
    * **concentration NT effluent** [mg/L] : concentration en NT en sortie de filière de traitement.
    * **concentration NO3 effluent** [mg/L] : concentration en NO3 en sortie de filière de traitement.
    * **concentration PT effluent** [mg/L] : concentration en PT en sortie de filière de traitement.
    * **concentration coliformes** [UFC/100mL] : concentration en coliformes en sortie de filière de traitement.
    * **déviation MES** [%] : déviation de la concentration en MES dans l'effluent par rapport au niveau de rejet.
    * **déviation DBO5** [%] : déviation de la concentration en DBO5 dans l'effluent par rapport au niveau de rejet.
    * **déviation NTK** [%] : déviation de la concentration en NTK dans l'effluent par rapport au niveau de rejet.
    * **déviation DCO** [%] : déviation de la concentration en DCO dans l'effluent par rapport au niveau de rejet.
    * **déviation NT** [%] : déviation de la concentration en NT dans l'effluent par rapport au niveau de rejet.
    * **déviation NO3** [%] : déviation de la concentration en NO3 dans l'effluent par rapport au niveau de rejet.
    * **déviation PT** [%] : déviation de la concentration en PT dans l'effluent par rapport au niveau de rejet.
    * **déviation coliformes** [%] : déviation de la concentration en coliformes dans l'effluent par rapport au niveau de rejet.

    Les déviations sont mises en formes : en vert si supérieures ou égales à 0, en rouge si inférieures à 0. Elles renseignent sur la 
    conformité de la filière par rapport aux niveaux de rejets renseignés en entrée de module : vert = conforme, rouge = non conforme.

    * **MES normalisé** [-] : valeur normalisée de la concentration en MES dans l'effluent par rapport au niveau de rejet exigé.
    * **DBO5 normalisé** [-] : valeur normalisée de la concentration en DBO5 dans l'effluent par rapport au niveau de rejet exigé.
    * **NTK normalisé** [-] : valeur normalisée de la concentration en NTK dans l'effluent par rapport au niveau de rejet exigé.
    * **DCO normalisé** [-] : valeur normalisée de la concentration en DCO dans l'effluent par rapport au niveau de rejet exigé.
    * **NT normalisé** [-] : valeur normalisée de la concentration en NT dans l'effluent par rapport au niveau de rejet exigé.
    * **NO3 normalisé** [-] : valeur normalisée de la concentration en NO3 dans l'effluent par rapport au niveau de rejet exigé.
    * **PT normalisé** [-] : valeur normalisée de la concentration en PT dans l'effluent par rapport au niveau de rejet exigé.
    * **coliformes normalisés** [-] : valeur normalisée de la concentration en coliformes dans l'effluent par rapport au niveau de rejet exigé.
    * **surface normalisée** [-] : valeur normalisée de la surface totale de la filière par rapport à la surface disponible.

    Si la valeur normalisée est inférieure ou égale à 1, alors elle respecte la contrainte indiquée (niveau de rejet ou surface disponible). Sinon, elle l'excède.

.. note::
    Pour les paramètres facultatifs (niveau de rejet de certains polluants, surface disponible), s'ils ne sont pas renseignés, leurs déviation et 
    valeur normalisée ne sont pas calculées (*NULL*).

.. important::

    Parmi les entités de la couche ``Couche de filières``, seules les filières de traitement affichant des déviations "vertes" permettent d'atteindre les niveaux de rejet indiqués en entrée de module.

La **succession de procédés** (*descriptif filière*) varie d'une filière de traitement à une autre. 

Pour chaque filière de traitement, en plus des **concentrations de sortie atteintes** dans l'effluent, des **caractéristiques géométriques** sont indiquées 
(*surface totale*, *surface par étage de traitement*, *volume total*, *profondeur saturée*, *profondeur désaturée*), des **caractéristiques de 
fonctionnement** (*taux de charge par étape de traitement* pour les différents polluants et *taux de charge hydraulique par étape de traitement*) ainsi que
des **indicateurs de conformité** par rapport aux contraintes énoncées (*déviations*, *valeurs normalisées*).

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

* Cherche ``ELAN`` dans la *Boîte à outils de traitements* et sélectionner ``Procédés`` (bulles 1 et 2).

* Choisir *Tropical* pour le climat (bulle 3).

* Indiquer la couche ``STEU`` dont vous avez renseigné les attributs (bulle 4) et la couche ``surface-dispo`` que vous venez de créer (bulle 5).

.. image:: _static/ex-procedes.png
     :width: 600

* Vérifier que les champs identifiés pour les niveaux de rejets et le débit journalier sont corrects.

* Indiquer un nom et un emplacement pour l'enregistrement du fichier de sortie (bulle 6), puis exécuter (bulle 7).

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

Étape 3 : Pré-sélectionner une filière par exutoire
-----------------------------------------------------

Ici, 6 filières permettent d'atteindre les niveaux de rejets imposés (déviations en vert) :
    
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
VdNSS pourrait constituer un second scénario.

.. note::
   Des représentations graphiques (bar plot et radar plot) pour mieux visualiser les attributs des différentes filières retenues seront bientôt disponibles
   en sortie de module ``Procédés``. Il sera ainsi plus simple d'identifier leurs points forts et leurs points faibles respectifs.

Étape 4 : Créer un objet scénario (module ``Créer un scénario``)
-----------------------------------------------------------------

Le module ``Créer un scénario`` vous permet de créer un objet scénario contenant à la fois le pré-dimensionnement d'un réseau et celui des filières associées (1 par exutoire).

Il prend la forme d'un géopackage. C'est sur la base de ce géopackage que le scénario pourra ensuite être évalué par le module ``Evaluation``.

Préalable 
^^^^^^^^^^^^

**1.** Disposer d'une couche ``Canalisations`` issue du module ``Réseau``.

**2.** Avoir pré-dimensionné des filières pour chacun des exutoires de cette couche ``Canalisations`` avec le module ``Procédés`` (couche ``Couche de filières``).

**3.** Avoir choisi une possibilité de filière pour chaque exutoire parmi toutes celles pré-dimensionnées.

Utilisation du module
^^^^^^^^^^^^^^^^^^^^^^

**1.** Ouvrir la table attributaire de votre ``Couche de filières`` et sélectionner une filière par exutoire. Par exemple ici, la filière VdNS1 (1 seule filière car 1 seul exutoire dans ce scénario).

.. image:: _static/select-filiere.png
    :width: 600

**2.** Chercher ``ELAN`` dans la boîte à outils de traitements et sélectionner ``Créer un scénario``.

.. image:: _static/start-scenario.png
    :width: 250


**3.** Nommer votre scénario (bulle 1), indiquer la couche ``Canalisations`` à considérer (bulle 2), renseigner la couche ``Couche de filières`` et 
**cocher impérativement** ``Entités sélectionnées uniquement`` (bulle 3) afin que seules les filières que vous avez pré-sélectionnées soient prises en compte.

**4.** Indiquer un nom et un emplacement pour le fichier de sortie (bulle 4) puis exécuter (bulle 5).

.. image:: _static/use-scenario.png
    :width: 667

**5.** En sortie de module, vous obtenez **1 fichier.gpkg qui contient 9 couches** : 

- 7 couches issues du module ``Réseau``.
- 1 couche ``Couche de filières`` avec les filières retenues.
- 1 couche sans géométrie  ``metadata`` qui contient un identifiant unique pour la comparaison postérieure à d'autres scénarios.

.. important::
    **Le géopackage de sortie ne s'ouvre pas dans le projet**. Il est juste enregistré à l'emplacement indiqué, prêt à être chargé dans un nouveau projet à des fins d'évaluation puis de comparaison.

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

.. important::
    L'aspect itératif de la définition d'un scénario est brièvement mentionné mais n'est pas détaillé dans ce pas à pas. Il s'agit d'une pratique possible (voire inévitable).
    
    Par exemple : si vous jugez que certains bâtiments sont trop "coûteux" à raccorder (plus de 40 mètre linéaire pour un bâtiment), 
    vous pouvez éditer la couche bâtiment et supprimer ces bâtiments pour voir quel serait l'impact de leur maintien en assainissement 
    non collectif sur le pré-dimensionnement du réseau proposé. De même vous pouvez redéfinir les chemins empruntables en supprimant certains et/ou en en ajoutant d'autres.