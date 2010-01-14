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
