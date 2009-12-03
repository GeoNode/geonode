{% load i18n %}

if(window.MyHazard && window.MyHazard.Viewer){
  Ext.apply(MyHazard.Viewer.prototype, {
      pdfButtonText: gettext("PDF Report"),
      reportSwitcherTip: gettext("Request hazard data by clicking on the map"),
      pointReporterTip: gettext("Point reporter"),
      lineReporterTip: gettext("Line reporter"),
      polygonReporterTip: gettext("Polygon reporter"),
      navActionTipText: gettext("Pan map"),
      zoomSliderTipText: gettext("Zoom level"),
      transparencyButtonText: gettext("Set layer transparency"),
      reportFailureMessage: gettext("Failure while retrieving report..."),
      reportPopupTitle: gettext("MyHazard Report")
  });
}
