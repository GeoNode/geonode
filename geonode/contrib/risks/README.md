# geonode-risk_management_tools
The ``geonode-risk_management_tools`` contrib app is a GeoNode Extension built by WorldBanck GFDRR which adds the capability of extracting and managing Hazard Risks on geographical areas.

## Overview
The World Bank and GFDRR are leading an ongoing Technical Assistance (TA) to the Government of Afghanistan on Disaster Risk Management. As part of this TA, a multi-hazard risk assessment was conducted. An international consortium was hired to produce new information on hazard, exposure, vulnerability and risk, for flooding, earthquake, landslide, avalanche, and drought. Hazard and loss for different return periods was computed for all districts and regions. In addition, a cost-benefit analysis was conducted for a select number of risk reduction options for floods and earthquakes (e.g. flood levees; earthquake-proofing of buildings).

A GeoNode (http://disasterrisk.af.geonode.org/) was developed by ENEA to host and share the data. Many of the data layers have been uploaded and stylized on this GeoNode. The GeoNode is currently following the standard format. World Bank has an interest in improving the decision-making and data-extraction capabilities by expanding this GeoNode with two modules. One module should allow the user to dynamically explore the potential costs and benefits of the pre-calculated risk management options, by sliding bars, changing numbers and getting outputs in graphs, charts and a simple map. The second module should allow the user to easily extract maps and tabular results for their area and indicator of interest, again using drop-down menus and boxes that filter existing information and maps.

### Module 1: Cost-benefit Analysis & Decision Tool
This module should allow the user to use an interactive user interface (drop-down menus; slide bars; buttons) to access pre-processed tables and maps related to cost-benefit analysis of risk management options.

### Module 2: Risk Data Extraction and Visualization
This module should enable the user to easily show and extract data for the area (district, province, national) of interest. Based on the user's selection of area (linked to admin 1 and admin 2 shapefiles), indicator (linked to table and/or map), and indicator property (linked to rows and columns in the table), the user should get the correct map and a chart/graph.

# Settings

## Activation

In the ``settings.py``(or local-settings) file, enable the ``geonode.contrib.metadataxsl`` app.  
e.g.::
```Python
    GEONODE_CONTRIB_APPS = (
        'geonode.contrib.risks'
    )
```
## Collect static files

This step is needed in order to copy in the static dir the ``.xsl`` file that will be referenced by the
exported metadata file, and one ``.css`` file that is referenced within the xsl file.

        python manage.py collectstatic

This means that any customization to the output format should be performed on these files.

# Other refs
