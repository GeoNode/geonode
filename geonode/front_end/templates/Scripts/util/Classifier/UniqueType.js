function UniqueType(http, scope, attributeTypes, filter) {
    var $this = this;
    var $http = http;
    var $scope = scope;
    ClassType.call(this, scope);

    this.isDataLoading = false;

    this.getDivisionCount = function () {
        return 5;
    };

    this.areEqual = function (a, b) {
        if (a.value == b.value)
            return true;
        return false;
    };

    this.setFieldDropDown = function () {
        $scope.NeededAttributes = $scope.Attributes;
    };

    this.setInitialSettings = function (settings, colorPaletteGenerator) {
        $scope.radioSelectionChanged();
        $scope.flags.field = settings.selectedField;
        $scope.dropdownSelectionChanged();
        colorPaletteGenerator.setState(settings.colorPaletteState);
        $scope.flags.chosenPalette = colorPaletteGenerator.getChosenPalette();
    };

    this.getSettings = function (colorPaletteGenerator) {
        var settings = {
            isRange: 'false',
            selectedField: $scope.flags.field,
            colorPaletteState: colorPaletteGenerator.getState(),
            division: this.getDivisionCount(),
            selected: $scope.chosenValuesForGrid,
            unselected: []
        };
        return settings;
    };

    this.addSelectionsToGrid = function (colorPaletteGenerator) {
        var extractedItems = this.getCheckedItems(filter);

        this.addToGridData(extractedItems);
        this.removeItemsFromPropertyData(extractedItems);
        this.setColorForGridData(colorPaletteGenerator);
    };

    this.removeItem = function (rowIndex, colorPaletteGenerator) {
        var extractedItems = $scope.chosenValuesForGrid.splice(rowIndex, 1);
        angular.forEach(extractedItems, function (item) {
            item.checked = false;
        });

        var unorderedItems = $scope.flags.PropertyData.concat(extractedItems);
        if (this.orderItems) {
            this.orderItems(unorderedItems);
        }
        $scope.flags.PropertyData = unorderedItems;
        this.setColorForGridData(colorPaletteGenerator);
    };

    this.setInitialUnselectedItems = function () {
        if (_.isNull($scope.flags.field))
            return;
        this.getPropertyDataFromServer();
    };

    this.getPropertyDataFromServer = function () {
        $this.isDataLoading = true;
        $http({
            method: "GET",
            url: "/layers/"+$scope.layerId+"/unique-value-for-attribute/"+$scope.flags.field+"/",
        })
        .success(function (data, status, headers, config) {

            data = filterDataIfDateType(data.values);
            $scope.originalData = data;
            $scope.flags.PropertyData = getUnSelectedItems();
            $this.isDataLoading = false;
        })
        .error(function () {
            $this.isDataLoading = false;
        });
    };

    function filterDataIfDateType(data) {
        if (attributeTypes.isDateType(_.findWhere(scope.Attributes, { id: scope.flags.field }).type)) {
            for (var i in data) {
                data[i].value = filter('date')(data[i].value, 'yyyy-MM-dd');
            }
        }
        return data;
    }

    function getUnSelectedItems() {
        var unselectedItems = [];
        angular.forEach($scope.originalData, function (item, index) {
            var foundItems = _.findWhere($scope.chosenValuesForGrid, { value: item.value });
            if (!foundItems) {
                unselectedItems.push(item);
            }
        });
        return unselectedItems;
    }

    this.prepareData = function () {
        if (_.isNull($scope.flags.field))
            return;
        if ($scope.originalData === undefined) {
            this.getPropertyDataFromServer(populatePropertyData);
        } else {
            populatePropertyData();
        }
    };

    function populatePropertyData() {
        $scope.flags.PropertyData = [].concat($scope.originalData);
    }
}
UniqueType.prototype = new ClassType();
UniqueType.prototype.constructor = UniqueType;
