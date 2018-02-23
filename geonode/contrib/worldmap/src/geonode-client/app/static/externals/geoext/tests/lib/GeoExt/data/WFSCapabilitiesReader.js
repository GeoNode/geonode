var doc = (new OpenLayers.Format.XML).read(
'<?xml version="1.0" encoding="UTF-8"?>'+
'<WFS_Capabilities version="1.0.0" xsi:schemaLocation="http://www.opengis.net/wfs http://someserver.com:8080/geoserver/schemas/wfs/1.0.0/WFS-capabilities.xsd" xmlns="http://www.opengis.net/wfs" xmlns:cite="http://www.opengeospatial.net/cite" xmlns:it.geosolutions="http://www.geo-solutions.it" xmlns:tiger="http://www.census.gov" xmlns:sde="http://geoserver.sf.net" xmlns:topp="http://www.openplans.org/topp" xmlns:sf="http://www.openplans.org/spearfish" xmlns:nurc="http://www.nurc.nato.int" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'+
    '<Service>'+
        '<Name>WFS</Name>'+
        '<Title>GeoServer Web Feature Service</Title>'+
        '<Abstract>This is the reference implementation of WFS 1.0.0 and WFS 1.1.0, supports all WFS operations including Transaction.</Abstract>'+
        '<Keywords>WFS, WMS, GEOSERVER</Keywords>'+
        '<OnlineResource>http://someserver.com:8080/geoserver/wfs</OnlineResource>'+
        '<Fees>NONE</Fees>'+
        '<AccessConstraints>NONE</AccessConstraints>'+
    '</Service>'+
    '<Capability>'+
        '<Request>'+
            '<GetCapabilities>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Get onlineResource="http://someserver.com:8080/geoserver/wfs?request=GetCapabilities" />'+
                    '</HTTP>'+
                '</DCPType>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Post onlineResource="http://someserver.com:8080/geoserver/wfs?" />'+
                    '</HTTP>'+
                '</DCPType>'+
            '</GetCapabilities>'+
            '<DescribeFeatureType>'+
                '<SchemaDescriptionLanguage>'+
                    '<XMLSCHEMA />'+
                '</SchemaDescriptionLanguage>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Get onlineResource="http://someserver.com:8080/geoserver/wfs?request=DescribeFeatureType" />'+
                    '</HTTP>'+
                '</DCPType>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Post onlineResource="http://someserver.com:8080/geoserver/wfs?" />'+
                    '</HTTP>'+
                '</DCPType>'+
            '</DescribeFeatureType>'+
            '<GetFeature>'+
                '<ResultFormat>'+
                    '<GML2 />'+
                    '<SHAPE-ZIP />'+
                    '<GEOJSON />'+
                    '<csv />'+
                    '<GML3 />'+
                '</ResultFormat>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Get onlineResource="http://someserver.com:8080/geoserver/wfs?request=GetFeature" />'+
                    '</HTTP>'+
                '</DCPType>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Post onlineResource="http://someserver.com:8080/geoserver/wfs?" />'+
                    '</HTTP>'+
                '</DCPType>'+
            '</GetFeature>'+
            '<Transaction>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Get onlineResource="http://someserver.com:8080/geoserver/wfs?request=Transaction" />'+
                    '</HTTP>'+
                '</DCPType>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Post onlineResource="http://someserver.com:8080/geoserver/wfs?" />'+
                    '</HTTP>'+
                '</DCPType>'+
            '</Transaction>'+
            '<LockFeature>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Get onlineResource="http://someserver.com:8080/geoserver/wfs?request=LockFeature" />'+
                    '</HTTP>'+
                '</DCPType>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Post onlineResource="http://someserver.com:8080/geoserver/wfs?" />'+
                    '</HTTP>'+
                '</DCPType>'+
            '</LockFeature>'+
            '<GetFeatureWithLock>'+
                '<ResultFormat>'+
                    '<GML2 />'+
                '</ResultFormat>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Get onlineResource="http://someserver.com:8080/geoserver/wfs?request=GetFeatureWithLock" />'+
                    '</HTTP>'+
                '</DCPType>'+
                '<DCPType>'+
                    '<HTTP>'+
                        '<Post onlineResource="http://someserver.com:8080/geoserver/wfs?" />'+
                    '</HTTP>'+
                '</DCPType>'+
            '</GetFeatureWithLock>'+
        '</Request>'+
    '</Capability>'+
    '<FeatureTypeList>'+
        '<Operations>'+
            '<Query />'+
            '<Insert />'+
            '<Update />'+
            '<Delete />'+
            '<Lock />'+
        '</Operations>'+
        '<FeatureType>'+
            '<Name>sf:archsites</Name>'+
            '<Title>Spearfish archeological sites</Title>'+
            '<Abstract>Sample data from GRASS, archeological sites location, Spearfish, South Dakota, USA</Abstract>'+
            '<Keywords>archsites, spearfish, sfArchsites, archeology</Keywords>'+
            '<SRS>EPSG:26713</SRS>'+
            '<LatLongBoundingBox minx="-103.8725637911543" miny="44.37740330855979" maxx="-103.63794182141925" maxy="44.48804280772808" />'+
        '</FeatureType>'+
        '<FeatureType>'+
            '<Name>sf:bugsites</Name>'+
            '<Title>Spearfish bug locations</Title>'+
            '<Abstract>Sample data from GRASS, bug sites location, Spearfish, South Dakota, USA</Abstract>'+
            '<Keywords>spearfish, sfBugsites, insects, bugsites, tiger_beetles</Keywords>'+
            '<SRS>EPSG:26713</SRS>'+
            '<LatLongBoundingBox minx="-103.86796131703647" miny="44.373938816704396" maxx="-103.63773523234195" maxy="44.43418821380063" />'+
        '</FeatureType>'+
        '<FeatureType>'+
            '<Name>sf:restricted</Name>'+
            '<Title>Spearfish restricted areas</Title>'+
            '<Abstract>Sample data from GRASS, restricted areas, Spearfish, South Dakota, USA</Abstract>'+
            '<Keywords>spearfish, restricted, areas, sfRestricted</Keywords>'+
            '<SRS>EPSG:26713</SRS>'+
            '<LatLongBoundingBox minx="-103.85057172920756" miny="44.39436387625042" maxx="-103.74741494853805" maxy="44.48215752041131" />'+
        '</FeatureType>'+
        '<FeatureType>'+
            '<Name>sf:roads</Name>'+
            '<Title>Spearfish roads</Title>'+
            '<Abstract>Sample data from GRASS, road layout, Spearfish, South Dakota, USA</Abstract>'+
            '<Keywords>sfRoads, spearfish, roads</Keywords>'+
            '<SRS>EPSG:26713</SRS>'+
            '<LatLongBoundingBox minx="-103.87741691493184" miny="44.37087275281798" maxx="-103.62231404880659" maxy="44.50015918338962" />'+
        '</FeatureType>'+
        '<FeatureType>'+
            '<Name>sf:streams</Name>'+
            '<Title>Spearfish streams</Title>'+
            '<Abstract>Sample data from GRASS, streams, Spearfish, South Dakota, USA</Abstract>'+
            '<Keywords>spearfish, sfStreams, streams</Keywords>'+
            '<SRS>EPSG:26713</SRS>'+
            '<LatLongBoundingBox minx="-103.87789019829768" miny="44.372335260095554" maxx="-103.62287788915457" maxy="44.502218486214815" />'+
        '</FeatureType>'+
    '</FeatureTypeList>'+
    '<ogc:Filter_Capabilities>'+
        '<ogc:Spatial_Capabilities>'+
            '<ogc:Spatial_Operators>'+
                '<ogc:Disjoint />'+
                '<ogc:Equals />'+
                '<ogc:DWithin />'+
                '<ogc:Beyond />'+
                '<ogc:Intersect />'+
                '<ogc:Touches />'+
                '<ogc:Crosses />'+
                '<ogc:Within />'+
                '<ogc:Contains />'+
                '<ogc:Overlaps />'+
                '<ogc:BBOX />'+
            '</ogc:Spatial_Operators>'+
        '</ogc:Spatial_Capabilities>'+
        '<ogc:Scalar_Capabilities>'+
            '<ogc:Logical_Operators />'+
            '<ogc:Comparison_Operators>'+
                '<ogc:Simple_Comparisons />'+
                '<ogc:Between />'+
                '<ogc:Like />'+
                '<ogc:NullCheck />'+
            '</ogc:Comparison_Operators>'+
            '<ogc:Arithmetic_Operators>'+
                '<ogc:Simple_Arithmetic />'+
                '<ogc:Functions>'+
                    '<ogc:Function_Names>'+
                        '<ogc:Function_Name nArgs="1">abs</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">abs_2</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">abs_3</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">abs_4</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">acos</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Area</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">asin</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">atan</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">atan2</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="3">between</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">boundary</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">boundaryDimension</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">buffer</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="3">bufferWithSegments</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">ceil</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">centroid</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">classify</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Collection_Average</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Collection_Bounds</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Collection_Count</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Collection_Max</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Collection_Median</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Collection_Min</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Collection_Sum</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">Collection_Unique</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">Concatenate</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">contains</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">convert</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">convexHull</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">cos</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">crosses</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">dateFormat</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">dateParse</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">difference</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">dimension</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">disjoint</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">distance</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">double2bool</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">endPoint</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">envelope</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">EqualInterval</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">equalsExact</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="3">equalsExactTolerance</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">equalTo</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">exp</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">exteriorRing</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">floor</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">geometryType</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">geomFromWKT</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">geomLength</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">getGeometryN</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">getX</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">getY</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">getZ</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">greaterEqualThan</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">greaterThan</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="0">id</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">IEEEremainder</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="3">if_then_else</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="11">in10</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="3">in2</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="4">in3</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="5">in4</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="6">in5</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="7">in6</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="8">in7</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="9">in8</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="10">in9</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">int2bbool</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">int2ddouble</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">interiorPoint</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">interiorRingN</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">intersection</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">intersects</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">isClosed</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">isEmpty</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">isLike</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">isNull</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">isRing</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">isSimple</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">isValid</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="3">isWithinDistance</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">length</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">lessEqualThan</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">lessThan</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">log</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">max</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">max_2</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">max_3</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">max_4</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">min</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">min_2</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">min_3</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">min_4</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">not</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">notEqualTo</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">numberFormat</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">numGeometries</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">numInteriorRing</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">numPoints</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">overlaps</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">parseBoolean</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">parseDouble</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">parseInt</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">parseLong</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="0">pi</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">pointN</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">pow</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">PropertyExists</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">Quantile</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="0">random</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">relate</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="3">relatePattern</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">rint</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">round</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">round_2</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">roundDouble</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">sin</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">sqrt</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">StandardDeviation</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">startPoint</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">strConcat</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">strEndsWith</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">strEqualsIgnoreCase</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">strIndexOf</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">strLastIndexOf</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">strLength</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">strMatches</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="4">strReplace</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">strStartsWith</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="3">strSubstring</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">strSubstringStart</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">strToLowerCase</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">strToUpperCase</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">strTrim</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">symDifference</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">tan</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">toDegrees</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">toRadians</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">touches</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="1">toWKT</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">union</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">UniqueInterval</ogc:Function_Name>'+
                        '<ogc:Function_Name nArgs="2">within</ogc:Function_Name>'+
                    '</ogc:Function_Names>'+
                '</ogc:Functions>'+
            '</ogc:Arithmetic_Operators>'+
        '</ogc:Scalar_Capabilities>'+
    '</ogc:Filter_Capabilities>'+
'</WFS_Capabilities>'
);