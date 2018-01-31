var mapModule = angular.module("mapModule", []);

mapModule.factory("mapModes", [function () {
    return {
        select: "select"
        , addShape: "addShape"
        , editShape: "editShape"
        , deleteShape: "deleteShape"
        , trackLocation: "trackLocation"
    };
}]).factory("reprojection", [
    'ol',
    function (ol) {
        return {
            coordinate: {
                to3857: function (latLng) {
                    return ol.proj.transform(latLng, 'EPSG:4326', 'EPSG:3857');
                },
                toLatLong: function (coordinate) {
                    return ol.proj.transform(coordinate, 'EPSG:3857', 'EPSG:4326');
                }
            },
            extent: {
                to3857: function (latLngExtent) {
                    return ol.proj.transformExtent(latLngExtent, 'EPSG:4326', 'EPSG:3857');
                },
                toLatLong: function (extent) {
                    return ol.proj.transformExtent(extent, 'EPSG:3857', 'EPSG:4326');
                }
            }
        };
    }
]).factory('strokeDashstyles', [
    function () {
        var strokeDashstyles = ['solid', 'dot', 'dash', 'dashdot', 'longdash', 'longdashdot'];

        var dashTypeText = {
            'solid': 'solid',
            'dot': 'dot',
            'dash': 'dash',
            'dashdot': 'dash dot',
            'longdash': 'long dash',
            'longdashdot': 'long dash dot'
        };

        var dashTypeSvgArray = {
            'solid': '',
            // 'dot': '1 12',
            // 'dash': '12 12',
            'dashdot': '12 12 1 12',
            'longdash': '24 12',
            'longdashdot': '24 12 1 12'
        };

        function getDashedArray(style) {
            var dashedArray = dashTypeSvgArray[style.strokeDashstyle];
            if (dashedArray != undefined) {
                return dashedArray;
            }
            if (style.strokeDashstyle == 'dot') {
                return "1 " + style.dashSpace;
            }
            return style.dashWidth + " " + style.dashSpace;
        }

        return {
            allDasheTypes: strokeDashstyles,
            defaultDashTypeName: 'solid',
            dashTypeText: dashTypeText,
            dashTypeSvgArray: dashTypeSvgArray,
            getDashedArray: getDashedArray
        };
    }
]).factory('featureTypes', [
    function () {
        var featureTypes = { point: 'point', polyline: 'polyline', polygon: 'polygon', geoTiff: 'geoTiff' }
        return featureTypes;
    }
]).factory('pointGraphics', ['urlResolver',
    function (urlResolver) {
        var pointGraphics = [];

        // [
        //     'ol-marker-blue.png',
        //     'ol-marker-gold.png',
        //     'ol-marker-green.png',
        //     'ol-marker-red.png'].forEach(function (graphics) {
        //         pointGraphics.push(urlResolver.resolveRoot('Content/symbology/' + graphics));
        //     });
            
        return pointGraphics;
    }
]).factory('pointGraphicNames', [
    function () {
        var graphicNames = ['circle', 'square', /*'star', */'x', 'cross', 'triangle'];
        var graphicIconClass = {
            'circle': 'fa fa-circle fa-fw',
            'square': 'fa fa-square fa-fw',
            //'star': 'fa fa-star fa-fw',
            'x': 'fa fa-times fa-fw',
            'cross': 'fa fa-plus fa-fw',
            'triangle': 'fa fa-play fa-rotate-270 fa-fw'
        };
        return {
            allGraphics: graphicNames,
            defaultGraphic: graphicNames[0],
            graphicIconClass: graphicIconClass,
            isValidGraphic: function (graphicName) {
                return !!graphicIconClass[graphicName];
            }
        };
    }
]).factory('pointTextGraphics', ['urlResolver', function (urlResolver) {

    var textGraphicNames = ['circledText', 'squaredText', 'triangledText', 'circledGraphic', 'squaredGraphic', 'triangledGraphic' ];
    var textGraphicIconClasses = {
        'circledText': 'circledText.png',
        'squaredText': 'squaredText.png',
        'triangledText': 'triangledText.png',
        'circledGraphic': 'circledText.png',
        'squaredGraphic': 'squaredText.png',
        'triangledGraphic': 'triangledText.png'
    };

    _.each(textGraphicIconClasses, function (value, key) {
        textGraphicIconClasses[key] = urlResolver.resolveRoot('Content/symbology/') + value;
    });

    var graphicNamesForSld = {
        'circledText': {
            name: 'circle',
            displacementY: -2
        },
        'squaredText': {
            name: 'square',
            displacementY: -2
        },
        'triangledText': {
            name: 'triangle',
            displacementY: -10
        },
        'circledGraphic': {
            isFontAwesome: true,
            name: 'circle',
            displacementY: -2
        },
        'squaredGraphic': {
            isFontAwesome: true,
            name: 'square',
            displacementY: -2
        },
        'triangledGraphic': {
            isFontAwesome: true,
            name: 'triangle',
            displacementY: -10
        }
    };

    return {
        // allTextGraphics: textGraphicNames,
        allTextGraphics: [],
        textGraphicIconClasses: textGraphicIconClasses,
        isValidTextGraphic: function (graphicName) {
            return graphicNamesForSld[graphicName] && !graphicNamesForSld[graphicName].isFontAwesome;
        },
        isValidFontAwesomeGraphic: function (graphicName) {
            return graphicNamesForSld[graphicName] && graphicNamesForSld[graphicName].isFontAwesome;
        },
        getGraphicNameForSld: function (textGraphicName) {
            return graphicNamesForSld[textGraphicName].name;
        },
        getDisplacementY: function (textGraphicName) {
            return graphicNamesForSld[textGraphicName].displacementY;
        }
    };
}]).factory('polygonFillPatterns', [
    function () {
        return {
            allPatterns: [
                { value: '', name: 'default' }
                , { value: 'shape://vertline', name: 'vertical line' }
                , { value: 'shape://horline', name: 'horizontal line' }
               // , { value: 'shape://slash', name: 'slash' }
                , { value: 'shape://backslash', name: 'backslash' }
                , { value: 'shape://dot', name: 'dot' }
                , { value: 'shape://plus', name: 'plus' }
               // , { value: 'shape://times', name: 'times' }
            ]
        }
    }]).factory('layerStyleGenerator', ['pointGraphicNames', 'strokeDashstyles', 'sldGenerator', 'labelingEditorService',
    function (pointGraphicNames, strokeDashstyles, sldGenerator, labelingEditorService) {
        var _colorChooser = new ColorChooser([
            "F0A3FF", "0075DC", "993F00", "4C005C", "191919",
            "005C31", "2BCE48", "FFCC99", "94FFB5", "8F7C00",
            "9DCC00", "C20088", "003380", "FFA405", "FFA8BB",
            "426600", "FF0010", "5EF1F2", "00998F", "E0FF66",
            "740AFF", "990000", "FFFF80", "FFFF00", "FF5005"
        ]);

        var defaultStylesByType = {
            'point': {
                strokeWidth: 1,
                fillOpacity: 0.75,
                pointRadius: 14,
                graphicName: pointGraphicNames.defaultGraphic,
                textFillColor: '#222026'
            },
            'polyline': {
                strokeWidth: 1
            },
            'polygon': {
                strokeWidth: 1,
                fillOpacity: 0.5,
                fillPattern: ""
            }
        };

        var commonDefaultStyles = {
            cursor: 'pointer',
            strokeDashstyle: strokeDashstyles.defaultDashTypeName
        }

        for (var type in defaultStylesByType) {
            defaultStylesByType[type] = angular.extend({}, commonDefaultStyles, defaultStylesByType[type]);
        }

        var commonSelectStyle = {
            externalGraphic: null,
            fillPattern: "",
            fillColor: "blue",
            fillOpacity: 0.4,
            strokeColor: "blue",
            strokeOpacity: 1,
            strokeWidth: 1,
            strokeDashstyle: "solid",
            cursor: "pointer",
            pointRadius: 6,
            graphicName: "circle",
            textFillColor: '#222026'
        };

        function generate(featureType) {
            var strokeColor = _colorChooser.nextColor();
            var defaultStyle = {
                strokeColor: '#' + strokeColor
            };
            var selectStyle = {
                strokeColor: '#0000ff',
                fillColor: '#0000ff'
            };

            if (featureType != 'polyline') {
                var strokeHsv = $c.hex2hsv(strokeColor);
                var fillRgb = $c.hsv2rgb(strokeHsv.H, strokeHsv.S, strokeHsv.V / 2);
                defaultStyle.fillColor = $c.rgb2hex(fillRgb.R, fillRgb.G, fillRgb.B);
            }

            defaultStyle = angular.extend({}, defaultStylesByType[featureType], defaultStyle);
            selectStyle = angular.extend({}, commonSelectStyle, selectStyle);

            var style = {
                "default": defaultStyle,
                "select": selectStyle,
                "labelConfig": labelingEditorService.getDefaultLabelConfig()
            }

            //TODO: restore
            /*for (var styleType in style) {
                style[styleType] = angular.extend({}, OpenLayers.Feature.Vector.style[styleType], style[styleType]);
            }*/

            return style;
        }

        function generateDefaultRasterStyle() {
            var defaultStyle = {
                opacity: 1,
            };
            var selectStyle = {};

            var style = {
                "default": defaultStyle,
                "select": selectStyle,
                "labelConfig": labelingEditorService.getDefaultLabelConfig()
            }

            return style;
        }

        function ColorChooser(colorSet) {
            var _current = Math.floor(Math.random() * colorSet.length);

            this.nextColor = function () {
                _current = (++_current) % colorSet.length;

                return colorSet[_current];
            };
        }

        function getSldStyle(featureType, style, includeHeader, classification, labelConfig) {
            return sldGenerator.getSld(featureType, style, includeHeader, classification, labelConfig);
        }

        function getConditionalSld(classification) {
            return sldGenerator.getClassificationConditionalSld(classification);
        }

        function getLabelingSld(labelConfig, featureType) {
            return sldGenerator.getLabelingSld(labelConfig, featureType);
        }

        return {
            generate: generate,
            getSldStyle: getSldStyle,
            getConditionalSld: getConditionalSld,
            generateDefaultRasterStyle: generateDefaultRasterStyle,
            getLabelingSld: getLabelingSld
        };
    }
    ]).factory('mapAccessLevel', [
    function () {
        var urlParts = window.location.pathname.split("/");
        var action = urlParts[urlParts.length - 3];
        var isPublic = !!action && action.toLowerCase() == 'public';
        var isEmbedded = !!action && action.toLowerCase() == 'embedded';
        var isPrivate = !isPublic && !isEmbedded;
        var publicId = isPrivate ? null : urlParts[urlParts.length - 2];

        return {
            isPublic: isPublic,
            isEmbedded: isEmbedded,
            isPrivate: isPrivate,
            publicId: publicId,
            isWritable: isPrivate
        }
    }
    ]).factory('google', [
    function () {
        return window.google;
    }
    ]).factory('ol', [
    function () {
        return window.ol;
    }
    ]);