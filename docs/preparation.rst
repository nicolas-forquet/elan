.. _preparation:

Obtention et préparation des données géographiques
==================================================

.. _entrees_reseau:

Entrées du module ``Réseau``
----------------------------

Pour pouvoir utiliser le module ``Réseau``, **4 couches géographiques** sont nécessaires :

* ``STEU`` : couche vecteur qui contient l'ensemble des **emplacements envisagés comme exutoires** (station de traitement des eaux usées existante ou projet possible), type : *point*.

* ``bâtiments`` : couche vecteur qui rassemble les **bâtiments à raccorder**, type : *point* (centroïdes des bâtiments). Si l'occupation est différente selon les bâtiments, le nombre d'habitants par bâtiment peut être indiqué via un attribut (*population* par exemple).

* ``routes`` : couche vecteur indiquant les **routes empruntables** pour le raccordement, type : *ligne*.

* ``MNT`` : couche raster (.tif, .asc, .vrt) du **modèle numérique de terrain** pour la zone d'intérêt.

.. note::
    Les couches vecteur peuvent être des .shp ou des .gpkg.

Si vous disposez de ces 4 couches, vous pouvez vous rendre directement à la page :ref:`Création d'un scénario pour la question du centralisé / décentralisé <prb1>`.
Sinon, poursuivez ici pour quelques astuces et explications sur l'obtention et la préparation des données géographiques requises.

**Pour la couche** ``STEU``, le plus simple est de ``Créer une nouvelle couche`` de type *point* et de l'éditer de sorte à indiquer tous les emplacements possibles comme exutoires (1 point = 1 exutoire possible).

**Pour les autres couches** : 

En contexte français (Hexagone et Outre-Mer)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _ rge_alti:

* ``MNT``: raster téléchargeable par département sur le site `Géoservices de l'IGN <https://geoservices.ign.fr/>`_ 
    * MNT à 25 m : `BD ALTI® 25M <https://geoservices.ign.fr/bdalti>`_
    * MNT à 5 m voire 1 m : `RGE ALTI® <https://geoservices.ign.fr/rgealti>`_

* ``routes`` et ``bâtiments``: couches téléchargeables par département sur le site Géoservices de l'IGN `BD TOPO® <https://geoservices.ign.fr/bdtopo>`_.

.. _bd_topo:

.. tip::
    Pour accéder aux routes et bâtiments à l'échelle de votre zone d'étude et non du département, vous pouvez installer et utiliser le plugin `BD TOPO® Extractor <https://plugins.qgis.org/plugins/bd_topo_extractor/>`_.
    
    Il vous suffit de :

        * Installer l'extension via le gestionnaire d'extensions.
        * Dessiner sur la carte la zone rectangulaire à extraire.
        * Choisir les couches ``Bâtiment`` et ``Tronçon de route``.

.. attention::
    La couche ``bâtiments`` obtenue est de type *polygone* et non *point*. Elle doit donc être transformée via le module :ref:`Population <population>` intégré à Elan ou le module ``Centroïdes`` qui est natif de QGIS.

En contexte international
^^^^^^^^^^^^^^^^^^^^^^^^^

* ``MNT`` : le MNT ou DEM en anglais (Digital Elevation Model), est *a priori* disponible sur l'ensemble des territoires du monde à une maille de 30 m via différentes plateformes.

.. note::
    Plus le MNT est précis, plus les sorties du module ``Réseau`` seront pertinentes. 
    **Nous vous recommandons donc de regarder si des données MNT à 10 m ou 5 m sont disponibles dans votre contexte national**. 
    A défaut, utilisez le MNT à 30 m, mais gardez en tête que la précision du MNT impacte les résultats du module ``Réseau`` (surestimation du nombre de stations de pompage). 

.. _alaska_edu:

.. tip::
    Si vous ne disposez pas de données locales de MNT à une maille inférieure à 30 m, vous pouvez consulter le site ASF Data Search à l'adresse suivante : https://search.asf.alaska.edu/#/ et suivre les étapes indiquées pour essayer de trouver une tuile de MNT à rune maille de 12.5 m sur votre zone.

    * Sélectionner Geographic Search pour Search type (bulle 1).
    * Sélectionner ALOS PALSAR pour Data Set (bulle 2).
    * Indiquer votre zone sur la carte (bulle 3, carré jaune).
    * Cliquer sur SEARCH (bulle 4).
    * Regarder si parmi les tuiles proposées à gauche, il y en a une où un fichier High-Res Terrain Corrected est proposé au téléchargement (bulle 5).
    * Si oui, il vous faudra créer un compte (email et mot de passe) pour pouvoir télécharger le fichier.

.. image:: _static/alaska-edu.png
      :width: 700

* ``routes`` et ``bâtiments``: le module :ref:`Routes et bâtiments <routes>` d'Elan vous permet d'extraire les données OpenStreetMap sur une zone définie.

.. attention::
    La couche ``bâtiments`` obtenue sera de type *polygone* et non *point*. Elle devra donc être transformée via le module :ref:`Population <population>` intégré à Elan ou le module ``Centroïdes`` qui est natif de QGIS.

.. _open_buildings:

