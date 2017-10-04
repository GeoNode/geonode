# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0025_auto_20170801_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='map',
            name='content_map',
            field=models.TextField(default='<h3>The Harvard WorldMap Project</h3>  <p>WorldMap is an open source web mapping system that is currently  under construction. It is built to assist academic research and  teaching as well as the general public and supports discovery,  investigation, analysis, visualization, communication and archiving  of multi-disciplinary, multi-source and multi-format data,  organized spatially and temporally.</p>  <p>The first instance of WorldMap, focused on the continent of  Africa, is called AfricaMap. Since its beta release in November of  2008, the framework has been implemented in several geographic  locations with different research foci, including metro Boston,  East Asia, Vermont, Harvard Forest and the city of Paris. These web  mapping applications are used in courses as well as by individual  researchers.</p>  <h3>Introduction to the WorldMap Project</h3>  <p>WorldMap solves the problem of discovering where things happen.  It draws together an array of public maps and scholarly data to  create a common source where users can:</p>  <ol>  <li>Interact with the best available public data for a  city/region/continent</li>  <li>See the whole of that area yet also zoom in to particular  places</li>  <li>Accumulate both contemporary and historical data supplied by  researchers and make it permanently accessible online</li>  <li>Work collaboratively across disciplines and organizations with  spatial information in an online environment</li>  </ol>  <p>The WorldMap project aims to accomplish these goals in stages,  with public and private support. It draws on the basic insight of  geographic information systems that spatiotemporal data becomes  more meaningful as more "layers" are added, and makes use of tiling  and indexing approaches to facilitate rapid search and  visualization of large volumes of disparate data.</p>  <p>WorldMap aims to augment existing initiatives for globally  sharing spatial data and technology such as <a target="_blank" href="http://www.gsdi.org/">GSDI</a> (Global Spatial Data  Infrastructure).WorldMap makes use of <a target="_blank" href="http://www.opengeospatial.org/">OGC</a> (Open Geospatial  Consortium) compliant web services such as <a target="_blank" href="http://en.wikipedia.org/wiki/Web_Map_Service">WMS</a> (Web  Map Service), emerging open standards such as <a target="_blank" href="http://wiki.osgeo.org/wiki/Tile_Map_Service_Specification">WMS-C</a>  (cached WMS), and standards-based metadata formats, to enable  WorldMap data layers to be inserted into existing data  infrastructures.&nbsp;<br>  <br>  All WorldMap source code will be made available as <a target="_blank" href="http://www.opensource.org/">Open Source</a> for others to use  and improve upon.</p>', null=True, verbose_name='Site Content', blank=True),
        ),
    ]
