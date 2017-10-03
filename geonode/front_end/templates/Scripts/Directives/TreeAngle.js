var treeModule = angular.module('tree', ['ui.sortable']);

treeModule.directive('treeAngle', [
    function () {
        return {
            transclude: false,
            replace: true,
            restrict: "AC",
            templateUrl: '/static/Templates/tree.html',
            controller: ['$scope', '$rootScope', function ($scope, $rootScope) {
                $scope.rootNode = { isExpanded: true };

                jantrik.EventPool.register('layerStateChanged', function () {
                    $scope.$evalAsync();
                });

                $scope.stopPropagation = function (event) {
                    event.stopPropagation();
                };
    
                $scope.initializeGroups = function (layer) {
                    layer.groups = [];
                    layer.ungrouped = [];
                    updateGroups(layer);
                }

                function updateGroups(layer) {
                    layer.groups.length = 0;
                    layer.ungrouped.length = 0;

                    var classes = layer.getClassifierDefinitions().selected;

                    var groupedClasses = getGroupedClasses(classes);
                    for (var index in groupedClasses.grouped) {
                        layer.groups.push(groupedClasses.grouped[index]);
                    }
                    for (var i in groupedClasses.ungrouped) {
                        layer.ungrouped.push(groupedClasses.ungrouped[i]);
                    }
                }

                $rootScope.$on('classificationChanged', function (event, args) {
                    updateGroups(args.layer);
                });

                function getGroupedClasses(classes) {
                    var ungrouped = [];
                    var groups = {};

                    for (var index in classes) {
                        var groupName = classes[index].groupName;
                        if (groupName) {
                            if (groups[groupName]) {
                                groups[groupName].classes.push(classes[index]);
                            } else {
                                groups[groupName] = { name: groupName, classes: [classes[index]] };
                            }
                        } else {
                            ungrouped.push(classes[index]);
                        }
                    }

                    checkGroups(groups);

                    return { grouped: groups, ungrouped: ungrouped };
                }

                function checkGroups(groups) {

                    for (var index in groups) {
                        for (var subIndex in groups[index].classes) {
                            groups[index].isChecked = groups[index].classes[subIndex].checked;
                        }
                    }
                }
            }]
        };
    }]);
