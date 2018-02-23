/**
 * @requires GeoExt/Lang.js
 */

GeoExt.Lang.add("id", {

    "gxp.menu.LayerMenu.prototype": {
        layerText: "Layer"
    },

    "gxp.plugins.AddLayers.prototype": {
        addActionMenuText: "Tambahkan layer",
        addActionTip: "Tambahkan layer",
        addServerText: "Tambahkan server baru",
        addButtonText: "Add layers",
        untitledText: "Untitled",
        addLayerSourceErrorText: "Kesalahan mendapatkan kemampuan WMS ({msg}). \nSilakan cek url dan coba lagi.",
        availableLayersText: "Layer tersedia",
        expanderTemplateText: "<p><b>Abstract:</b> {abstract}</p>",
        panelTitleText: "Title",
        layerSelectionText: "Source:",
        sourceSelectOrTypeText: "Choose one or type service URL",
        doneText: "Selesai",
        uploadText: "Unggah data"
    },
    
    "gxp.plugins.BingSource.prototype": {
        title: "Layers Bing",
        roadTitle: "Jalan Bing",
        aerialTitle: "Udara Bing",
        labeledAerialTitle: "Udara Bing dengan label"
    },    

    "gxp.plugins.FeatureEditor.prototype": {
        splitButtonText: "Edit",
        createFeatureActionText: "Create",
        editFeatureActionText: "Modify",
        createFeatureActionTip: "Membuat sebuah fitur",
        editFeatureActionTip: "Edit fitur"
    },
    
    "gxp.plugins.FeatureGrid.prototype": {
        displayFeatureText: "Tampilkan pada peta",
        firstPageTip: "Halaman pertama",
        previousPageTip: "Halaman sebelumnya",
        zoomPageExtentTip: "Zoom sampai batas halaman",
        nextPageTip: "Halaman berikut",
        lastPageTip: "Halaman terakhir",
        totalMsg: "Features {1} to {2} of {0}"
    },
    
    "gxp.plugins.GoogleEarth.prototype": {
        menuText: "3D Viewer",
        tooltip: "Switch to 3D Viewer"
    },
    
    "gxp.plugins.GoogleSource.prototype": {
        title: "Google Layers",
        roadmapAbstract: "Tampilkan peta jalan",
        satelliteAbstract: "Tampilkan citra satelit",
        hybridAbstract: "Tampilkan citra dengan nama jalan",
        terrainAbstract: "Tampilkan peta jalan dengan peta medan"
    },

    "gxp.plugins.LayerProperties.prototype": {
        menuText: "Properti layer",
        toolTip: "Properti layer"
    },
    
    "gxp.plugins.LayerTree.prototype": {
        shortTitle: "Layer-layer",
        rootNodeText: "Layer-layer",
        overlayNodeText: "Superimposisi",
        baseNodeText: "Layer dasar"
    },

    "gxp.plugins.LayerManager.prototype": {
        baseNodeText: "Layer dasar"
    },

    "gxp.plugins.Legend.prototype": {
        menuText: "Tampilkan legend",
        tooltip: "Tampilkan legend"
    },

    "gxp.plugins.LoadingIndicator.prototype": {
        loadingMapMessage: "Loading Map..."
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
        buttonText: "Pengukuran",
        lengthMenuText: "Panjang",
        areaMenuText: "Luas",
        lengthTooltip: "Pengukuran panjang",
        areaTooltip: "Pengukuran luas",
        measureTooltip: "Pengukuran"
    },

    "gxp.plugins.Navigation.prototype": {
        menuText: "Pan peta",
        tooltip: "Pan peta"
    },

    "gxp.plugins.NavigationHistory.prototype": {
        previousMenuText: "Zoom ke luas sebelumnya",
        nextMenuText: "Zoom ke luas setelahnya",
        previousTooltip: "Zoom ke luas sebelumnya",
        nextTooltip: "Zoom ke luas setelahnya"
    },

    "gxp.plugins.OSMSource.prototype": {
        title: "OpenStreetMap Layers",
        mapnikAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/'>OpenStreetMap</a>",
        osmarenderAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/'>OpenStreetMap</a>"
    },

    "gxp.plugins.Print.prototype": {
        buttonText:"Cetak",
        menuText: "Cetak peta",
        tooltip: "Cetak peta",
        previewText: "Preview cetak",
        notAllNotPrintableText: "Tidak semua layer dapat dicetak",
        nonePrintableText: "Tidak ada peta yang dapat dicetak"
    },

    "gxp.plugins.MapQuestSource.prototype": {
        title: "MapQuest Layers",
        osmAttribution: "Tiles Courtesy of <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        osmTitle: "MapQuest OpenStreetMap",
        naipAttribution: "Tiles Courtesy of <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        naipTitle: "Citra MapQuest"
    },

    "gxp.plugins.QueryForm.prototype": {
        queryActionText: "Query",
        queryMenuText: "Queryable Layer",
        queryActionTip: "Query layer yang dipilih",
        queryByLocationText: "Query by current map extent",
        queryByAttributesText: "Query atribut",
        queryMsg: "Querying...",
        cancelButtonText: "Batal",
        noFeaturesTitle: "Tidak sesuai",
        noFeaturesMessage: "Permintaan anda tidak berhasil."
    },

    "gxp.plugins.RemoveLayer.prototype": {
        removeMenuText: "Hapus layer",
        removeActionTip: "Hapus layer"
    },

    "gxp.plugins.Styler.prototype": {
        menuText: "Edit Styles",
        tooltip: "Manage layer styles"

    },

    "gxp.plugins.WMSGetFeatureInfo.prototype": {
        buttonText:"Identify",
        infoActionTip: "Get Feature Info",
        popupTitle: "Info fitur"
    },

    "gxp.plugins.Zoom.prototype": {
        zoomMenuText: "Zoom Box",
        zoomInMenuText: "Memperbesar",
        zoomOutMenuText: "Memperkecil",
        zoomTooltip: "Zoom by dragging a box",
        zoomInTooltip: "Memperbesar",
        zoomOutTooltip: "Memperkecil"
    },
    
    "gxp.plugins.ZoomToExtent.prototype": {
        menuText: "Pembesaran maksimum",
        tooltip: "Pembesaran maksimum"
    },
    
    "gxp.plugins.ZoomToDataExtent.prototype": {
        menuText: "Pembesaran batas layer",
        tooltip: "Pembesaran batas layer"
    },

    "gxp.plugins.ZoomToLayerExtent.prototype": {
        menuText: "Pembesaran batas layer",
        tooltip: "Pembesaran batas layer"
    },
    
    "gxp.plugins.ZoomToSelectedFeatures.prototype": {
        menuText: "Pembesaran pada fitur terpilih",
        tooltip: "Pembesaran pada fitur terpilih"
    },

    "gxp.FeatureEditPopup.prototype": {
        closeMsgTitle: "Simpan update?",
        closeMsg: "Fitur belum di simpan. Apakah ingin disimpan?",
        deleteMsgTitle: "Hapus Fitur?",
        deleteMsg: "Anda yakin untuk menghapus fitur ini?",
        editButtonText: "Edit",
        editButtonTooltip: "Jadikan fitur dapat diedit",
        deleteButtonText: "Hapus",
        deleteButtonTooltip: "Hapus fitur ini",
        cancelButtonText: "Batal",
        cancelButtonTooltip: "Berhenti mengedit, batalkan perubahan",
        saveButtonText: "Simpan",
        saveButtonTooltip: "Simpan Update"
    },
    
    "gxp.FillSymbolizer.prototype": {
        fillText: "Isikan warna",
        colorText: "Warna",
        opacityText: "Kepekatan"
    },
    
    "gxp.FilterBuilder.prototype": {
        builderTypeNames: ["any", "all", "none", "not all"],
        preComboText: "Sesuai",
        postComboText: "of the following:",
        addConditionText: "tambahkan kondisi",
        addGroupText: "tambahkan grup",
        removeConditionText: "Hilangkan kondisi"
    },
    
    "gxp.grid.CapabilitiesGrid.prototype": {
        nameHeaderText : "Nama",
        titleHeaderText : "Judul",
        queryableHeaderText : "Queryable",
        layerSelectionLabel: "Melihat data dari:",
        layerAdditionLabel: "atau tambahkan sebagai server baru.",
        expanderTemplateText: "<p><b>Abstract:</b> {abstract}</p>"
    },
    
    "gxp.PointSymbolizer.prototype": {
        graphicCircleText: "Lingkaran",
        graphicSquareText: "square",
        graphicTriangleText: "Segitiga",
        graphicStarText: "Bintang",
        graphicCrossText: "Silang",
        graphicXText: "x",
        graphicExternalText: "dari luar",
        urlText: "URL",
        opacityText: "Kepekatan",
        symbolText: "Simbol",
        sizeText: "Ukuran",
        rotationText: "Rotasi"
    },

    "gxp.QueryPanel.prototype": {
        queryByLocationText: "Query lokasi",
        currentTextText: "Sejauh ini",
        queryByAttributesText: "Query atribut",
        layerText: "Layer"
    },
    
    "gxp.RulePanel.prototype": {
        scaleSliderTemplate: "{scaleType} Scale 1:{scale}",
        labelFeaturesText: "Label Fitur",
        labelsText: "Labels",
        basicText: "Basic",
        advancedText: "Tingkat lanjut",
        limitByScaleText: "Batasan oleh skala",
        limitByConditionText: "Batasan oleh kondisi",
        symbolText: "Simbol",
        nameText: "Nama"
    },
    
    "gxp.ScaleLimitPanel.prototype": {
        scaleSliderTemplate: "{scaleType} Scale 1:{scale}",
        minScaleLimitText: "Min scale limit",
        maxScaleLimitText: "Batas skala maksimum"
    },
    
    "gxp.StrokeSymbolizer.prototype": {
        solidStrokeName: "solid",
        dashStrokeName: "dash",
        dotStrokeName: "dot",
        titleText: "Stroke",
        styleText: "Style",
        colorText: "Color",
        widthText: "Width",
        opacityText: "Opacity"
    },
    
    "gxp.StylePropertiesDialog.prototype": {   
        titleText: "General",
        nameFieldText: "Name",
        titleFieldText: "Title",
        abstractFieldText: "Abstract"
    },
    
    "gxp.TextSymbolizer.prototype": {
        labelValuesText: "Label nilai",
        haloText: "Halo",
        sizeText: "Ukuran"
    },
    
    "gxp.WMSLayerPanel.prototype": {
        aboutText: "Tentang Program",
        titleText: "Judul",
        nameText: "Nama",
        descriptionText: "Deskripsi",
        displayText: "Tampilan",
        opacityText: "Kecerahan",
        formatText: "Format",
        transparentText: "Transparent",
        cacheText: "Cache",
        cacheFieldText: "Menggunakan versi cached",
        stylesText: "Styles",
        infoFormatText: "Info format",
        infoFormatEmptyText: "Select a format"
    },

    "gxp.EmbedMapDialog.prototype": {
        publishMessage: "Peta anda siap dipublikasikan melalui web! Cukup salin HTML berikut untuk meletakkan peta dalam situs web Anda:",
        heightLabel: 'Tinggi',
        widthLabel: 'Lebar',
        mapSizeLabel: 'Ukuran peta',
        miniSizeLabel: 'Mini',
        smallSizeLabel: 'Kecil',
        premiumSizeLabel: 'Premium',
        largeSizeLabel: 'Besar'
    },
    
    "gxp.WMSStylesDialog.prototype": {
         addStyleText: "Tambah",
         addStyleTip: "Tambah style baru",
         chooseStyleText: "Choose style",
         deleteStyleText: "Hilangkan",
         deleteStyleTip: "Hapus style yang dipilih",
         editStyleText: "Edit",
         editStyleTip: "Edit style yang dipilih",
         duplicateStyleText: "Duplikat",
         duplicateStyleTip: "Duplikat style yang dipilih",
         addRuleText: "Tambah",
         addRuleTip: "Tambah Rule baru",
         newRuleText: "New Rule",
         deleteRuleText: "Hilangkan",
         deleteRuleTip: "Hapus Rule yang dipilih",
         editRuleText: "Edit",
         editRuleTip: "Edit ule yang dipilih",
         duplicateRuleText: "Duplikat",
         duplicateRuleTip: "Duplikat style yang dipilih",
         cancelText: "Batal",
         saveText: "Save",
         styleWindowTitle: "User Style: {0}",
         ruleWindowTitle: "Style Rule: {0}",
         stylesFieldsetTitle: "Styles",
         rulesFieldsetTitle: "Rules"
    },

    "gxp.LayerUploadPanel.prototype": {
        titleLabel: "Judul",
        titleEmptyText: "Judul Layer",
        abstractLabel: "Deskripsi",
        abstractEmptyText: "Deskripsi Layer",
        fileLabel: "Data",
        fieldEmptyText: "Pencarian arsip data...",
        uploadText: "Pengisian",
        waitMsgText: "Mengisi Data anda...",
        invalidFileExtensionText: "Ekstensi file harus salah satu: ",
        optionsText: "Pilihan",
        workspaceLabel: "Ruang Kerja",
        workspaceEmptyText: "Ruang kerja Default",
        dataStoreLabel: "Penyimpanan",
        dataStoreEmptyText: "Create new store",
        defaultDataStoreEmptyText: "Penyimpanan data Default"
    },
    
    "gxp.NewSourceDialog.prototype": {
        title: "Add New Server...",
        cancelText: "Cancel",
        addServerText: "Add Server",
        invalidURLText: "Enter a valid URL to a WMS endpoint (e.g. http://example.com/geoserver/wms)",
        contactingServerText: "Contacting Server..."
    },

    "gxp.ScaleOverlay.prototype": { 
        zoomLevelText: "Zoom level"
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
