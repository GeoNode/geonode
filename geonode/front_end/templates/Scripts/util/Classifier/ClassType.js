function ClassType(scope) {
    var $scope = scope;
    var $this = this;

    this.reverseColor = function () {
        var colors = [];
        angular.forEach($scope.chosenValuesForGrid, function (item, index) {
            colors.push(item.style[scope.rampProperty]);
        });
        var colorLenght = colors.length;
        angular.forEach($scope.chosenValuesForGrid, function (item, index) {
            item.style[scope.rampProperty] = colors[colorLenght - index - 1];
        });
    }

    this.setColorForGridData = function (colorPaletteGenerator) {
        var colorList = colorPaletteGenerator.getColorList($scope.chosenValuesForGrid.length);
        angular.forEach($scope.chosenValuesForGrid, function (item, index) {
            if (!item.style) {
                item.style = angular.copy(scope.defaultStyle);
                item.style[scope.rampProperty] = colorList[index] ? colorList[index] : item.style[scope.rampProperty];
            }
        });
    };

    this.setColor = function (extractedItems, colorPaletteGenerator) {
        var colorList = colorPaletteGenerator.getColorList(extractedItems.length);
        angular.forEach(extractedItems, function (item, index) {
            if (!item.style) {
                item.style = angular.copy(scope.defaultStyle);
                item.style[scope.rampProperty] = colorList[index] ? colorList[index] : item.style[scope.rampProperty];
            }
        });
    };

    this.getField = function (field) {
        var foundItem = _.findWhere($scope.NeededAttributes, field);
        return foundItem !== undefined ? foundItem : null;
    };

    this.getCheckedItems = function ($filter) {
        return $filter('filter')($scope.flags.PropertyData, { checked: true });
    };

    this.addToGridData = function (extractedItems) {
        var tempList = $scope.chosenValuesForGrid.concat(extractedItems);
        if (this.orderItems) {
            this.orderItems(tempList);
        }
        $scope.chosenValuesForGrid = tempList;
    };

    this.removeItemsFromPropertyData = function (extractedItems) {
        angular.forEach(extractedItems, function (item, index) {
            var tempRangeItemIndex = $this.findItemIndex($scope.flags.PropertyData, item);
            $scope.flags.PropertyData.splice(tempRangeItemIndex, 1);
        });
    };

    this.findItemIndex = function (dataset, item) {
        for (var i = 0; i < dataset.length; i++) {
            if (this.areEqual(dataset[i], item))
                return i;
        }
        return -1;
    };

    this.resetColorsForUnselectedItems = function () {
        angular.forEach($scope.flags.PropertyData, function (item, index) {
            if (!item.style) {
                item.style = {};
            }
            item.style[scope.rampProperty] = undefined;
        });
    };
}