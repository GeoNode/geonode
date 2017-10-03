function ColorPaletteGenerator() {

    var lastColorIndex = 0;
    var lastColorPaletteIndex = -1;
    var totalInterval = 50, colorPalettes;

    (function getColorPalettes() {
        colorPalettes = Jantrik.gradientGenerator.getColorPalettes(totalInterval, true);
    })();

    this.setState = function (state) {
        if (!state) return;
        lastColorPaletteIndex = state.lastColorPaletteIndex;
        lastColorIndex = state.lastColorIndex;
    };

    this.getState = function () {
        return {
            lastColorPaletteIndex: lastColorPaletteIndex,
            lastColorIndex: lastColorIndex
        };
    };

    this.getChosenPalette = function () {
        return this.getItemAt(lastColorPaletteIndex);
    };

    this.getPaletteData = function () {
        return colorPalettes;
    };

    this.getItemAt = function (index) {
        return colorPalettes[index];
    };

    this.resetColorIndex = function () {
        lastColorIndex = 0;
    };

    this.setChosenPalette = function (chosenPalette) {
        var tempIndex = colorPalettes.indexOf(chosenPalette);
        if (tempIndex !== lastColorPaletteIndex) {
            lastColorIndex = 0;
            lastColorPaletteIndex = tempIndex;
        }
    };

    this.getColorList = function (numberOfColors) {

        if (lastColorPaletteIndex == -1) return [];
        if (numberOfColors > totalInterval) return getColorListForLargerRange(numberOfColors);

        var colorlist = [];
        var interval = Math.floor(totalInterval / numberOfColors);

        for (var i = 0, j = 0; i < numberOfColors; i++, j += interval) {
            colorlist[i] = colorPalettes[lastColorPaletteIndex][j];
        }
        return colorlist;
    };

    function getColorListForLargerRange(numberOfColors) {
        var colorlist = [];
        var roundedDivisions = Math.ceil(numberOfColors / totalInterval);
        var remainingColors = numberOfColors % totalInterval;
        var count = 0, i = 0, j = 0;
        for (; i < totalInterval; j++) {
            colorlist[j] = colorPalettes[lastColorPaletteIndex][i];
            count++;

            if (count == roundedDivisions) {
                remainingColors--;
                count = 0;
                i++;
                if (remainingColors == 0) {
                    roundedDivisions--;
                    remainingColors = -1;
                }
            }
        }
        return colorlist;
    }
}

