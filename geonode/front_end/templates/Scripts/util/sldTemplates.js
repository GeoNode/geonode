appModule.factory('sldTemplateService', [function() {

    return {
        simplePointTemplate: '{9}' +
            '<NamedLayer>' +
            '<Name>' +
            '{7}' +
            '</Name>' +
            '</NamedLayer>' +
            '<UserStyle>' +
            '<Name>' +
            '{8}' +
            '</Name>' +
            '</UserStyle>' +
            '<PointSymbolizer> ' +
            '<Graphic> ' +
            '<Mark> ' +
            '<WellKnownName>{0}</WellKnownName> ' +
            '<Stroke> ' +
            '<CssParameter name="stroke">{1}</CssParameter>' +
            '<CssParameter name="stroke-width">{2}</CssParameter> ' +
            '<CssParameter name="stroke-dasharray">{3}</CssParameter>' +
            '</Stroke> ' +
            '<Fill> ' +
            '<CssParameter name="fill">{4}</CssParameter> ' +
            '<CssParameter name="fill-opacity">{5}</CssParameter> ' +
            '</Fill> ' +
            '</Mark> ' +
            '<Size>{6}</Size> ' +
            '</Graphic> ' +
            '</PointSymbolizer>',
        pointTemplateForTextGraphic: '{8}' +
            '<PointSymbolizer> ' +
            '<Graphic> ' +
            '<Mark> ' +
            '<WellKnownName>{0}</WellKnownName> ' +
            '<Stroke> ' +
            '<CssParameter name="stroke">{1}</CssParameter>' +
            '<CssParameter name="stroke-width">{2}</CssParameter> ' +
            '</Stroke> ' +
            '<Fill> ' +
            '<CssParameter name="fill">{3}</CssParameter> ' +
            '<CssParameter name="fill-opacity">{4}</CssParameter> ' +
            '</Fill> ' +
            '</Mark> ' +
            '<Size>30</Size> ' +
            '</Graphic> ' +
            '</PointSymbolizer>' +
            '<TextSymbolizer>' +
            '<Label>{5}</Label>' +
            '<Font><CssParameter name="font-family">Times</CssParameter>' +
            '<CssParameter name="font-size">14</CssParameter>' +
            '<CssParameter name="font-style">normal</CssParameter>' +
            '<CssParameter name="font-weight">bold</CssParameter>' +
            '</Font>' +
            '<LabelPlacement>' +
            '<PointPlacement>' +
            '<AnchorPoint>' +
            '<AnchorPointX>0.5</AnchorPointX>' +
            '<AnchorPointY>0.5</AnchorPointY>' +
            '</AnchorPoint>' +
            '<Displacement>' +
            '<DisplacementX>0</DisplacementX>' +
            '<DisplacementY>{6}</DisplacementY>' +
            '</Displacement>' +
            '</PointPlacement>' +
            '</LabelPlacement>' +
            '<Fill>' +
            '<CssParameter name="fill">{7}</CssParameter>' +
            '</Fill>' +
            '</TextSymbolizer>',
        pointTemplateForFontAwosomeTextGraphic: '{8}' +
            '<PointSymbolizer> ' +
            '<Graphic> ' +
            '<Mark> ' +
            '<WellKnownName>{0}</WellKnownName> ' +
            '<Stroke> ' +
            '<CssParameter name="stroke">{1}</CssParameter>' +
            '<CssParameter name="stroke-width">{2}</CssParameter> ' +
            '</Stroke> ' +
            '<Fill> ' +
            '<CssParameter name="fill">{3}</CssParameter> ' +
            '<CssParameter name="fill-opacity">{4}</CssParameter> ' +
            '</Fill> ' +
            '</Mark> ' +
            '<Size>30</Size> ' +
            '</Graphic> ' +
            '</PointSymbolizer>' +
            '<PointSymbolizer>' +
            '<Graphic>' +
            '<Mark>' +
            '<WellKnownName>ttf://FontAwesome#{9}</WellKnownName>' +
            '<Fill>' +
            '<CssParameter name="fill">{7}</CssParameter>' +
            '</Fill>' +
            '</Mark>' +
            '<Size>14</Size>' +
            '</Graphic>' +
            '</PointSymbolizer>',
        pointWithExternalGraphicTemplate: '{4}' +
            '<PointSymbolizer>' +
            '<Graphic> ' +
            '<ExternalGraphic> ' +
            '<OnlineResource xlink:type="simple" xlink:href="{0}{1}"/> ' +
            '<Format>image/png</Format>' +
            '</ExternalGraphic> ' +
            '<Opacity>' +
            '<ogc:Literal>{2}</ogc:Literal>' +
            '</Opacity>' +
            '<Size>{3}</Size> ' +
            '</Graphic> ' +
            '</PointSymbolizer>',

        simplePolylineTemplate: '{3}' +
            '<LineSymbolizer> ' +
            '<Stroke> ' +
            '<CssParameter name="stroke">{0}</CssParameter> ' +
            '<CssParameter name="stroke-width">{1}</CssParameter> ' +
            '<CssParameter name="stroke-linecap">round</CssParameter>' +
            '<CssParameter name="stroke-dasharray">{2}</CssParameter>' +
            '</Stroke> ' +
            '</LineSymbolizer>',

        simplePolygonTemplate: '{7}' +
            '<sld:NamedLayer>' +
            '   <sld:Name>{5}</sld:Name>' +
            '   <sld:UserStyle>' +
            '       <sld:Name>{6}</sld:Name>' +
            '       <sld:IsDefault>1</sld:IsDefault>' +
            '       <sld:FeatureTypeStyle>' +
            '           <sld:Rule>' +
            '               <sld:PolygonSymbolizer>' +
            '                   <sld:Fill>' +
            '                       <sld:CssParameter name="fill">{0}</sld:CssParameter> ' +
            '                       <sld:CssParameter name="fill-opacity">{1}</sld:CssParameter> ' +
            '                   </sld:Fill>' +
            '                   <sld:Stroke>' +
            '                       <sld:CssParameter name="stroke">{2}</sld:CssParameter> ' +
            '                       <sld:CssParameter name="stroke-width">{3}</sld:CssParameter> ' +
            // '                       <sld:CssParameter name="stroke-dasharray">{4}</sld:CssParameter>' +
            '                   </sld:Stroke>' +
            '               </sld:PolygonSymbolizer>' +
            '           </sld:Rule> ' +
            '           <sld:Rule>' +
            '               <!--label starts-->{8}' +
            '               <!--label ends-->' +
            '           </sld:Rule> ' +
            '       </sld:FeatureTypeStyle>' +
            '       <sld:FeatureTypeStyle>' +
            '           <!--classification starts-->{9}' +
            '           <!--classification ends-->' +
            '       </sld:FeatureTypeStyle>' +
            '   </sld:UserStyle>' +
            '</sld:NamedLayer>',

        fillPatternTemplate: '<GraphicFill>' +
            '<Graphic>' +
            '<Mark>' +
            '<WellKnownName>{0}</WellKnownName>' +
            '<Stroke>' +
            '<CssParameter name="stroke">{1}</CssParameter>' +
            '<CssParameter name="stroke-width">2</CssParameter>' +
            '</Stroke>' +
            '</Mark>' +
            '<Size>{2}</Size>' +
            '</Graphic>' +
            '</GraphicFill>',
        simpleRasterTemplate: '<RasterSymbolizer>' +
            '<Opacity>{0}</Opacity>' +
            '</RasterSymbolizer>',

        sldHeader: '<sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld" version="1.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml">' +
            '{0}' +
            '</sld:StyledLayerDescriptor>',

        labelTemplateForPointAndPolygon: '<TextSymbolizer>' +
            '<Label>' +
            '<ogc:PropertyName>{0}</ogc:PropertyName>' +
            '</Label>' +
            '<Font><CssParameter name="font-family">{1}</CssParameter>' +
            '<CssParameter name="font-size">{2}</CssParameter>' +
            '<CssParameter name="font-style">{3}</CssParameter>' +
            '<CssParameter name="font-weight">{4}</CssParameter>' +
            '</Font>' +
            '<LabelPlacement>' +
            '<PointPlacement>' +
            '<AnchorPoint>' +
            '<AnchorPointX>{5}</AnchorPointX>' +
            '<AnchorPointY>0</AnchorPointY>' +
            '</AnchorPoint>' +
            '<Displacement>' +
            '<DisplacementX>{6}</DisplacementX>' +
            '<DisplacementY>{7}</DisplacementY>' +
            '</Displacement>' +
            '<Rotation>{8}</Rotation>' +
            '</PointPlacement>' +
            '</LabelPlacement>' +
            '<Fill>' +
            '<CssParameter name="fill">{9}</CssParameter>' +
            '</Fill>' +
            '{10}' +
            '{11}' +
            '</TextSymbolizer>',

        labelTemplateForPolyline: '<TextSymbolizer>' +
            '<Label>' +
            '<ogc:PropertyName>{0}</ogc:PropertyName>' +
            '</Label>' +
            '<Font><CssParameter name="font-family">{1}</CssParameter>' +
            '<CssParameter name="font-size">{2}</CssParameter>' +
            '<CssParameter name="font-style">{3}</CssParameter>' +
            '<CssParameter name="font-weight">{4}</CssParameter>' +
            '</Font>' +
            '<LabelPlacement>' +
            '<LinePlacement>' +
            '<PerpendicularOffset>' +
            '{5}' +
            '</PerpendicularOffset>' +
            '</LinePlacement>' +
            '</LabelPlacement>' +
            '<Fill>' +
            '<CssParameter name="fill">{6}</CssParameter>' +
            '</Fill>' +
            '{7}' +
            '{8}' +
            '</TextSymbolizer>',
        getLabelOutLineTemplate: function(showBorder) {
            return !showBorder ?
                '' :
                '<Halo>' +
                '<Fill>' +
                '<CssParameter name="fill">{0}</CssParameter>' +
                '</Fill>' +
                '</Halo>';
        },
        labelingVendorOptionTemplates: {
            followLine: '<VendorOption name="followLine">true</VendorOption>',
            repeat: '<VendorOption name="repeat">{0}</VendorOption>',
            autoWrap: '<VendorOption name="autoWrap">{0}</VendorOption>',
            resolveConflict: '<VendorOption name="conflictResolution">{0}</VendorOption>',
            maxDisplacement: '<VendorOption name="maxDisplacement">{0}</VendorOption>'
        },

        getUniqueFilterTemplate: function() {
            return '<ogc:PropertyIsEqualTo>' +
                '<ogc:PropertyName>{0}</ogc:PropertyName>' +
                '<ogc:Literal>{1}</ogc:Literal>' +
                '</ogc:PropertyIsEqualTo>';
        },

        getUniqueFilterTemplateForNullValue: function() {
            return '<PropertyIsNull>' +
                '<PropertyName>{0}</PropertyName>' +
                '</PropertyIsNull>';
        },

        getRangeFilterTemplateForFirstRange: function() {
            return '<And>' +
                '<ogc:PropertyIsGreaterThanOrEqualTo>' +
                '<ogc:PropertyName>{0}</ogc:PropertyName>' +
                '<ogc:Literal>{1}</ogc:Literal>' +
                '</ogc:PropertyIsGreaterThanOrEqualTo>' +
                '<ogc:PropertyIsLessThanOrEqualTo>' +
                '<ogc:PropertyName>{0}</ogc:PropertyName>' +
                '<ogc:Literal>{2}</ogc:Literal>' +
                '</ogc:PropertyIsLessThanOrEqualTo>' +
                '</And>';
        },

        rangeFilterConditionalTemplate: '<And>' +
            '<ogc:PropertyIsGreaterThan>' +
            '<ogc:PropertyName>{0}</ogc:PropertyName>' +
            '<ogc:Literal>{1}</ogc:Literal>' +
            '</ogc:PropertyIsGreaterThan>' +
            '<ogc:PropertyIsLessThanOrEqualTo>' +
            '<ogc:PropertyName>{0}</ogc:PropertyName>' +
            '<ogc:Literal>{2}</ogc:Literal>' +
            '</ogc:PropertyIsLessThanOrEqualTo>' +
            '</And>',

        getRangeFilterTemplate: function() {
            return '<And>' +
                '<ogc:PropertyIsGreaterThan>' +
                '<ogc:PropertyName>{0}</ogc:PropertyName>' +
                '<ogc:Literal>{1}</ogc:Literal>' +
                '</ogc:PropertyIsGreaterThan>' +
                '<ogc:PropertyIsLessThanOrEqualTo>' +
                '<ogc:PropertyName>{0}</ogc:PropertyName>' +
                '<ogc:Literal>{2}</ogc:Literal>' +
                '</ogc:PropertyIsLessThanOrEqualTo>' +
                '</And>';
        },
        wrapWithFilterTag: function(template) {
            return template ?
                '<ogc:Filter>' +
                template +
                '</ogc:Filter>' :
                '';
        },
        wrapWithNotTag: function(template) {
            return template ? '<Not>' + template + '</Not>' : '';
        },
        wrapWithAndTag: function(template) {
            return template ? '<And>' + template + '</And>' : '';
        },
        wrapWithRuleTag: function(template) {
            return template ? '<Rule>' + template + '</Rule>' : '';
        },
        makeColorMapEntryTag: function(color, quantity) {
            return (color && !isNaN(quantity)) ?
                '<ColorMapEntry color="' + color + '" quantity="' + quantity + '" label="data" />' :
                '';
        },
        makeTransparentColorMapEntryTag: function(color, quantity) {
            return (color && !isNaN(quantity)) ?
                '<ColorMapEntry color="' + color + '" quantity="' + quantity + '" label="data" opacity="0" />' :
                '';
        },
        heatmapTemplate: '<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"><UserStyle><FeatureTypeStyle>' +
            '<Transformation>' +
            '<ogc:Function name="gs:Heatmap">' +
            '<ogc:Function name="parameter">' +
            '<ogc:Literal>data</ogc:Literal>' +
            '</ogc:Function>' +
            '<ogc:Function name="parameter">' +
            '<ogc:Literal>weightAttr</ogc:Literal>' +
            '<ogc:Literal>{0}</ogc:Literal>' +
            '</ogc:Function>' +
            '<ogc:Function name="parameter">' +
            '<ogc:Literal>radiusPixels</ogc:Literal>' +
            '<ogc:Function name="env">' +
            '<ogc:Literal>radius</ogc:Literal>' +
            '<ogc:Literal>{1}</ogc:Literal>' +
            '</ogc:Function>' +
            '</ogc:Function>' +
            '<ogc:Function name="parameter">' +
            '<ogc:Literal>pixelsPerCell</ogc:Literal>' +
            '<ogc:Literal>{2}</ogc:Literal>' +
            '</ogc:Function>' +
            '<ogc:Function name="parameter">' +
            '<ogc:Literal>outputBBOX</ogc:Literal>' +
            '<ogc:Function name="env">' +
            '<ogc:Literal>wms_bbox</ogc:Literal>' +
            '</ogc:Function>' +
            '</ogc:Function>' +
            '<ogc:Function name="parameter">' +
            '<ogc:Literal>outputWidth</ogc:Literal>' +
            '<ogc:Function name="env">' +
            '<ogc:Literal>wms_width</ogc:Literal>' +
            '</ogc:Function>' +
            '</ogc:Function>' +
            '<ogc:Function name="parameter">' +
            '<ogc:Literal>outputHeight</ogc:Literal>' +
            '<ogc:Function name="env">' +
            '<ogc:Literal>wms_height</ogc:Literal>' +
            '</ogc:Function>' +
            '</ogc:Function>' +
            '</ogc:Function>' +
            '</Transformation>' +
            '<Rule>' +
            '<RasterSymbolizer>' +
            '<Geometry>' +
            '<ogc:PropertyName>SHAPE</ogc:PropertyName></Geometry>' +
            '<Opacity>0.5</Opacity>' +
            '<ColorMap type="ramp" >' +
            '<ColorMapEntry color="{3}" quantity="0" label="nodata" opacity="0"/>' +
            '<ColorMapEntry color="{4}" quantity=".1" label="nodata"/>' +
            '<ColorMapEntry color="{5}" quantity="0.5" label="values" />' +
            '<ColorMapEntry color="{6}" quantity="0.9" label="values" />' +
            '</ColorMap>' +
            '</RasterSymbolizer>' +
            '</Rule>' +
            '</FeatureTypeStyle></UserStyle></StyledLayerDescriptor>',

        weightedPointTemplate: '<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd">' +
            '<UserStyle>' +
            '<FeatureTypeStyle>' +
            '{0}' +
            '</FeatureTypeStyle>' +
            '</UserStyle>' +
            '</StyledLayerDescriptor>',

        rasterColorTemplate: '<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd">' +
            '<UserStyle>' +
            '<FeatureTypeStyle>' +
            '<Rule>' +
            '<!--default filter starts--><!--default filter ends--><!--default style starts-->' +
            '<RasterSymbolizer>' +
            '<Opacity>{0}</Opacity>' +
            '<ColorMap>' +
            '{1}' +
            '</ColorMap>' +
            '</RasterSymbolizer>' +
            '<!--default style ends--></Rule> <Rule><!--label starts--><!--label ends-->' +
            '</Rule>' +
            '</FeatureTypeStyle>' +
            '<FeatureTypeStyle>' +
            '<!--classification starts--><!--classification ends-->' +
            '</FeatureTypeStyle>' +
            '</UserStyle>' +
            '</StyledLayerDescriptor>',

        wrapWithSldHeader: function(sld) {
            return '<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd">' +
                '<UserStyle>' +
                '<FeatureTypeStyle>' +
                sld +
                '</FeatureTypeStyle>' +
                '</UserStyle>' +
                '</StyledLayerDescriptor>';
        },
        chartSizeTemplate: '<Size>' +
            '<ogc:Add>' +
            '<ogc:Literal>20</ogc:Literal>' +
            '<ogc:Mul>' +
            '<ogc:Div>' +
            '<ogc:PropertyName>{0}</ogc:PropertyName>' +
            '<ogc:Literal>{1}</ogc:Literal>' +
            '</ogc:Div>' +
            '<ogc:Literal>100</ogc:Literal>' +
            '</ogc:Mul>' +
            '</ogc:Add>' +
            '</Size>',
        chartSld: function(config, chartDataString, seriesColor, chartSizeString) {
            /*return '<?xml version="1.0" encoding="ISO-8859-1"?> <StyledLayerDescriptor version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
                '<NamedLayer>' +
                '<Name></Name>' +
                '<UserStyle>' +
                '<Name>Pie charts</Name>' +

                '<FeatureTypeStyle>' +
                '<Rule>' +
                '<PolygonSymbolizer>' +
                '<Fill>' +
                '<CssParameter name="fill">#AAAAAA</CssParameter>' +
                '</Fill>' +
                '<Stroke />' +
                '</PolygonSymbolizer>' +
                '</Rule>' +
                '</FeatureTypeStyle>' +*/

            return '<!--chart settings starts-->' +
                '<FeatureTypeStyle>' +
                '<Rule>' +
                '<PointSymbolizer>' +
                '<Graphic>' +
                '<ExternalGraphic>' +
                '<OnlineResource xlink:href="http://chart?cht=' +
                config.chartId +
                '&amp;' +
                chartDataString +
                '&amp;chf=bg,s,FFFFFF00&amp;' +
                seriesColor + '"/>' +
                '<Format>application/chart</Format>' +
                '</ExternalGraphic>' +
                /*'<Size>' +
                '<ogc:Add>' +
                '<ogc:Literal>20</ogc:Literal>' +
                '<ogc:Literal>20</ogc:Literal>' +
                '</ogc:Add>' +
                '</Size>' +*/
                chartSizeString +
                '</Graphic>' +
                '</PointSymbolizer>' +
                '</Rule>' +
                '</FeatureTypeStyle>' +
                '<!--chart settings ends-->'
                /* +

                               '</UserStyle>' +
                               '</NamedLayer>' +
                               '</StyledLayerDescriptor>'*/
            ;
        }
    }
}]);