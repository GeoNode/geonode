(function (jantrik) {
    (function (gradientGenerator) {
        var totalInterval;
        var initialColors = [
                                {
                                    color1: { r: 2, g: 51, b: 80 }, color2: { r: 212, g: 239, b: 241 }
                                },
                                {
                                    color1: { r: 1, g: 20, b: 85 }, color2: { r: 212, g: 222, b: 241 }
                                },
                                {
                                    color1: { r: 85, g: 0, b: 48 }, color2: { r: 255, g: 216, b: 239 }
                                },
                                {
                                    color1: { r: 172, g: 0, b: 40 }, color2: { r: 255, g: 216, b: 225 }
                                },
                                {
                                    color1: { r: 255, g: 1, b: 61 }, color2: { r: 222, g: 202, b: 207 }
                                },
                                {
                                    color1: { r: 191, g: 44, b: 0 }, color2: { r: 253, g: 231, b: 224 }
                                },
                                {
                                    color1: { r: 81, g: 38, b: 25 }, color2: { r: 250, g: 220, b: 211 }
                                },
                                {
                                    color1: { r: 111, g: 111, b: 4 }, color2: { r: 253, g: 253, b: 240 }
                                },
                                {
                                    color1: { r: 43, g: 111, b: 4 }, color2: { r: 244, g: 255, b: 238 }
                                },
                                {
                                    color1: { r: 0, g: 107, b: 71 }, color2: { r: 238, g: 255, b: 250 }
                                },
                                {
                                    color1: { r: 0, g: 107, b: 121 }, color2: { r: 233, g: 255, b: 254 }
                                }
        ];

        var uniqueColors = [['#B0171F', '#8B5F65', '#5D478B', '#EE799F', '#DC143C', '#836FFF', '#CD6889', '#8B8386', '#00FF7F', '#FF3E96',
                            '#FF83FA', '#8B4789', '#EED2EE', '#4876FF', '#68228B', '#CD00CD', '#800080', '#E066FF', '#4B0082', '#E6E6FA',
                            '#0000EE', '#CAFF70', '#CDAD00', '#191970', '#27408B', '#CAE1FF', '#458B74', '#6E7B8B', '#C6E2FF', '#104E8B',
                            '#33A1C9', '#00688B', '#53868B', '#00868B', '#C1CDCD', '#0080CD', '#00C78C', '#98FB98', '#556B2F', '#FFFF00',
                            '#00BFFF', '#872657', '#8B8B00', '#FFA500', '#FFE4B5', '#FF6103', '#8E8E38', '#7D9EC0', '#C67171', '#5B5B5B']
        ];


        function componentToHex(c) {
            var hex = c.toString(16);
            return hex.length == 1 ? "0" + hex : hex;
        }

        function rgbToHex(r, g, b) {
            return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
        }

        function getColorSpectrums(color1, color2, steps) {
            var colorSets = [];
            for (var i = 0; i < steps; i++) {
                var ratio = i / steps;
                var r = Math.floor(color1.r * ratio + color2.r * (1 - ratio));
                var g = Math.floor(color1.g * ratio + color2.g * (1 - ratio));
                var b = Math.floor(color1.b * ratio + color2.b * (1 - ratio));
                colorSets.push(rgbToHex(r, g, b));
            }
            return colorSets;
        }


        gradientGenerator.getColorPalettes = function (numberOfIntervals, includeUniqueColors) {
            totalInterval = numberOfIntervals;
            var colorPalettes = [];
            if (includeUniqueColors) {
                for (var i in uniqueColors) {
                    colorPalettes.push(uniqueColors[i]);
                }
            }
            for (var j in initialColors) {
                colorPalettes.push(getColorSpectrums(initialColors[j].color1, initialColors[j].color2, totalInterval));
            }
            return colorPalettes;
        }

        gradientGenerator.getVisualizationColorPalettes = function () {
            return [['#FFEBD6', '#F5CBAE', '#EBA988', '#E08465', '#D65D45', '#CC3527', '#C40A0A'],
                ['#0000FF', '#6666FF', '#B3B3FF', '#FFFFFF', '#FFB3B3', '#FF6666', '#FF0000'],
                ['#FFFF80', '#FCE062', '#F7C348', '#F2A72E', '#C46D1B', '#963A0C', '#6B0601'],
                ['#F5F500', '#F5CC00', '#F5A300', '#F57A00', '#F55200', '#F52900', '#F50000'],
                ['#C2523C', '#E68E1C', '#F7D707', '#7BED00', '#0EC441', '#1E9094', '#0B2C7A'],
                ['#FFFFFF', '#D5D5D5', '#AAAAAA', '#808080', '#555555', '#2B2B2B', '#080808']];
        }

    })(jantrik.gradientGenerator = jantrik.gradientGenerator || {});
})(window.Jantrik = window.Jantrik || {});