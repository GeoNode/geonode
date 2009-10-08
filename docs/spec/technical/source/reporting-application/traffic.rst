Example Session
===============

This document is intended to provide a high-level idea of how data flows in the
process of a user requesting and receiving a hazard report in the hazard
application.

==========  ============================================================================================  ========
Sender      Message                                                                                       Receiver
==========  ============================================================================================  ========
Browser     Initial page load (GET dj/hazard/)                                                            GeoNode
GeoNode     HTML + JS for frontend application                                                            Browser
Browser     Report request (click position, layers, view size) (GET dj/hazard/report.html)                GeoNode
GeoNode     Forwards request parameters augmented with data from DB (POST gs/rest/process/hazardreport/)  GeoServer
GeoServer   Gets data from DB/TIFFs, calculates statistics, formats response                              GeoNode
GeoNode     Formats process results into HTML                                                             Browser
Browser     Full report request (repeat parameters) (GET dj/hazard/report.pdf)                            GeoNode
GeoNode     Forwards request parameters augmented with data from DB                                       GeoServer
GeoNode     Fetches WMS tiles from GeoServer                                                              GeoServer
GeoServer   Gets data, calculates statistics, formats response, renders tiles                             GeoNode
GeoNode     Formats data and images into a PDF report template                                            Browser
==========  ============================================================================================  ========
