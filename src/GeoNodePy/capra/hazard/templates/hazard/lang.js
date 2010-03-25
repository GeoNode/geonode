{% load i18n %}

if (window.MyHazard && window.MyHazard.Viewer) {
    Ext.apply(MyHazard.Viewer.prototype, {
        lineReporterTip: gettext("Line reporter"),
        navActionTipText: gettext("Pan map"),
        pdfButtonText: gettext("PDF Report"),
        pointReporterTip: gettext("Point reporter"),
        polygonReporterTip: gettext("Polygon reporter"),
        reportEmptyDataSetMessage: gettext("Please select some layers before requesting a report."),
        reportFailureMessage: gettext("Failure while retrieving report..."),
        reportPopupTitle: gettext("MyHazard Report"),
        reportSwitcherTip: gettext("Tooltip here"),
        transparencyButtonText: gettext("Transparency"),
        zoomSliderTipText: gettext("Zoom level")
    });
}

if (capra && capra.DataGrid) {
    Ext.apply(capra.DataGrid.prototype, {
        dataTitleHeaderText: gettext("Title"),
        dataNameHeaderText: gettext("Name"),
        dataDetailText: gettext("More information about this layer"),
        layerTitleSuffix: gettext("Layers"),
        uncategorizedLabel: gettext("Uncategorized")
    });
}

if (capra && capra.AMEGrid) {
    Ext.apply(capra.AMEGrid.prototype, {
        gridTitleText: gettext('AME Data'),
        countryLabelText: gettext('Country'),
        scenarioLabelText: gettext('Scenario'),
        ameLabelText: gettext('Name'),
        singularFileText: gettext('File'),
        pluralFilesText: gettext('Files'),
        downloadText: gettext('Download'),
        fileDetailsText: gettext('More Information about this file')
    });
}