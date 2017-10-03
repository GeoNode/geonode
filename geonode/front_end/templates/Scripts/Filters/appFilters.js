angular.module("app.filters", []).filter('identifyBlank', [
    function () {
        return function (value) {
            if (value === "" || value === undefined || value === null) {
                return "<Blank>";
            }
            return value;
        };
    }
]).filter("byteFilter", [
    function () {
        return function (byteValue, decimal) {
            decimal = isNaN(decimal) ? 2 : decimal;
            if (isNaN(byteValue)) {
                return byteValue;
            }
            var count = -1;
            var oldValue = byteValue;

            while (byteValue >= 1) {
                count++;
                oldValue = byteValue;
                byteValue /= 1024;
            }

            switch (count) {
                case 1:
                    return +oldValue.toFixed(decimal) + " KB";
                case 2:
                    return +oldValue.toFixed(decimal) + " MB";
                case 3:
                    return +oldValue.toFixed(decimal) + " GB";
                case 4:
                    return +oldValue.toFixed(decimal) + " TB";
                default:
                    return +oldValue.toFixed(decimal) + " B";
            }
        };
    }
]).filter("largeToInfinityFilter", [
    function () {
        return function (value, minimumValueOfInfinity) {
            minimumValueOfInfinity = isNaN(minimumValueOfInfinity) ? 999999 : minimumValueOfInfinity;
            return value > minimumValueOfInfinity ? '∞' : value;
        }
    }
]).filter("maxBoundary", [
    function () {
        return function (value, maxValue) {
            return value > maxValue ? maxValue : value;
        }
    }
]).filter("fileTypeFilter", [
    function () {
        return function (collection, type, property) {
            if (type == "All") return collection;
            var filteredColletion = [];
            for (var i in collection) {
                if (collection[i][property].toLowerCase() == type.toLowerCase()) {
                    filteredColletion.push(collection[i]);
                }
            }
            return filteredColletion;
        }
    }
]).filter('contrastColor', [
    function () {
        return function (hexcolor) {
            hexcolor = hexcolor.substring('1');
            return (parseInt(hexcolor, 16) > 0xffffff / 2) ? 'black' : 'white';
        }
    }
]).filter('plus', [
    function () {
        return function (num1, num2) {
            return Number(num1) + Number(num2);
        }
    }
]);
