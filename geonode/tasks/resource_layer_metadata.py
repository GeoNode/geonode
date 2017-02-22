    #

    ###############################
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                  username=settings.OGC_SERVER['default']['USER'],
                  password=settings.OGC_SERVER['default']['PASSWORD'])

    count_notification = Template(
        '[$ctr/$total] Editing Metadata for Layer: $layername')

    ###
    #   TREES - DBH (diameter at breast height) and Standing Tree Volume Estimation
    #   with sld template
    ###
    filter_substring = '_trees'
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "biota"
            title = Template(
                '$area DBH (diameter at breast height) and Standing Tree Volume Estimation')
            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                style_update(layer, 'trees_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """These are points that display the estimated diameter at breast height (DBH) of a forested area. It shows the percentage of trees per dbh class (in cm).

                These are points that display the estimated tree volume of a forested area. It shows the percentage of trees per volume class (in cum)
                """
                layer.purpose = "Forest Resources Assesment/Management"
                layer.keywords.add("FRExLS", " Trees", " DBH",
                                   "Standing Tree Volume", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   CCM - Canopy Cover Model
    ###
    filter_substring = '_ccm'
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "biota"
            title = Template('$area Canopy Cover Model')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "These are rasters, with resolution of 1 meter, that display the canopy cover of a forested area. It shows Canopy Cover % which ranges from Low to High"
                layer.purpose = "Forest Resources Assesment/Management"
                layer.keywords.add("FRExLS", "Canopy Cover", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   CHM - Canopy Height Models
    ###

    filter_substring = '_chm'
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "biota"
            title = Template('$area Canopy Height Model')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "These are rasters, with resolution of 1 meter, that display the canopy height of a forested area.It shows the height of trees/vegetation (in meter) present in the sample area"
                layer.purpose = "Forest Resources Assesment/Management"
                layer.keywords.add("FRExLS", "Canopy Height", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   AGB - Area Biomass Estimation
    ###
    filter_substring = "_agb"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "biota"
            title = Template('$area Biomass Estimation')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "These are rasters, with a resolution of 10 meters, that display the estimated biomass of a forested area. It shows the total biomass (in kg) per 10sqm of the selected area."
                layer.purpose = "Forest Resources Assesment/Management"
                layer.keywords.add("FRExLS", "Biomass", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   aquaculture - Aquaculture
    ###
    filter_substring = "_aquaculture"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "imageryBaseMapsEarthCover"
            title = Template('$area Aquaculture')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                style_update(layer, layer.name + '_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """Maps prepared by Phil-LiDAR 2 Program B and reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include extracted aquaculture (fishponds, fish pens, fish traps, fish corrals) from the LiDAR data and/or orthophoto.
             
                Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
                Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
                Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free."
                """
                layer.purpose = "Detailed Coastal (aquaculture, mangroves) Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making."
                layer.keywords.add("CoastMap", "Aquaculture",
                                   "Fish Pens", "Fish Ponds", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   mangroves - Mangroves
    ###
    filter_substring = "_mangroves"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "imageryBaseMapsEarthCover"
            title = Template('$area Mangroves')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                style_update(layer, layer.name + '_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include extracted mangrove areas from the LiDAR data and/or orthophoto.
             
                Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
                Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
                Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free.
                """
                layer.purpose = "Detailed Coastal (aquaculture, mangroves) Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making."
                layer.keywords.add("CoastMap", "Mangroves", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   agrilandcover - Agricultural Landcover
    ###
    filter_substring = "_agrilandcover"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "imageryBaseMapsEarthCover"
            title = Template('$area Agricultural Landcover')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                style_update(layer, layer.name + '_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include initial Land Cover Map of Agricultural Resources.
             
                Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
                Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
                Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free.
                """
                layer.purpose = "Detailed Agricultural Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making. This complements on-going programs of the Department of Agriculture by utilizing LiDAR data for the mapping of high value crops and vulnerability assessment."
                layer.keywords.add("PARMap", "Agriculture",
                                   "Landcover", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   agricoastlandcover - Agricultural and Coastal Landcover
    ###

    filter_substring = "_agricoastlandcover"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "imageryBaseMapsEarthCover"
            title = Template('$area Agricultural and Coastal Landcover')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """ Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include initial Land Cover Map of Agricultural Resources integrated with Coastal Resources.
     
                Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
                Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
                Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free.
                """
                layer.purpose = "Integrated Agricultural and Coastal Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making. This complements on-going programs of the Department of Agriculture by utilizing LiDAR data for the mapping of high value crops and vulnerability assessment."
                layer.keywords.add(
                    "PARMap", "Agriculture", "COASTMap", "Mangrove", "Landcover", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   irrigation - River Basin Irrigation Network
    #   with sld template
    ###
    filter_substring = "_irrigation"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "inlandWaters"
            title = Template('$area River Basin Irrigation Network')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                style_update(layer, 'irrigation_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "This shapefile contains extracted irrigation networks from LiDAR DEM and orthophotos."
                layer.purpose = "Irrigation network maps are useful for planning irrigation structures to fully utilize water resources and distribute water to non-irrigated lands. This data contains irrigation classification and the corresponding elevations of start and end-point of each segment that can be used for further studies that involve irrigation network modeling. "
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.keywords.add("Irrigation Networks", "Canals",
                                   "Ditches", "Hydrology", "PHD", "PhilLiDAR2")
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   streams - River Basin Streams (LiDAR), Streams (SAR)
    ###
    filter_substring = "_streams"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "inlandWaters"
            title = Template(
                '$area River Basin Streams (LiDAR), Streams (SAR)')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """This shapefile contains extracted stream network derived from LiDAR DEM with a 1-meter resolution (solid lines) and SAR DEM with 10-m resolution (broken lines).

                Note: The extracted streams are based on thalwegs (lines of lowest elevation) and not on centerlines."
                """
                layer.purpose = "Stream network maps provides important information to planners and decision makers in managing and controlling streams to make these bodies of water more useful and less disruptive to human activity."
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.keywords.add("Streams", "Rivers", "Creeks",
                                   "Drainages", "Hydrology", "PHD", "PhilLiDAR2")
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   wetlands - River Basin Inland Wetlands
    #   with sld template
    ###
    filter_substring = "_wetlands"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "inlandWaters"
            title = Template('$area River Basin Inland Wetlands')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                style_update(layer, 'wetlands_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "This shapefile contains extacted inland wetlands derived from LiDAR DEM and orthophotos. Depressions that can be detected from the elevation model were indicative of the presence of wetlands."
                layer.purpose = "Inland wetlands are key to preserving biodiversity. These features are home to various species that rely on a healthy ecosystem to thrive. Also, wetlands are sometimes used for water storage that can later be utilized in agricultural activities."
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.keywords.add("Inland Wetlands", "Wetlands",
                                   "Depressions", "Hydrology", "PHD", "PhilLiDAR2")
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   power - Hydropower Potential Sites
    #   with sld template
    ###
    filter_substring = "_power"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total = len(layer_list)
            ctr = 0
            identifier = "environment"
            # depends if 1000
            title = Template('Hydropower Potential Sites $distance $area')

            for layer in layer_list:
                ctr += 1
                print "Layer: %s" % layer.name
                style_update(layer, 'power_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_', ' ')
                distance = text_split[1].replace('_', ' ').lstrip()
                print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
                layer.title = title.substitute(area=area, distance=distance)
                layer.abstract = """Each province has 3 datasets - for horizontal distances of 100m, 500m, 1000m - with the following information: head, simulated flow, simulated power and hydropower classification.

                The hydropower resource potential is theoretical based on the hydrologic model ArcSWAT and terrain analysis. Hydropower classification is based on theoretical capacity with 80% technical efficiency as prescribed by the DOE."""
                layer.purpose = "Site Identification of Hydropower Sites for future development"
                layer.category = TopicCategory.objects.get(
                    identifier=identifier)
                layer.keywords.add("Hydropower", "REMap", "PhilLiDAR2")
                layer.save()
        except Exception as e:
            print "%s" % e
            pass