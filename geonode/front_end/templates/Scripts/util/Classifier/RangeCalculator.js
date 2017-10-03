function RangeCalculator() {
    this.calculate = function (min, max, division) {

        var rangeLength = (max - min) / division;
        var rangelist = [];
        var minimum = min;

        for (var i = 0; i < division; i++) {
            rangelist[i] = { rangeMin: minimum };
            if (i == (division - 1)) {
                rangelist[i].rangeMax = max;
                break;
            }
            else rangelist[i].rangeMax = (minimum + rangeLength);
            minimum = rangelist[i].rangeMax;
        }
        return rangelist; //fixedPrecision(rangelist);
    };

    function fixedPrecision(rangeList) {
        for (var i in rangeList) {
            rangeList[i].rangeMin = parseFloat(rangeList[i].rangeMin.toFixed(8));
            rangeList[i].rangeMax = parseFloat(rangeList[i].rangeMax.toFixed(8));
        }
        return rangeList;
    }

    this.adjustRange = function (rangeList, item) {
        var tempIndex = findItemIndex(rangeList, item);
        for (var i = tempIndex + 1; i < (rangeList.length) ;) {
            if (rangeList[tempIndex].rangeMax >= rangeList[i].rangeMax) {
                rangeList.splice(i, 1);
            }
            else {
                rangeList[i].rangeMin = rangeList[tempIndex].rangeMax;
                rangeList[i].rangeMax = rangeList[i].rangeMax;
                break;
            }
        }
    };

    this.adjustNullRange = function (rangeList, item, max) {

        var tempIndex = findItemIndex(rangeList, item);
        if (tempIndex == (rangeList.length - 1)) {
            rangeList[tempIndex].rangeMax = max;
        }
        else {
            rangeList[tempIndex].rangeMax = rangeList[tempIndex + 1].rangeMin;
        }
    };

    function findItemIndex(dataSet, item) {
        for (var i = 0; i < dataSet.length; i++) {
            if (dataSet[i].rangeMin == item.rangeMin && dataSet[i].rangeMax == item.rangeMax)
                return i;
        }
        return -1;
    }
}


