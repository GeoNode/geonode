function RangeType(http, scope, rangeCalculator, attributeDefinitionHelper, filter) {
    var $this = this;
    var $http = http;
    var $scope = scope;
    var rangeFunctionalty = rangeCalculator;
    ClassType.call(this, scope);

    this.isDataLoading = false;

    this.addSelectionsToGrid = function (colorPaletteGenerator) {
        var extractedItems = this.getCheckedItems(filter);
        if (extractedItems.length == 0)
            return;
        this.getCount(extractedItems, function (resultData) {
            $this.setColor(resultData, colorPaletteGenerator);
            $this.addToGridData(resultData);
            $this.removeItemsFromPropertyData(resultData);
        });
    };

    this.removeItem = function (rowIndex) {
        var extractedItems = $scope.chosenValuesForGrid.splice(rowIndex, 1);
        rangeFunctionalty.removeRange($scope.chosenValuesForGrid, extractedItems[0]);
    };

    this.removeRange = function (gridData, item) {
        var itemIndex = gridData.indexOf(item);
        if (itemIndex == (gridData.length - 1))
            gridData[itemIndex - 1].rangeMax = gridData[itemIndex + 1].rangeMax + gridData[itemIndex].rangeMax;
        else
            gridData[itemIndex + 1].rangeMin = gridData[itemIndex].rangeMin;
    };

    this.areEqual = function (a, b) {
        if (a.rangeMin == b.rangeMin && a.rangeMax == b.rangeMax)
            return true;
        return false;
    };

    this.getDivisionCount = function () {
        return $scope.chosenValuesForGrid.length + $scope.flags.PropertyData.length;
    };

    this.getUnselectedItems = function () {
        return $scope.flags.PropertyData;
    };

    this.setInitialUnselectedItems = function (unselectedItems) {
        $scope.flags.PropertyData = unselectedItems;
    };

    this.setFieldDropDown = function () {
        var attributeDefs = attributeDefinitionHelper.getNumericAttributeDefs(scope.Attributes);
        $scope.NeededAttributes = attributeDefs.concat(attributeDefinitionHelper.getSpatialAttributeDefs(scope.Attributes));
    };

    this.setInitialSettings = function (settings, colorPaletteGenerator) {
        this.setFieldDropDown();
        $scope.flags.field = settings.selectedField;
        $scope.flags.minimum = settings.min;
        $scope.flags.maximum = settings.max;
        $scope.flags.division = settings.division;
        colorPaletteGenerator.setState(settings.colorPaletteState);
        $scope.flags.chosenPalette = colorPaletteGenerator.getChosenPalette();
    };

    this.getSettings = function (colorPaletteGenerator) {
        var settings = {
            isRange: 'true',
            min: $scope.flags.minimum,
            max: $scope.flags.maximum,
            selectedField: $scope.flags.field,
            colorPaletteState: colorPaletteGenerator.getState(),
            division: this.getDivisionCount(),
            selected: $scope.chosenValuesForGrid,
            unselected: this.getUnselectedItems()
        };
        return settings;
    };

    this.orderItems = function (tempList) {
        tempList.sort(this.itemComparer);
    };

    this.getCount = function (extractedItems, callBack) {
        $this.isDataLoading = true;
        $http({
            method: "POST",
            url: "/Classification/GetCountForRanges",
            data: { layerId: $scope.layerId, attributeId: $scope.flags.field, ranges: extractedItems }
        })
        .success(function (data, status, headers, config) {
            $this.setCheckedProperty(data);
            callBack(data);
            $this.isDataLoading = false;
        })
        .error(function () {
            $this.isDataLoading = false;
        });
    };

    this.setCheckedProperty = function (gridItems) {
        angular.forEach(gridItems, function (item) {
            item.checked = true;
        });
    };

    this.itemComparer = function (a, b) {
        return a.rangeMax > b.rangeMax;
    };

    this.getPropertyDataFromServer = function (callBack) {
        $this.isDataLoading = true;
        $http({
            method: "POST",
            url: "/Classification/GetRangeForField",
            data: { layerId: $scope.layerId, attributeId: $scope.flags.field }
        }).success(function (data, status, headers, config) {
            $scope.flags.minimum = data.minimum;
            $scope.flags.maximum = data.maximum;
            callBack();
            $this.isDataLoading = false;
        })
        .error(function () {
            $this.isDataLoading = false;
        });
    };



    this.prepareData = function (colorPaletteGenerator) {

        if (_.isNull($scope.flags.field) || !_.findWhere($scope.NeededAttributes, { id: $scope.flags.field }))
            return;
        if ($scope.flags.maximum === undefined) {
            this.getPropertyDataFromServer(function () {
                populatePropertyData(function () {
                    $this.setColorForGridData(colorPaletteGenerator);
                });
            });
        } else {
            populatePropertyData(function () {
                $this.setColorForGridData(colorPaletteGenerator);
            });
        }
    };

    function populatePropertyData(callback) {
        callback = callback || function () { };
        if ($scope.flags.division > 0) {
            var ranges = rangeFunctionalty.calculate($scope.flags.minimum, $scope.flags.maximum, $scope.flags.division);
            $this.getCount(ranges, function (data) {
                $scope.chosenValuesForGrid = data;
                callback();
            });
        }
    }
}
RangeType.prototype = new ClassType();
RangeType.prototype.constructor = RangeType;