.. note::
     Si votre zone d'étude est située dans l'hémisphère Sud, Open Buildings peut constituer une alternative intéressante à OpenStreetMap pour les bâtiments. Pour plus d'informations : https://sites.research.google/gr/open-buildings/.


Utilisation des modules ``Routes et bâtiments`` et ``Population``
-----------------------------------------------------------------

.. _routes:

Module ``Routes et bâtiments``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Le module ``Routes et bâtiments`` permet l'extraction des entités routes et bâtiments se trouvant dans une zone définie par l'utilisateur (couche de type *polygone*).
L'extraction se fait à partir `d'OpenStreetMap <https://www.openstreetmap.org>`_ qui rassemble des données cartographiques à l'échelle mondiale. 
OpenStreetMap est un outil ouvert et collaboratif.

.. note::
     La qualité des données OpenStreetMap est variable selon les zones du globe : elle peut être d'une qualité moindre par 
     rapport à des données nationales (moins de bâtiments reportés par exemple) comme de qualité équivalente. Dans 
     le dernier cas, l'utilisation du module ``Routes et bâtiments`` peut parfois s'avérer plus simple que l'usage des 
     données nationales (téléchargement, post-traitement).

     Bon à savoir : un très léger décalage en termes de georéférencement peut caractériser les données extraites à partir d'OpenStreetMap.

**Utilisation du module**

**1.** Chercher ``elan`` dans la boîte à outils de traitements et sélectionner ``Routes et bâtiments``.

.. image:: _static/start-r+b.png
      :width: 352

**2.** Indiquer la couche *polygone* qui délimite la zone à extraire (bulle 1), cocher *Reprojection des couches dans le SCR du projet* (bulle 2) puis exécuter (bulle 3).

.. image:: _static/r+b.png
      :width: 615

**3.** Après exécution du module, vous disposez de **cinq sorties** :

* ``Bâtiments`` : couche de type *polygone* avec les bâtiments tels que définis dans OpenStreetMap

* ``Bâtiments fusionnés`` : couche de type *polygone* obtenue après fusion des bâtiments adjacents

* ``Centroïdes des bâtiments`` : couche de type *point* qui contient les centroïdes de la couche ``Bâtiments`` 

* ``Centroïdes des bâtiments fusionnés`` : couche de type *point* qui contient les centroïdes de la couche ``Bâtiments fusionnés``

* ``Routes`` : couche de type *ligne* avec les routes telles que définies OpenStreetMap

Les couches **bâtiments** peuvent constituer des entrées pour le **module** ``Population``.

Les couches **centroïdes et routes** peuvent être utilisées en entrée du **module** ``Réseau``.

.. tip:: 
    Lorsque vous lancez le module, vous pouvez laisser l'option par défaut de *Créer une couche temporaire* pour les cinq sorties et n'enregistrer que celles dont vous
    avez besoin / celles qui vous donnent le plus satisfaction au regard de votre connaissance du terrain et de la problématique.

    Par exemple : 

          .. image:: _static/save-temp.png
               :width: 700

.. _population:

Module ``Population``
^^^^^^^^^^^^^^^^^^^^^

Le module ``Population`` permet de **répartir un nombre connu d'individus au sein des bâtiments de la zone**. 
La répartition se fait **en appliquant la méthode surfacique** qui considère l'emprise des bâtiments : plus un 
bâtiment occupe une surface importante, plus le nombre d'individus associé sera lui aussi important.

Pour plus d'informations sur la méthode de répartition utilisée :

    *Lwin et al., (2009). A GIS Approach to Estimation of Building Population for Micro-spatial Analysis. Transactions in GIS, 13(4):401-414, doi: 10.1111/j.1467-9671.2009.01171.x*

.. note::
    Si vous souhaitez considérer un **nombre moyen d'individus par bâtiment** identique pour chacun d'entre eux, 
    **utilisez directement le module** ``Réseau`` où vous préciserez le nombre moyen d'individus par bâtiment qui est à
    considérer. 

**Utilisation du module**

.. _start-pop:

**1.** Chercher ``elan`` dans la boîte à outils de traitements et sélectionner ``Population``.

.. image:: _static/start-pop.png
    :width: 354

**2.** Indiquer une valeur de population (bulle 1), renseigner la couche de bâtiments (bulle 2), enregistrer dans
un fichier (bulle 3) puis exécuter (bulle 4).

.. attention::
    La couche de bâtiments doit être de type *polygone*.

.. image:: _static/use-pop.png
    :width: 621

**3.** Après exécution du module, vous disposez **d'une couche de type point** avec les **centroïdes des bâtiments** de la zone.
A chaque centroïde est associé un nombre d'individus (**attribut population**) auquel vous pouvez accéder en ouvrant la table 
attributaire de la couche.

.. tip::
    Pour **répartir plus finement la population** (par exemple par quartiers), sélectionner les entités d'un quartier avant de lancer
    le module ``Population`` et après avoir indiqué la couche, cocher **Entités sélectionnés uniquement**. 
    
    Répéter autant de fois que de quartiers de la zone. Puis utiliser l'outil ``Fusionner des couches vecteur`` de QGIS pour obtenir une seule et unique 
    couche (entrée du module ``Réseau``).


Entrées du module ``Hydraulique``
---------------------------------

.. hint::
   Cette section est en cours de construction.