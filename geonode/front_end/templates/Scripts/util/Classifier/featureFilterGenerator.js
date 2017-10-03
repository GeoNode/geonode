appModule.factory('featureFilterGenerator', ['attributeTypes', 'cqlFilterCharacterFormater',
    function (attributeTypes, cqlFilterCharacterFormater) {

        function getFilterStringForClassification(surfLayer) {
            if (!surfLayer.getClassifierDefinitions().selected
                || surfLayer.getClassifierDefinitions().selected.length == 0) return null;

            if (surfLayer.getClassifierDefinitions().selected[0].rangeMin
                || surfLayer.getClassifierDefinitions().selected[0].rangeMin == 0) {
                return getRangeFilterStringForClassification(surfLayer);
            } else {
                return getUniqueValueFilterStringForClassification(surfLayer);
            }
        }

        function getTypeOfAttribute(surfLayer, attributeId) {
            var attrDefinition = surfLayer.getAttributeDefinition();
            return _.findWhere(attrDefinition, { Id: attributeId });
        }

        function isAttributeTypeNumeric(surfLayer, attributeId) {
            var item = getTypeOfAttribute(surfLayer, attributeId);
            return attributeTypes.isNumericType(item.Type);
        }

        function isAttributeTypeDate(surfLayer, attributeId) {
            var item = getTypeOfAttribute(surfLayer, attributeId);
            return attributeTypes.isDateType(item.Type);
        }

        function getUniqueValueFilterStringForClassification(surfLayer) {
            var attributeName = surfLayer.getClassifierDefinitions().selectedField;
            var isNumeric = isAttributeTypeNumeric(surfLayer, attributeName);
            var isDate = isAttributeTypeDate(surfLayer, attributeName);

            var filterString = "";
            var classification = surfLayer.getClassifierDefinitions().selected;

            for (var i in classification) {
                if (!surfLayer.isClassVisible(classification[i])) {
                    var currentFilterString = "";
                    if (classification[i].value == null) {
                        currentFilterString += attributeName + " IS NOT NULL";
                    } else {
                        if (isDate) {
                            currentFilterString += attributeName + " NOT BETWEEN " + cqlFilterCharacterFormater.formatSpecialCharacters(classification[i].value) + " AND " + cqlFilterCharacterFormater.formatSpecialCharacters(classification[i].value);
                        }
                        else if (isNumeric) {
                            currentFilterString += "NOT " + attributeName + " = " + cqlFilterCharacterFormater.formatSpecialCharacters(classification[i].value);
                        } else {
                            currentFilterString += attributeName + " NOT LIKE '" + cqlFilterCharacterFormater.formatSpecialCharacters(classification[i].value) + "'";
                        }
                    }

                    if (filterString) {
                        currentFilterString = " AND " + currentFilterString;
                    }
                    filterString += currentFilterString;
                }
            }
            return filterString;
        }

        function getRangeFilterStringForClassification(surfLayer) {
            var filterString = "";
            var attributeName = surfLayer.getClassifierDefinitions().selectedField;
            var classification = surfLayer.getClassifierDefinitions().selected;

            for (var i in classification) {
                if (!surfLayer.isClassVisible(classification[i])) {
                    var currentFilterString;
                    if (i == 0) {
                        currentFilterString = attributeName + " < " + classification[i].rangeMin + " OR " + attributeName + " > " + classification[i].rangeMax;
                    } else {
                        currentFilterString = attributeName + " <= " + classification[i].rangeMin + " OR " + attributeName + " > " + classification[i].rangeMax;
                    }
                    if (filterString) {
                        currentFilterString = " AND " + currentFilterString;
                    }
                    filterString += currentFilterString;
                }
            }
            return filterString;
        }

        function getCqlQueryForLayer(surfLayer) {
            var queryFields = surfLayer.getQueries();
            var queryString = "";

            for (var i in queryFields) {
                var currentQueryString;
                var attributeName = queryFields[i].attributeName;
                var attributeType = queryFields[i].type;
                if (queryFields[i].value) {
                    currentQueryString = getLayerQueryForUniqueType(attributeName, attributeType, queryFields[i].value);
                } else {
                    currentQueryString = getLayerQueryForRangeType(attributeName, attributeType, queryFields[i].rangeMin, queryFields[i].rangeMax);
                }
                if (queryString) {
                    queryString += " OR " + currentQueryString;
                } else {
                    queryString = currentQueryString;
                }
            }
            return queryString;
        }

        function getLayerQueryForUniqueType(attributeName, type, value) {
            var queryString="";
            if (value == null) {
                queryString += attributeName + " IS NULL";
            } else {
                if (type == 'date') {
                    queryString += attributeName + " BETWEEN " + cqlFilterCharacterFormater.formatSpecialCharacters(value) + " AND " + cqlFilterCharacterFormater.formatSpecialCharacters(value);
                }
                else if (type == 'number') {
                    queryString += attributeName + " = " + cqlFilterCharacterFormater.formatSpecialCharacters(value);
                } else {
                    queryString += attributeName + " LIKE '" + cqlFilterCharacterFormater.formatSpecialCharacters(value) + "'";
                }
            }
            return queryString;
        }

        function getLayerQueryForRangeType(attributeName, rangeMin, rangeMax) {
            return attributeName + " >= " + rangeMin + " AND " + attributeName + " <= " + rangeMax;
        }
        
        return {
            getFilter: function (surfLayer) {
                var classificationFilter = getFilterStringForClassification(surfLayer);
                var layerQueryCqlFilter = getCqlQueryForLayer(surfLayer);
                var filterString;
                if (classificationFilter && layerQueryCqlFilter) {
                    filterString = "(" + classificationFilter + ") AND (" + layerQueryCqlFilter + ")";
                } else {
                    filterString = classificationFilter || layerQueryCqlFilter;
                }
                return { cql_filter: filterString ? filterString : null };
            }
        }
    }
]);
