/**
 * @requires GeoExt/Lang.js
 */

GeoExt.Lang.add("zh-cn", {

    "gxp.menu.LayerMenu.prototype": {
        layerText: "图层"
    },

    "gxp.plugins.AddLayers.prototype": {
        addActionMenuText: "添加图层",
        addActionTip: "添加图层",
        addServerText: "添加新的服务",
        addButtonText: "添加图层",
        untitledText: "未定义",
        addLayerSourceErrorText: "错误：无法获取WMS ({msg})。\n请确认url并重试。",
        availableLayersText: "可用图层",
        expanderTemplateText: "<p><b>概述：</b> {abstract}</p>",
        panelTitleText: "标题",
        layerSelectionText: "源:",
        sourceSelectOrTypeText: "选择一个或输入其他服务URL",
        doneText: "完成",
        uploadText: "上传图层"
    },

    "gxp.plugins.BingSource.prototype": {
        title: "Bing图层",
        roadTitle: "Bing路网",
        aerialTitle: "Bing天空",
        labeledAerialTitle: "Bing Aerial With Labels"
    },

    "gxp.plugins.FeatureEditor.prototype": {
        splitButtonText: "编辑",
        createFeatureActionText: "创建",
        editFeatureActionText: "修改",
        createFeatureActionTip: "创建新的要素",
        editFeatureActionTip: "编辑已有要素"
    },

    "gxp.plugins.FeatureGrid.prototype": {
        displayFeatureText: "在地图上显示",
        firstPageTip: "第一页",
        previousPageTip: "上一页",
        zoomPageExtentTip: "缩放到页面范围",
        nextPageTip: "下一页Next page",
        lastPageTip: "最后一页Last page",
        totalMsg: "第{0}页的第{1}到{2}个要素"
    },

    "gxp.plugins.GoogleEarth.prototype": {
        menuText: "3D视图",
        tooltip: "切换到3D视图"
    },
    
    "gxp.plugins.GoogleSource.prototype": {
        title: "谷歌图层",
        roadmapAbstract: "显示街景地图",
        satelliteAbstract: "显示卫星影像",
        hybridAbstract: "显示带街道名的影像",
        terrainAbstract: "显示带地形的街景地图"
    },
    "gxp.plugins.LayerProperties.prototype": {
        menuText: "图层属性",
        toolTip: "图层属性"
    },

    "gxp.plugins.LayerTree.prototype": {
        shortTitle: "图层",
        rootNodeText: "图层",
        overlayNodeText: "覆盖图",
        baseNodeText: "底图"
    },

    "gxp.plugins.Legend.prototype": {
        menuText: "显示比例尺",
        tooltip: "显示比例尺"
    },

    "gxp.plugins.LoadingIndicator.prototype": {
        loadingMapMessage: "加载地图..."
    },

    "gxp.plugins.MapBoxSource.prototype": {
        title: "MapBox图层",
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
        buttonText: "测量",
        lengthMenuText: "长度",
        areaMenuText: "面积",
        lengthTooltip: "测量长度",
        areaTooltip: "测量面积",
        measureTooltip: "测量"
    },

    "gxp.plugins.Navigation.prototype": {
        menuText: "浏览地图",
        tooltip: "浏览地图"
    },

    "gxp.plugins.NavigationHistory.prototype": {
        previousMenuText: "缩放到上一个范围",
        nextMenuText: "缩放到下一个范围",
        previousTooltip: "缩放到上一个范围",
        nextTooltip: "缩放到下一个范围"
    },

    "gxp.plugins.OSMSource.prototype": {
        title: "OpenStreetMap图层",
        mapnikAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/'>OpenStreetMap</a>",
        osmarenderAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/'>OpenStreetMap</a>"
    },

    "gxp.plugins.Print.prototype": {
        buttonText:"打印",
        menuText: "打印地图",
        tooltip: "打印地图",
        previewText: "打印预览",
        notAllNotPrintableText: "并非所有图层都能打印",
        nonePrintableText: "所有图层都无法打印"
    },

    "gxp.plugins.MapQuestSource.prototype": {
        title: "MapQuest图层",
        osmAttribution: "Tiles Courtesy of <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        osmTitle: "MapQuest OpenStreetMap",
        naipAttribution: "Tiles Courtesy of <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        naipTitle: "MapQuest Imagery"
    },

    "gxp.plugins.QueryForm.prototype": {
        queryActionText: "查询",
        queryMenuText: "查询图层",
        queryActionTip: "查询所选图层",
        queryByLocationText: "通过地图范围查询",
        queryByAttributesText: "通过属性查询",
        queryMsg: "查询中...",
        cancelButtonText: "取消",
        noFeaturesTitle: "没有匹配项",
        noFeaturesMessage: "您的查询未返回任何结果。"
    },

    "gxp.plugins.RemoveLayer.prototype": {
        removeMenuText: "移除图层",
        removeActionTip: "移除图层"
    },

    "gxp.plugins.Styler.prototype": {
        menuText: "编辑样式",
        tooltip: "管理图层样式"

    },

    "gxp.plugins.WMSGetFeatureInfo.prototype": {
        buttonText:"识别",
        infoActionTip: "获取要素信息",
        popupTitle: "要素信息"
    },

    "gxp.plugins.Zoom.prototype": {
        zoomMenuText: "缩放框",
        zoomInMenuText: "放大",
        zoomOutMenuText: "缩小",
        zoomTooltip: "缩放至所选框",
        zoomInTooltip: "放大",
        zoomOutTooltip: "缩小"
    },

    "gxp.plugins.ZoomToExtent.prototype": {
        menuText: "缩放到最大范围",
        tooltip: "缩放到最大范围"
    },


    "gxp.plugins.ZoomToLayerExtent.prototype": {
        menuText: "缩放至图层范围",
        tooltip: "缩放至图层范围"
    },

    "gxp.plugins.ZoomToSelectedFeatures.prototype": {
        menuText: "缩放至所选要素",
        tooltip: "缩放至所选要素"
    },

    "gxp.FeatureEditPopup.prototype": {
        closeMsgTitle: "保存更改？",
        closeMsg: "该要素的更改未保存。需要保存这些更改吗？",
        deleteMsgTitle: "删除要素？",
        deleteMsg: "确定要删除该要素？",
        editButtonText: "编辑",
        editButtonTooltip: "使该要素可编辑",
        deleteButtonText: "删除",
        deleteButtonTooltip: "删除该要素",
        cancelButtonText: "取消",
        cancelButtonTooltip: "停止编辑并不保存",
        saveButtonText: "保存",
        saveButtonTooltip: "保存更改"
    },

    "gxp.FillSymbolizer.prototype": {
        fillText: "填充",
        colorText: "颜色",
        opacityText: "不透明度"
    },

    "gxp.FilterBuilder.prototype": {
        builderTypeNames: ["any", "all", "none", "not all"],
        preComboText: "匹配",
        postComboText: "下列：",
        addConditionText: "添加条件",
        addGroupText: "添加分组",
        removeConditionText: "移除条件"
    },

    "gxp.grid.CapabilitiesGrid.prototype": {
        nameHeaderText : "名称",
        titleHeaderText : "标题",
        queryableHeaderText : "可查询",
        layerSelectionLabel: "查看可取数据：",
        layerAdditionLabel: "或者添加新的服务。",
        expanderTemplateText: "<p><b>概述：</b> {abstract}</p>"
    },



    "gxp.QueryPanel.prototype": {
        queryByLocationText: "通过位置查询",
        currentTextText: "当前选项",
        queryByAttributesText: "通过属性查询",
        layerText: "图层"
    },

    "gxp.RulePanel.prototype": {
        scaleSliderTemplate: "{scaleType} 缩放1:{scale}",
        labelFeaturesText: "标签要素",
        labelsText: "标签",
        basicText: "原始的",
        advancedText: "更新的",
        limitByScaleText: "缩放限制",
        limitByConditionText: "位置限制",
        symbolText: "符号",
        nameText: "名称"
    },

    "gxp.PointSymbolizer.prototype": {
        graphicCircleText: "圆形",
        graphicSquareText: "正方形",
        graphicTriangleText: "三角形",
        graphicStarText: "星形",
        graphicCrossText: "交叉形",
        graphicXText: "x形",
        graphicExternalText: "外部",
        urlText: "URL",
        opacityText: "不透明度",
        symbolText: "符号",
        sizeText: "大小",
        rotationText: "旋转"
    },

    "gxp.ScaleLimitPanel.prototype": {
        scaleSliderTemplate: "{scaleType} 缩放1:{scale}",
        minScaleLimitText: "最小缩放限制",
        maxScaleLimitText: "最大缩放限制"
    },

    "gxp.StrokeSymbolizer.prototype": {
        solidStrokeName: "实线",
        dashStrokeName: "短线",
        dotStrokeName: "点线",
        titleText: "边界",
        styleText: "样式",
        colorText: "颜色",
        widthText: "宽度",
        opacityText: "不透明度"
    },

    "gxp.StylePropertiesDialog.prototype": {
        titleText: "常规",
        nameFieldText: "名称",
        titleFieldText: "标题",
        abstractFieldText: "概述"
    },

    "gxp.TextSymbolizer.prototype": {
        labelValuesText: "标签属性",
        haloText: "光环",
        sizeText: "大小",
        priorityText: "优先",
        labelOptionsText: "标签选项",
        autoWrapText: "自动换行",
        followLineText: "走线",
        maxDisplacementText: "最大偏移",
        repeatText: "重复",
        forceLeftToRightText: "强制从左到右",
        graphicResizeText: "图像大小",
        graphicMarginText: "图形",
        graphicTitle: "图形",
        fontColorTitle:  "字体颜色和不透明度",
        positioningText: "定位",
        anchorPointText: "锚点",
        displacementXText: "X向偏移",
        displacementYText: "Y向偏移",
        perpendicularOffsetText: "垂直偏移量",
        priorityHelp: "指定字段的值越高，标签将越快被绘制(从而在解决冲突中获利)",
        autoWrapHelp: "包装超过一定长度的标签",
        followLineHelp: "标签是否应该遵循直线的几何形状?",
        maxDisplacementHelp: "如果标签位置占线则采用像素的最大偏移",
        repeatHelp: "在一定数量的像素之后重复标签",
        forceLeftToRightHelp: "标签通常会被翻转，以使其更易读。如果这个字符恰好是一个方向箭头那么这是不可取的",
        graphic_resizeHelp: "指定调整标签图形(如高速公路护栏)，以适应标签文本的模式。默认模式“none”从不修改标签图形。在拉伸模式下，GeoServer将调整图形以精确地包围标签文本，可能会修改图像的纵横比。在比例模式下，GeoServer将把图像扩展到足够大的位置，以使文本围绕文本，同时保持其原始的长宽比。",
        graphic_marginHelp: "类似于保证金简写属性在HTML，CSS的解释取决于提供了多少边缘值：1 =使用保证金在长度的标签。2 =使用顶部和底部边缘的第一和第二个左和右的利润率。3 =使用第一个顶部边缘，第二个为左和右边缘，第三个为底部边缘。4 =使用第一个，第二个为右，第三个为底部边缘，第四个为左边缘。"
     },
    "gxp.WMSLayerPanel.prototype": {
        aboutText: "关于",
        titleText: "标题",
        nameText: "名称",
        descriptionText: "描述",
        displayText: "显示",
        opacityText: "不透明度",
        formatText: "瓦片格式",
        infoFormatText: "信息格式",
        infoFormatEmptyText: "选择一个格式",
        transparentText: "透明度",
        cacheText: "缓存",
        cacheFieldText: "使用缓存版本",
        stylesText: "样式",
        displayOptionsText: "显示选项",
        queryText: "过滤限制",
        scaleText: "范围限制",
        minScaleText: "最小范围",
        maxScaleText: "最大范围",
        switchToFilterBuilderText: "切换回过滤生成器",
        cqlPrefixText: "或者",
        cqlText: "用CQL过滤器代替"
    },

    "gxp.EmbedMapDialog.prototype": {
        publishMessage: "您的地图已准备好发布到Web上！只需在您的网站上复制以下HTML加载地图：",
        heightLabel: '高度',
        widthLabel: '宽度',
        mapSizeLabel: '地图大小',
        miniSizeLabel: '最小',
        smallSizeLabel: '小',
        premiumSizeLabel: '额外',
        largeSizeLabel: '大'
    },

    "gxp.WMSStylesDialog.prototype": {
         addStyleText: "添加",
         addStyleTip: "添加新的样式",
         chooseStyleText: "选择样式",
         classifyStyleText:"分类",
         classifyStyleTip:"基于属性进行分类",
         deleteStyleText: "移除",
         deleteStyleTip: "删除所选样式",
         editStyleText: "编辑",
         editStyleTip: "编辑所选样式",
         duplicateStyleText: "拷贝",
         duplicateStyleTip: "拷贝所选样式",
         addRuleText: "添加",
         addRuleTip: "添加新规则",
         newRuleText: "新规则",
         deleteRuleText: "移除",
         deleteRuleTip: "删除所选规则",
         editRuleText: "编辑",
         editRuleTip: "编辑所选规则",
         duplicateRuleText: "拷贝",
         duplicateRuleTip: "拷贝所选规则",
         cancelText: "取消",
         saveText: "保存",
         styleWindowTitle: "用户样式：{0}",
         ruleWindowTitle: "样式规则：{0}",
         stylesFieldsetTitle: "样式",
         rulesFieldsetTitle: "规则"
    },

    "gxp.ClassificationPanel.prototype": {
        classifyText: "分类",
        rampBlueText: "蓝色",
        rampRedText: "红色",
        rampOrangeText: "橙色",
        rampJetText: "蓝-红",
        rampGrayText: "灰色",
        rampRandomText: "随机",
        rampCustomText: "自定义",
        selectColorText: "选择颜色",
        colorStartText: "起始颜色",
        colorEndText: "终止颜色",
        methodUniqueText: "唯一值",
        methodQuantileText: "等量",
        methodEqualText: "等距",
        methodJenksText: "Jenks自然间断点",
        standardDeviationText: "标准差",
        attributeText: "属性",
        selectAttributeText: "选择属性",
        startColor: "#FEE5D9",
        endColor: "#A50F15",
        generateRulesText: "应用",
        reverseColorsText: "反转颜色",
        methodText: "方法",
        classesText: "数量",
        colorrampText: "颜色梯度",
        selectMethodText: "选择方法"
    },

    "gxp.LayerUploadPanel.prototype": {
        titleLabel: "标题",
        titleEmptyText: "图层标题",
        abstractLabel: "描述",
        abstractEmptyText: "图层描述",
        fileLabel: "数据",
        fieldEmptyText: "浏览数据归档...",
        uploadText: "上传",
        waitMsgText: "上传你的数据..",
        invalidFileExtensionText: "文件扩展名必须是以下格式：",
        optionsText: "选项",
        workspaceLabel: "工作空间",
        workspaceEmptyText: "默认工作空间",
        dataStoreLabel: "仓库",
        dataStoreEmptyText: "创建新的仓库",
        defaultDataStoreEmptyText: "默认数据仓库"
    },

    "gxp.NewSourceDialog.prototype": {
        title: "添加新的服务...",
        cancelText: "取消",
        addServerText: "添加服务",
        invalidURLText: "通过正确的URL进入WMS端点 (e.g. http://example.com/geoserver/wms)",
        contactingServerText: "连接服务器..."
    },

    "gxp.ScaleOverlay.prototype": {
        zoomLevelText: "缩放等级"
    },

    "gxp.plugins.ArcGISCacheSource.prototype": {
        noLayersTitle: "没有ArcGIS图层",
        noLayersText: "无法找到拥有兼容投影（墨卡托）的任何图层，位置："
    },

    "gxp.plugins.ArcRestSource.prototype": {
        noLayersTitle: "没有ArcGIS图层",
        noLayersText: "无法找到拥有兼容投影（墨卡托）的任何图层，位置："
    },

    "gxp.plugins.MapShare.prototype": {
        text: "分享地图",
        toolTip: "地图信息和下载链接"
    },

    "gxp.plugins.AnnotationTool.prototype": {
        errorTitle: "注释创建失败",
        noteText: "注释",
        notesText: "注释",
        showNotesText: "显示注释",
        editNotesText: "编辑注释",
        addNoteText: "添加注释",
        newNoteText: "新的注释",
        projection: "EPSG:4326",
        pointText: "点",
        lineText: "线",
        polygonText: "形状",
        saveFailTitle: "无法保存注释",
        saveFailText: "编辑失败，您未拥有保存改注释的权限",
        saveText: "保存",
        editText: "编辑",
        deleteText: "删除",
        cancelText: "取消",
        titleText: "标题"
    },



    "gxp.SearchBar.prototype": {
        emptyText: '正在检索...',
        searchText: '检索',
        noSearchableLayersTitle: '未检索到图层',
        noSearchableLayersMsg: '目前地图上没有可搜索图层。您必须在地图上至少拥有一个有可检索字段的可见图层。',
        searchTermTitle: "所需检索项",
        searchTermText: "请输入检索项",
        resetText: "重置"
    },

    "gxp.plugins.PrintPage.prototype": {
        menuText: "打印地图",
        tooltip: "打印地图",
        buttonText: "打印"
    },

    "gxp.plugins.CoordinateTool.prototype": {
        title: "地图坐标 （经度，纬度）",
        infoActionTip: "获取鼠标位置的坐标信息",
        coordinatePositionText: "坐标位置"
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
        infoActionTip: "获取我的位置",
        locationFailedText: "位置检测失败"
    },

    "gxp.plugins.LayerShare.prototype": {
        menuText: "分享图层",
        toolTip: "图层信息和下载链接"
    },

    "gxp.plugins.MapShare.prototype": {
        text: "分享我的地图",
        toolTip: "地图信息和下载链接"
    },

    "gxp.plugins.AddCategory.prototype": {
        addCategoryMenuText:"添加分类",
        addCategoryActionTipText:"向图层树添加分类",
        categoryNameText: "分类名："
    },

    "gxp.plugins.RemoveCategory.prototype": {
        removeCategoryActionText:"移除分类",
        removeCategoryActionTipText: "移除分类以及其内所有图层",
        cannotRemoveText: "该分类不能被移除"
    },

    "gxp.plugins.RenameCategory.prototype": {
        renameCategoryActionText:"重命名分类",
        renameCategoryActionTipText:"为该分类创建新的名字",
        cannotRenameText: "该分类不能被重命名"
    },

    "gxp.LinkEmbedMapDialog.prototype": {
        linkMessage: '<span style="font-size:10pt;">拷贝以下链接到email或者IM：</span>',
        publishMessage: '<span style="font-size:10pt;">拷贝以下HTML嵌入到前端：</span>'
    },

    "gxp.plugins.GeoNodeQueryTool.prototype" : {
        infoActionTip: "获取要素信息",
        popupTitle: "要素信息",
        resetTitle: "重置",
        resetToolTipText: "清空所有要素"
    },

    "gxp.plugins.MapRevisionTool.prototype" : {
        infoActionTip: "查看地图修订列表",
        toolText: "修订",
        windowTitle: "地图修订历史记录"
    },

    "gxp.plugins.GazetteerTool.prototype" : {
        infoActionTip: '输入要搜索的地名',
        toolText: '地名索引',
        searchingText: '检索中...',
        fromText: '起始: YYYY-MM-DD',
        toText: '终止: YYYY-MM-DD',
        datesText: '日期',
        geocodersText: '地理编码',
        advancedText: '高级设置',
        sourceText: '源',
        startDateText: '开始日期',
        endDateText: '结束日期',
        placenameText: '地名',
        coordinatesText: '坐标系',
        searchText: '检索'
    },

    'gxp.FeedSourceDialog.prototype': {
        addPicasaText: 'Picasa Photos',
        addFlickrText: 'Add Flickr Photos',
        addYouTubeText: 'YouTube Videos',
        addHGLText: 'Harvard Geospatial Library',
        addRSSText: '其他GeoRSS Feed',
        addFeedText: '添加到地图',
        titleText: 'Feed标题',
        keywordText: '关键字',
        typeText: '类型',
        urlText: 'URL',
        maxResultsText: '最大 # Results',
        chooseNumberText: '选择数量...',
        georssfeedsText: 'GeoRSS Feeds'
    },


    'gxp.plugins.MapShare.prototype': {
        text: "分享地图",
        toolTip: "地图信息以及下载链接"
    },


    'gxp.plugins.LayerManager.prototype': {
        baseNodeText: "底图"
    },

    'gxp.plugins.LayerTree.prototype': {
        overlayNodeText: '覆盖图',
        baseNodeText: '底图',
        addCategoryActionText: '添加分类',
        addCategoryActionTipText: '添加分类'
    }
    
});
