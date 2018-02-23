/**
 * @requires GeoExt/Lang.js
 */

GeoExt.Lang.add("de", {

    "gxp.menu.LayerMenu.prototype": {
        layerText: "Layer"
    },

    "gxp.plugins.AddLayers.prototype": {
        addActionMenuText: "Layer hinzufügen",
        addActionTip: "Layer hinzufügen",
        addServerText: "Server hinzufügen",
        addButtonText: "Layer hinzufügen",
        untitledText: "ohne Titel",
        addLayerSourceErrorText: "Fehler beim Abfragen der WMS Capabilities ({msg}).\nBitte URL prüfen und erneut versuchen.",
        availableLayersText: "verfügbare Layer",
        expanderTemplateText: "<p><b>Kurzbeschreibung:</b> {abstract}</p>",
        panelTitleText: "Titel",
        layerSelectionText: "Quelle:",
        sourceSelectOrTypeText: "Auswählen oder Service URL engeben",
        doneText: "Fertig",
        uploadText: "Daten hochladen"
    },
    
    "gxp.plugins.BingSource.prototype": {
        title: "Bing Layer",
        roadTitle: "Bing Strassen",
        aerialTitle: "Bing Luftbilder",
        labeledAerialTitle: "Bing Luftbilder mit Beschriftung"
    },

    "gxp.plugins.FeatureEditor.prototype": {
        splitButtonText: "Editieren",
        createFeatureActionText: "Erzeugen",
        editFeatureActionText: "Bearbeiten",
        createFeatureActionTip: "neues Objekt erstellen",
        editFeatureActionTip: "bestehendes Objekt bearbeiten"
    },
    
    "gxp.plugins.FeatureGrid.prototype": {
        displayFeatureText: "auf der Karte darstellen",
        firstPageTip: "erste Seite",
        previousPageTip: "vorherige Seite",
        zoomPageExtentTip: "Zoom zur max. Ausdehnung",
        nextPageTip: "nächste Seite",
        lastPageTip: "letzte Seite",
        totalMsg: "{1} bis {2} von {0} Datensätzen"
    },

    "gxp.plugins.GoogleEarth.prototype": {
        menuText: "3D Viewer",
        tooltip: "zum 3D Viewer wechseln"
    },
    
    "gxp.plugins.GoogleSource.prototype": {
        title: "Google Layers",
        roadmapAbstract: "Strassenkarte zeigen",
        satelliteAbstract: "Luftbilder zeigen",
        hybridAbstract: "Luftbilder mit Strassennamen zeigen",
        terrainAbstract: "Strassenkarte mit Gelände zeigen"
    },

    "gxp.plugins.LayerProperties.prototype": {
        menuText: "Layer Eigenschaften",
        toolTip: "Layer Eigenschaften"
    },
    
    "gxp.plugins.LayerTree.prototype": {
        shortTitle: "Layer",
        rootNodeText: "Layer",
        overlayNodeText: "überlagernde Layer",
        baseNodeText: "Basiskarten"
    },
    
    "gxp.plugins.LayerManager.prototype": {
        baseNodeText: "Basiskarte"
    },

    "gxp.plugins.Legend.prototype": {
        menuText: "Legende zeigen",
        tooltip: "Legende zeigen"
    },

    "gxp.plugins.LoadingIndicator.prototype": {
        loadingMapMessage: "Karte laden..."
    },

    "gxp.plugins.MapBoxSource.prototype": {
        title: "MapBox Layers",
        blueMarbleTopoBathyJanTitle: "Blue Marble Topography & Bathymetry (January)",
        blueMarbleTopoBathyJulTitle: "Blue Marble Topography & Bathymetry (July)",
        blueMarbleTopoJanTitle: "Blue Marble Topography (January)",
        blueMarbleTopoJulTitle: "Blue Marble Topography (July)",
        controlRoomTitle: "Control Room",
        geographyClassTitle: "Geography Class",
        naturalEarthHypsoTitle: "Natural Earth Hypsometric",
        naturalEarthHypsoBathyTitle: "Natural Earth Hypsometric & Bathymetry",
        naturalEarth1Title: "Natural Earth I",
        naturalEarth2Title: "Natural Earth II",
        worldDarkTitle: "World Dark",
        worldLightTitle: "World Light",
        worldPrintTitle: "World Print"
    },

    "gxp.plugins.Measure.prototype": {
        buttonText: "Messen",
        lengthMenuText: "Länge",
        areaMenuText: "Fläche",
        lengthTooltip: "Länge messen",
        areaTooltip: "Fläche messen",
        measureTooltip: "Messen"
    },

    "gxp.plugins.Navigation.prototype": {
        menuText: "Kartenausschnitt verschieben",
        tooltip: "Kartenausschnitt verschieben"
    },

    "gxp.plugins.NavigationHistory.prototype": {
        previousMenuText: "Kartenausschnitt zurück",
        nextMenuText: "Kartenausschnitt vorwärts",
        previousTooltip: "Kartenausschnitt zurück",
        nextTooltip: "Kartenausschnitt vorwärts"
    },

    "gxp.plugins.OSMSource.prototype": {
        title: "OpenStreetMap Layer",
        mapnikAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/'>OpenStreetMap</a>",
        osmarenderAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/'>OpenStreetMap</a>"
    },

    "gxp.plugins.Print.prototype": {
        buttonText:"Drucken",
        menuText: "Karte drucken",
        tooltip: "Karte drucken",
        previewText: "Druckansicht",
        notAllNotPrintableText: "Es können nicht alle Layer gedruckt werden.",
        nonePrintableText: "Keiner der aktuellen Kartenlayer kann gedruckt werden."
    },

    "gxp.plugins.MapQuestSource.prototype": {
        title: "MapQuest Layers",
        osmAttribution: "Tiles Courtesy of <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        osmTitle: "MapQuest OpenStreetMap",
        naipAttribution: "Tiles Courtesy of <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        naipTitle: "MapQuest Imagery"
    },

    "gxp.plugins.QueryForm.prototype": {
        queryActionText: "Abfrage",
        queryMenuText: "Abfrage Layer",
        queryActionTip: "selektierten Layer abfragen",
        queryByLocationText: "Abfrage nach aktuellem Kartenauscchnitt",
        queryByAttributesText: "Attributabfrage",
        queryMsg: "Abfrage wird ausgeführt",
        cancelButtonText: "Abbrechen",
        noFeaturesTitle: "keine Übereinstimmung",
        noFeaturesMessage: "Ihre Abfrage liefert keine Resultate."
    },

    "gxp.plugins.RemoveLayer.prototype": {
        removeMenuText: "Layer löschen",
        removeActionTip: "Layer löschen"
    },
    
    "gxp.plugins.Styler.prototype": {
        menuText: "Style bearbeiten",
        tooltip: "Layer Styles verwalten"

    },

    "gxp.plugins.WMSGetFeatureInfo.prototype": {
        buttonText:"Objektinformation",
        infoActionTip: "Objektinformation abfragen",
        popupTitle: "Objektinformation"
    },

    "gxp.plugins.Zoom.prototype": {
        zoomMenuText: "Zoom Box",
        zoomInMenuText: "Vergrössern",
        zoomOutMenuText: "Verkleinern",
        zoomTooltip: "Zoom durch Aufziehen einer Box",
        zoomInTooltip: "Vergrössern",
        zoomOutTooltip: "Verkleinern"
    },
    
    "gxp.plugins.ZoomToExtent.prototype": {
        menuText: "Maximale Ausdehnung",
        tooltip: "Maximale Ausdehnung"
    },
    
    "gxp.plugins.ZoomToDataExtent.prototype": {
        menuText: "Auf Layer zoomen",
        tooltip: "Auf Layer zoomen"
    },

    "gxp.plugins.ZoomToLayerExtent.prototype": {
        menuText: "Auf Layer zoomen",
        tooltip: "Auf Layer zoomen"
    },
    
    "gxp.plugins.ZoomToSelectedFeatures.prototype": {
        menuText: "Auf selektierte Objekte zoomen",
        tooltip: "Auf selektierte Objekte zoomen"
    },

    "gxp.FeatureEditPopup.prototype": {
        closeMsgTitle: "Änderung speichern?",
        closeMsg: "Ungespeicherte Änderungen. Möchten Sie die Änderungen speichern?",
        deleteMsgTitle: "Objekt löschen?",
        deleteMsg: "Sind Sie sicher, dass Sie dieses Objekt löschen möchten?",
        editButtonText: "Bearbeiten",
        editButtonTooltip: "Objekt editieren",
        deleteButtonText: "Löschen",
        deleteButtonTooltip: "Objekt löschen",
        cancelButtonText: "Abbrechen",
        cancelButtonTooltip: "Bearbeitung beenden, Änderungen verwerfen.",
        saveButtonText: "Speichern",
        saveButtonTooltip: "Änderungen speichern"
    },
    
    "gxp.FillSymbolizer.prototype": {
        fillText: "Füllung",
        colorText: "Farbe",
        opacityText: "Transparenz"
    },
    
    "gxp.FilterBuilder.prototype": {
        builderTypeNames: ["beliebige", "alle", "keine", "nicht alle"],
        preComboText: "Match",
        postComboText: "der folgenden:",
        addConditionText: "Bedingung hinzufügen",
        addGroupText: "Gruppe hinzufügen",
        removeConditionText: "Bedingung entfernen"
    },
    
    "gxp.grid.CapabilitiesGrid.prototype": {
        nameHeaderText : "Name",
        titleHeaderText : "Titel",
        queryableHeaderText : "abfragbar",
        layerSelectionLabel: "Verfügbare Daten anzeigen von:",
        layerAdditionLabel: "oder neuen Server hinzufügen.",
        expanderTemplateText: "<p><b>Kurzbeschreibung:</b> {abstract}</p>"
    },
    
    "gxp.PointSymbolizer.prototype": {
        graphicCircleText: "Kreis",
        graphicSquareText: "Rechteck",
        graphicTriangleText: "Dreieck",
        graphicStarText: "Stern",
        graphicCrossText: "Kreuz",
        graphicXText: "x",
        graphicExternalText: "extern",
        urlText: "URL",
        opacityText: "Transparenz",
        symbolText: "Symbol",
        sizeText: "Grösse",
        rotationText: "Rotation"
    },

    "gxp.QueryPanel.prototype": {
        queryByLocationText: "lagebezogene Abfrage",
        currentTextText: "aktuelle Ausdehnung",
        queryByAttributesText: "Attributabfrage",
        layerText: "Layer"
    },
    
    "gxp.RulePanel.prototype": {
        scaleSliderTemplate: "{scaleType} Massstab 1:{scale}",
        labelFeaturesText: "Objekte beschriften",
        labelsText: "Beschriftung",
        basicText: "Basic",
        advancedText: "Erweitert",
        limitByScaleText: "Massstabsbeschränkung",
        limitByConditionText: "Einschränkung durch Bedingung",
        symbolText: "Symbol",
        nameText: "Name"
    },
    
    "gxp.ScaleLimitPanel.prototype": {
        scaleSliderTemplate: "{scaleType} Massstab 1:{scale}",
        minScaleLimitText: "Minimale Massstabsgrenze",
        maxScaleLimitText: "Maximale Massstabsgrenze"
    },
    
    "gxp.StrokeSymbolizer.prototype": {
        solidStrokeName: "ausgezogen",
        dashStrokeName: "gestrichelt",
        dotStrokeName: "gepunktet",
        titleText: "Linie",
        styleText: "Style",
        colorText: "Farbe",
        widthText: "Breite",
        opacityText: "Transparenz"
    },
    
    "gxp.StylePropertiesDialog.prototype": {   
        titleText: "Allgemein",
        nameFieldText: "Name",
        titleFieldText: "Titel",
        abstractFieldText: "Kurzbeschreibung"
    },
    
    "gxp.TextSymbolizer.prototype": {
        labelValuesText: "Label values",
        haloText: "Halo",
        sizeText: "Grösse"
    },
    
    "gxp.WMSLayerPanel.prototype": {
        aboutText: "Über",
        titleText: "Titel",
        nameText: "Name",
        descriptionText: "Beschreibung",
        displayText: "Anzeige",
        opacityText: "Transparenz",
        formatText: "Format",
        transparentText: "transparent",
        cacheText: "Cache",
        cacheFieldText: "Version aus dem Cache benützen",
        stylesText: "Styles",
        infoFormatText: "Info Format",
        infoFormatEmptyText: "Format auswählen"
    },

    "gxp.EmbedMapDialog.prototype": {
        publishMessage: "Ihre Karte ist für die Publikation im Web bereit. Kopieren Sie einfach den folgenden HTML-Code, um die Karte in Ihre Webseite einzubinden:",
        heightLabel: 'Höhe',
        widthLabel: 'Breite',
        mapSizeLabel: 'Kartengrösse',
        miniSizeLabel: 'Mini',
        smallSizeLabel: 'Klein',
        premiumSizeLabel: 'Premium',
        largeSizeLabel: 'Gross'
    },
    
    "gxp.WMSStylesDialog.prototype": {
         addStyleText: "Hinzufügen",
         addStyleTip: "neuen Style hinzufügen",
         chooseStyleText: "Style auswählen",
         deleteStyleText: "Löschen",
         deleteStyleTip: "selektierten Style löschen",
         editStyleText: "Bearbeiten",
         editStyleTip: "selektierten Style bearbeiten",
         duplicateStyleText: "Duplizieren",
         duplicateStyleTip: "selektierten Style duplizieren",
         addRuleText: "Hinzufügen",
         addRuleTip: "neue Regel hinzufügen",
         newRuleText: "neue Regel",
         deleteRuleText: "Entfernen",
         deleteRuleTip: "selektierte Regel löschen",
         editRuleText: "Bearbeiten",
         editRuleTip: "selektierte Regel bearbeiten",
         duplicateRuleText: "Duplizieren",
         duplicateRuleTip: "selektierte Regel duplizieren",
         cancelText: "Abbrechen",
         saveText: "Speichern",
         styleWindowTitle: "User Style: {0}",
         ruleWindowTitle: "Style Regel: {0}",
         stylesFieldsetTitle: "Styles",
         rulesFieldsetTitle: "Regeln"
    },

    "gxp.LayerUploadPanel.prototype": {
        titleLabel: "Titel",
        titleEmptyText: "Layertitel",
        abstractLabel: "Beschreibung",
        abstractEmptyText: "Layerbeschreibung",
        fileLabel: "Daten",
        fieldEmptyText: "Datenarchiv durchsuchen...",
        uploadText: "Hochladen",
        waitMsgText: "Ihre Daten werden hochgeladen...",
        invalidFileExtensionText: "Dateierweiterung muss eine sein von: ",
        optionsText: "Optionen",
        workspaceLabel: "Workspace",
        workspaceEmptyText: "Standard Workspace",
        dataStoreLabel: "Store",
        dataStoreEmptyText: "Neuen Store erzeugen",
        defaultDataStoreEmptyText: "Default Datastore"
    },
    
    "gxp.NewSourceDialog.prototype": {
        title: "neuen Server hinzufügen...",
        cancelText: "Abbrechen",
        addServerText: "Server hinzufügen",
        invalidURLText: "Fügen Sie eine gültige URL zu einem WMS ein (z.B. http://example.com/geoserver/wms)",
        contactingServerText: "Server wird kontaktiert..."
    },

    "gxp.ScaleOverlay.prototype": { 
        zoomLevelText: "Zoomstufe"
    },
    
    "gxp.plugins.ArcGISCacheSource.prototype": {
        noLayersTitle: "No ArcGIS Layers",
        noLayersText: "Could not find any layers with a compatible projection (Web Mercator) at "
    },    
    
    "gxp.plugins.ArcRestSource.prototype": {
        noLayersTitle: "No ArcGIS Layers",
        noLayersText: "Could not find any layers with a compatible projection (Web Mercator) at "
    },
    
    "gxp.plugins.MapShare.prototype": { 
    	text: "Share Map",
    	toolTip: "Map info and download links"
    },
    
    "gxp.plugins.AnnotationTool.prototype": {
        errorTitle: "Error creating annotation",
        noteText: "Note",        
        notesText: "Notes",
        showNotesText: "Show notes",
        editNotesText: "Edit notes",       
        addNoteText: "Add note",        
        newNoteText: "New note",
        projection: "EPSG:4326",
        pointText: "Point",
        lineText: "Line",
        polygonText: "Shape",
        saveFailTitle: "Could not save note",
        saveFailText: "Edit failed.  You might not have permission to save this note.",        
        saveText: "Save",        
        editText: "Edit",       
        deleteText: "Delete",        
        cancelText: "Cancel",        
        titleText: "Title"
    },
    
    "gxp.SearchBar.prototype": {
    	emptyText: 'Enter search...',
    	searchText: 'Search',
    	noSearchableLayersTitle: 'No Searchable Layers',
    	noSearchableLayersMsg: 'There are currently no searchable layers on the map.  You must have at least one visible layer with searchable fields on the map.',
    	searchTermTitle: "Search Term Required", 
    	searchTermText: "Please enter a search term",
    	resetText: "Reset"
    },
    
    "gxp.plugins.PrintPage.prototype": {
        menuText: "Print Map",
        tooltip: "Print Map",
        buttonText: "Print"
    },
    
    "gxp.plugins.CoordinateTool.prototype": {
        title: "Map Coordinates (longitude, latitude)",
        infoActionTip: "Get coordinates at the mouse position",
        coordinatePositionText: "CoordinatePosition"
    },
    
    "gxp.plugins.FeedSource.prototype": {
        title: 'Feed Source'
    },
    
    "gxp.plugins.HGLSource.prototype": {
        title: 'Harvard Geospatial Library Source'
    },
    
    "gxp.plugins.HGLFeedSource.prototype" : {
        title: 'HGL Feed Source'
    },
    
    "gxp.plugins.PicasaFeedSource.prototype" : {
        title: 'Picasa Source'
    },
    
    "gxp.plugins.YouTubeFeedSource.prototype" : {
        title: 'YouTube Source'
    },
    
    "gxp.plugins.GeoLocator.prototype": {
        infoActionTip: "Get My Location",
        locationFailedText: "Location detection failed"
    },
    
    "gxp.plugins.LayerShare.prototype": {
        menuText: "Share Layer",
        toolTip: "Layer info and download links"
    },

    "gxp.plugins.MapShare.prototype": {
        text: "Share My Map",
        toolTip: "Map info and download links"
    },    

    "gxp.plugins.AddCategory.prototype": {
        addCategoryMenuText:"Add Category",
        addCategoryActionTipText:"Add a category to the layer tree",
        categoryNameText: "Category name:"
    },    
    
    "gxp.plugins.RemoveCategory.prototype": {
    	removeCategoryActionText:"Remove Category",
    	removeCategoryActionTipText: "Remove this category and all its layers from the map",
    	cannotRemoveText: "This category cannot be removed"
    },
    
    "gxp.plugins.RenameCategory.prototype": {
        renameCategoryActionText:"Rename Category",
        renameCategoryActionTipText:"Give this category a new name",
        cannotRenameText: "This category cannot be renamed"
    },
    
    "gxp.LinkEmbedMapDialog.prototype": {
    	linkMessage: 'Paste link in email or IM'
    },    
    
    "gxp.plugins.GeoNodeQueryTool.prototype" : {
        infoActionTip: "Get Feature Info",
        popupTitle: "Feature Info",
        resetTitle: "Reset",
        resetToolTipText: " Clear all features"
    },
    
    "gxp.plugins.MapRevisionTool.prototype" : {
    	infoActionTip: 'View a list of map revisions',
    	toolText: 'Revisions',
    	windowTitle: "Map Revision History"
    },
    
    "gxp.plugins.GazetteerTool.prototype" : {
        infoActionTip: 'Enter a place name to search for',
        toolText: 'Gazetteer',
        searchingText: 'Searching...',
        fromText: 'From: YYYY-MM-DD',
        toText: 'To: YYYY-MM-DD',
        datesText: 'Dates',
        geocodersText: 'Geocoders', 
        advancedText: 'Advanced',
        sourceText: 'Source',
        startDateText: 'Start Date',
        endDateText: 'End Date',  	
        placenameText: 'Place name',
        coordinatesText: 'Coordinates'  	
    },
    
    "gxp.plugins.StreetViewTool.js" : {
    	toolText: "Google Street View",
    	streetViewTitle: "Google Street View",  	
    	infoActionTip: "Click on the map to see Google Street View"
    }

});
