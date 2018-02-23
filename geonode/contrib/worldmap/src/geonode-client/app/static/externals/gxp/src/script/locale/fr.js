/**
 * @requires GeoExt/Lang.js
 */

GeoExt.Lang.add("fr", {

    "gxp.plugins.AddLayers.prototype": {
        addActionMenuText: "Ajouter des couches",
        addActionTip: "Ajouter des couches",
        addServerText: "Ajouter un nouveau serveur",
        untitledText: "Sans titre",
        addLayerSourceErrorText: "Impossible d'obtenir les capacités WMS ({msg}).\nVeuillez vérifier l'URL et essayez à nouveau.",
        availableLayersText: "Couches disponibles",
        uploadText: "Télécharger des données",
        layerSelectionText: "Source:",
        sourceSelectOrTypeText: "Choisissez un URL ou taper l'URL de service",
        doneText: "Terminé"
    },
    
    "gxp.plugins.BingSource.prototype": {
        title: "Couches Bing",
        roadTitle: "Bing routes",
        aerialTitle: "Bing images aériennes",
        labeledAerialTitle: "Bing images aériennes avec étiquettes"
    },    

    "gxp.plugins.FeatureEditor.prototype": {
        splitButtonText: "Rédiger",
        createFeatureActionText: "Créer",
        editFeatureActionText: "Modifier",
        createFeatureActionTip: "Créer un nouvel objet",
        editFeatureActionTip: "Modifier un objet existant"
    },
    
    "gxp.plugins.FeatureGrid.prototype": {
        displayFeatureText: "Afficher sur la carte",
        firstPageTip: "Première page",
        previousPageTip: "Page précédente",
        zoomPageExtentTip: "Zoom sur la page",
        nextPageTip: "Page suivante",
        lastPageTip: "Dernière page",
        totalMsg: "Caractéristiques {1} à {2} de {0}"
    },

    "gxp.plugins.GoogleEarth.prototype": {
        menuText: "Passer à la visionneuse 3D",
        tooltip: "Passer à la visionneuse 3D"
    },
    
    "gxp.plugins.GoogleSource.prototype": {
        title: "Couches Google",
        roadmapAbstract: "Carte routière",
        satelliteAbstract: "Images satellite",
        hybridAbstract: "Images avec routes",
        terrainAbstract: "Carte routière avec le terrain",
        roadmapTitle: "Google Routière",       
        hybridTitle: "Google Hybrid",
        satelliteTitle: "Google Satellite",
        terrainTitle: "Google Terrain"
    },

    "gxp.plugins.LayerProperties.prototype": {
        menuText: "Propriétés de la couche",
        toolTip: "Propriétés de la couche"
    },
    
    "gxp.plugins.LayerTree.prototype": {
        shortTitle: "Couches",
        rootNodeText: "Couches",
        overlayNodeText: "Surimpressions",
        baseNodeText: "Couches"
    },

    "gxp.plugins.LayerManager.prototype": {
        baseNodeText: "Couche"
    },

    "gxp.plugins.Legend.prototype": { 
        menuText: "Légende",
        tooltip: "Légende"
    },

    "gxp.plugins.Measure.prototype": {
        buttonText: "Mesure",
        lengthMenuText: "Longueur",
        areaMenuText: "Surface",
        lengthTooltip: "Mesure de longueur",
        areaTooltip: "Mesure de surface",
        measureTooltip: "Mesure"
    },

    "gxp.plugins.Navigation.prototype": {
        menuText: "Panner la carte",
        tooltip: "Panner la carte"
    },

    "gxp.plugins.NavigationHistory.prototype": {
        previousMenuText: "Position précédente",
        nextMenuText: "Position suivante",
        previousTooltip: "Position précédente",
        nextTooltip: "Position suivante"
    },

    "gxp.plugins.LoadingIndicator.prototype": {
        loadingMapMessage: "Chargement de la carte..."
    },

    "gxp.plugins.MapBoxSource.prototype": {
        title: "Couches MapBox",
        blueMarbleTopoBathyJanTitle: "Topographie et Bathymétrie Blue Marble (janvier)",
        blueMarbleTopoBathyJulTitle: "Topographie et Bathymétrie Blue Marble (juillet)",
        blueMarbleTopoJanTitle: "Topographie Blue Marble (janvier)",
        blueMarbleTopoJulTitle: "Topographie Blue Marble (juillet)",
        controlRoomTitle: "Salle de commande",
        geographyClassTitle: "Cours de géographie",
        naturalEarthHypsoTitle: "Hypsométrie du monde",
        naturalEarthHypsoBathyTitle: "Hypsométrie & Bathymétrie du monde",
        naturalEarth1Title: "Monde I",
        naturalEarth2Title: "Monde II",
        worldDarkTitle: "Monde (foncé)",
        worldLightTitle: "Monde (éclair)",
        worldPrintTitle: "Imprimer le monde"
    },

    "gxp.plugins.OSMSource.prototype": {
        title: "Couches OpenStreetMap",
        mapnikAttribution: "Données CC-By-SA par <a href='http://openstreetmap.org/'>OpenStreetMap</a>",
        osmarenderAttribution: "Données CC-By-SA par <a href='http://openstreetmap.org/'>OpenStreetMap</a>"
    },

    "gxp.plugins.Print.prototype": {
        buttonText:"Imprimer",
        menuText: "Imprimer la carte",
        tooltip: "Imprimer la carte",
        previewText: "Aperçu avant impression",
        notAllNotPrintableText: "Toutes les couches ne peuvent pas être imprimées",
        nonePrintableText: "Aucune de vos couches ne peut être imprimée"
    },

    "gxp.plugins.MapQuestSource.prototype": {
        title: "MapQuest Layers",
        osmAttribution: "Avec la permission de tuiles <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        osmTitle: "MapQuest OpenStreetMap",
        naipAttribution: "Avec la permission de tuiles <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        naipTitle: "MapQuest Imagery"
    },

    "gxp.plugins.QueryForm.prototype": {
        queryActionText: "Interrogation",
        queryMenuText: "Couche de requêtes",
        queryActionTip: "Interroger la couche sélectionnée",
        queryByLocationText: "Interroger par la zone de la carte actuelle",
        queryByAttributesText: "Requête par attributs"
    },

    "gxp.plugins.RemoveLayer.prototype": {
        removeMenuText: "Enlever la couche",
        removeActionTip: "Enlever la couche"
    },

    "gxp.plugins.WMSGetFeatureInfo.prototype": {
        buttonText:"Identifier",
        infoActionTip: "Acquérir les informations",
        popupTitle: "Info sur l'objet"
    },

    "gxp.plugins.Zoom.prototype": {
        zoomMenuText: "Zone zoom",
        zoomInMenuText: "Zoom avant",
        zoomOutMenuText: "Zoom arrière",
        zoomTooltip: "Zoom en tirant un carré",
        zoomInTooltip: "Zoom avant",
        zoomOutTooltip: "Zoom arrière"
    },
    
    "gxp.plugins.ZoomToExtent.prototype": {
        menuText: "Zoomer sur la carte max",
        tooltip: "Zoomer sur la carte max"
    },
    
    "gxp.plugins.ZoomToDataExtent.prototype": {
        menuText: "Zoomer sur la couche",
        tooltip: "Zoomer sur la couche"
    },

    "gxp.plugins.ZoomToLayerExtent.prototype": {
        menuText: "Zoomer sur la couche",
        tooltip: "Zoomer sur la couche"
    },
    
    "gxp.plugins.ZoomToSelectedFeatures.prototype": {
        menuText: "Zoomer sur les objets sélectionnés",
        tooltip: "Zoomer sur les objets sélectionnés"
    },

    "gxp.FeatureEditPopup.prototype": {
        closeMsgTitle: "Enregistrer les modifications ?",
        closeMsg: "Cet objet a des modifications non enregistrées. Voulez-vous enregistrer vos modifications ?",
        deleteMsgTitle: "Supprimer l'objet ?",
        deleteMsg: "Etes-vous sûr de vouloir supprimer cet objet ?",
        editButtonText: "Modifier",
        editButtonTooltip: "Modifier cet objet",
        deleteButtonText: "Supprimer",
        deleteButtonTooltip: "Supprimer cet objet",
        cancelButtonText: "Annuler",
        cancelButtonTooltip: "Arrêter de modifier, annuler les modifications",
        saveButtonText: "Enregistrer",
        saveButtonTooltip: "Enregistrer les modifications"
    },
    
    "gxp.FillSymbolizer.prototype": {
        fillText: "Remplir",
        colorText: "Couleur",
        opacityText: "Opacité"
    },
    
    "gxp.FilterBuilder.prototype": {
        builderTypeNames: ["Tout", "tous", "aucun", "pas tout"],
        preComboText: "Match",
        postComboText: "de ce qui suit:",
        addConditionText: "Ajouter la condition",
        addGroupText: "Ajouter un groupe",
        removeConditionText: "Supprimer la condition"
    },
    
    "gxp.grid.CapabilitiesGrid.prototype": {
        nameHeaderText : "Nom",
        titleHeaderText : "Titre",
        queryableHeaderText : "Interrogeable",
        layerSelectionLabel: "Voir les données disponibles à partir de :",
        layerAdditionLabel: "ou ajouter un nouveau serveur.",
        expanderTemplateText: "<p><b>Résumé:</b> {abstract}</p>"
    },
    
    "gxp.PointSymbolizer.prototype": {
        graphicCircleText: "Cercle",
        graphicSquareText: "Carré",
        graphicTriangleText: "Triangle",
        graphicStarText: "Étoile",
        graphicCrossText: "Croix",
        graphicXText: "x",
        graphicExternalText: "Externe",
        urlText: "URL",
        opacityText: "Opacité",
        symbolText: "Symbole",
        sizeText: "Taille",
        rotationText: "Rotation"
    },

    "gxp.QueryPanel.prototype": {
        queryByLocationText: "Interrogation selon le lieu",
        currentTextText: "Mesure actuelle",
        queryByAttributesText: "Requête par attributs",
        layerText: "Calque"
    },
    
    "gxp.RulePanel.prototype": {
        scaleSliderTemplate: "{scaleType} échelle 1:{scale}",
        labelFeaturesText: "Label Caractéristiques",
        advancedText: "Avancé",
        limitByScaleText: "Limiter par l'échelle",
        limitByConditionText: "Limiter par condition",
        symbolText: "Symbole",
        nameText: "Nom"
    },
    
    "gxp.ScaleLimitPanel.prototype": {
        scaleSliderTemplate: "{scaleType} échelle 1:{scale}",
        maxScaleLimitText: "Échelle maximale"
    },
    
    "gxp.TextSymbolizer.prototype": {
        labelValuesText: "Label valeurs",
        haloText: "Halo",
        sizeText: "Taille"
    },
    
    "gxp.WMSLayerPanel.prototype": {
        aboutText: "A propos",
        titleText: "Titre",
        nameText: "Nom",
        descriptionText: "Description",
        displayText: "Affichage",
        opacityText: "Opacité",
        formatText: "Format",
        transparentText: "Transparent",
        cacheText: "Cache",
        cacheFieldText: "Utiliser la version mise en cache",
        infoFormatText: "Info format",
        infoFormatEmptyText: "Choisissez un format"
    },

    "gxp.EmbedMapDialog.prototype": {
        publishMessage: "Votre carte est prête à être publiée sur le web. Il suffit de copier le code HTML suivant pour intégrer la carte dans votre site Web :",
        heightLabel: 'Hauteur',
        widthLabel: 'Largeur',
        mapSizeLabel: 'Taille de la carte',
        miniSizeLabel: 'Mini',
        smallSizeLabel: 'Petit',
        premiumSizeLabel: 'Premium',
        largeSizeLabel: 'Large'
    },

    "gxp.LayerUploadPanel.prototype": {
        titleLabel: "Titre",
        titleEmptyText: "Titre de la couche",
        abstractLabel: "Description",
        abstractEmptyText: "Description couche",
        fileLabel: "Données",
        fieldEmptyText: "Parcourir pour ...",
        uploadText: "Upload",
        waitMsgText: "Transfert de vos données ...",
        invalidFileExtensionText: "L'extension du fichier doit être : ",
        optionsText: "Options",
        workspaceLabel: "Espace de travail",
        workspaceEmptyText: "Espace de travail par défaut",
        dataStoreLabel: "Magasin de données",
        dataStoreEmptyText: "Créer une nouvelle réserve",
        defaultDataStoreEmptyText: "Réserve de données par défaut"
    },

    "gxp.NewSourceDialog.prototype": {
        title: "Ajouter un nouveau serveur...",
        cancelText: "Annuler",
        addServerText: "Ajouter un serveur",
        invalidURLText: "Indiquez l'URL valide d'un serveur WMS (e.g. http://example.com/geoserver/wms)",
        contactingServerText: "Interrogation du serveur..."
    },

    "gxp.ScaleOverlay.prototype": { 
        zoomLevelText: "Niveau de zoom"
    },
    
    "gxp.plugins.ArcGISCacheSource.prototype": {
        noLayersTitle: "Aucune couche ArcGIS n'a été trouvée.",
        noLayersText: " Aucune couche avec une projection compatible (Web Mercator) n'a été trouvée. "
    },    
    
    "gxp.plugins.ArcRestSource.prototype": {
        noLayersTitle: "Aucune couche ArcGIS n'a été trouvée.",
        noLayersText: "Aucune couche avec une projection compatible (Web Mercator) n'a été trouvée à "
    },
    
    "gxp.plugins.MapShare.prototype": { 
    	text: "Partager cette carte",
    	toolTip: "Informations sur cette carte et les liens de téléchargement"
    },
    
    "gxp.plugins.AnnotationTool.prototype": {
        errorTitle: "Une erreur s'est produite lors de la création de l'annotation.",
        noteText: "Note",        
        notesText: "Notes",
        showNotesText: "Montrer les notes",
        editNotesText: "Rédiger les notes",       
        addNoteText: "Ajouter une note",        
        newNoteText: "Nouvelle note",
        projection: "EPSG:4326",
        pointText: "Point",
        lineText: "Ligne",
        polygonText: "Forme",
        saveFailTitle: "L'enregistrement de la note a échoué",
        saveFailText: "La modification a échoué. Vous n'avez peut-être pas les autorisations pour sauvegarder cette note.",        
        saveText: "Sauvegarder",        
        editText: "Rédiger",       
        deleteText: "Supprimer",        
        cancelText: "Annuler",        
        titleText: "Titre"
    },
    
    "gxp.SearchBar.prototype": {
    	emptyText: 'Chercher...',
    	searchText: 'Chercher',
    	noSearchableLayersTitle: 'Aucune couche ne peut être intérroger.',
    	noSearchableLayersMsg: "Il n'y a pas de couche interrogeable dans cette carte. Vous devez avoir au moins une couche visible avec des champs interrogeable dans la carte.",
    	searchTermTitle: "Terme à rechercher obligatoire.", 
    	searchTermText: "Veuillez entrer un terme à rechercher.",
    	resetText: "Réinitialiser"
    },
    
    "gxp.plugins.PrintPage.prototype": {
        menuText: "Imprimer la carte",
        tooltip: "Imprimer la carte",
        buttonText: "Imprimer"
    },
    
    "gxp.plugins.CoordinateTool.prototype": {
        title: "Coordonnées de la carte (longitude, latitude)",
        infoActionTip: "Prendre les coordonnées de la position de la souris",
        coordinatePositionText: "Position des coordonnées"
    },
    
    "gxp.plugins.FeedSource.prototype": {
        title: "Source d'alimentation"
    },
    
    "gxp.plugins.HGLSource.prototype": {
        title: "Bibliothèque géospatiale d'Harvard"
    },
    
    "gxp.plugins.HGLFeedSource.prototype" : {
        title: "Source d'alimentation HGL "
    },
    
    "gxp.plugins.PicasaFeedSource.prototype" : {
        title: 'Picasa'
    },
    
    "gxp.plugins.YouTubeFeedSource.prototype" : {
        title: 'YouTube'
    },
    
    "gxp.plugins.GeoLocator.prototype": {
        infoActionTip: "Trouver mon emplacement",
        locationFailedText: "Détection de l'emplacement a échoué"
    },
    
    "gxp.plugins.LayerShare.prototype": {
        menuText: "Partager cette couche",
        toolTip: "Informations de la couche et les liens de téléchargement"
    },

    "gxp.plugins.MapShare.prototype": {
        text: "Partager ma carte",
        toolTip: "Informations de la carte et les liens de téléchargement"
    },    

    "gxp.plugins.AddCategory.prototype": {
        addCategoryMenuText:"Ajouter une catégorie",
        addCategoryActionTipText:"Ajouter une catégorie à la hiérarchie des couches",
        categoryNameText: "Nom de la catégorie:"
    },    
    
    "gxp.plugins.RemoveCategory.prototype": {
    	removeCategoryActionText:"Supprimer la catégorie",
    	removeCategoryActionTipText: "Supprimer cette catégorie et toutes ses couches de la carte",
    	cannotRemoveText: " Cette catégorie ne peut pas être supprimée."
    },
    
    "gxp.plugins.RenameCategory.prototype": {
        renameCategoryActionText:"Modifier le nom de la catégorie",
        renameCategoryActionTipText:"Changer le nom de la catégorie",
        cannotRenameText: "Vous n'êtes pas autorisé à changer le nom de cette catégorie"
    },
    
    "gxp.LinkEmbedMapDialog.prototype": {
    	linkMessage: 'Veuillez copier-coller ce lien dans un email'
    },    
    
    "gxp.plugins.GeoNodeQueryTool.prototype" : {
        infoActionTip: "Voir les informations de la caractéristique",
        popupTitle: "Infos caractéristique",
        resetTitle: "Réinitialiser",
        resetToolTipText: " Enlever les caractéristiques"
    },
    
    "gxp.plugins.MapRevisionTool.prototype" : {
    	infoActionTip: 'Voir la liste des modifications de cette carte',
    	toolText: 'Modifications',
    	windowTitle: "Historique des modifications de la carte"
    },
    
    "gxp.plugins.GazetteerTool.prototype" : {
        infoActionTip: "Entrer le nom d'un lieu à localiser",
        toolText: 'Index géographique',
        searchingText: 'Cherche en cours...',
        fromText: 'De: YYYY-MM-JJ',
        toText: 'A: YYYY-MM-JJ',
        datesText: 'Dates',
        geocodersText: 'Géocodes', 
        advancedText: 'Avancé',
        sourceText: 'Source',
        startDateText: 'A partir de',
        endDateText: 'Date de fin',  	
        placenameText: 'Nom de lieu',
        coordinatesText: 'Coordonnées'  	
    },
    
    "gxp.plugins.StreetViewTool.prototype" : {
    	toolText: "Street View",
    	streetViewTitle: "Google Street View",  	
    	infoActionTip: "Cliquez sur la carte pour voir Google Street View"
    }
});