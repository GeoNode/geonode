appHelperModule.factory('controlVisibleFactory', function() {
    return {
        isTextControlVisible: function(controlType) {
             if (controlType === "text" || controlType === undefined)
                return true;
            return false;
        },
        isDropdownControlVisible: function(controlType) {
            if (controlType === "dropdown")
                return true;
            return false;
        }

    };
});

appHelperModule.factory('queryOutputFactory', function() {
    return {

         htmlEntities:function(str) {
        return String(str).replace(/</g, '&lt;').replace(/>/g, '&gt;');
    },
        dropdownControlTypeName:'dropdown',
        textControlTypeName:'text',
        betweenConditionName:'BETWEEN',
        dropdownDataSourceType:'number',


        getDataForTextControl:function(rule){
        var data = rule.data;
            var condition = rule.condition;
            if(condition == '1' ){
                data =  "'"+rule.data+"'";
            }else if(condition == '3' || condition == '4'){
                data =  "'"+rule.data+"%'";
            }else if(condition == '5' ||condition == '6'){
                data =  "'%"+rule.data+"'";
            }else if(condition == '7' ||condition == '8' ||condition == '2'){
                data =  "'%"+rule.data+"%'";
            }else{
                data =  "'"+rule.data+"'";
            }
            return data;
        },

        getOutput: function(group) {


            if (!group) return "";
            for (var str = "", i = 0; i < group.rules.length; i++) {

                i > 0 && (str += group.operator +" ");


                var fieldName = group.rules[i].field.name;
                var condition = this.htmlEntities(group.rules[i].condition);

                var data = group.rules[i].data;  // for int value

                if (group.rules[i].field.controlType == this.textControlTypeName){ // for text value
                    data = "'"+group.rules[i].data+"'";
                    data = this.getDataForTextControl(group.rules[i]);
                    if(group.rules[i].condition =='1'){
                        condition = '=';
                    }else if(group.rules[i].condition =='2' ||group.rules[i].condition =='4' ||group.rules[i].condition =='6' ||group.rules[i].condition =='8' ){
                        condition = 'NOT LIKE';
                    }else{
                        condition = 'LIKE';
                    }

                }

                if (group.rules[i].field.controlType == this.dropdownControlTypeName){ // for drop down value
                    data = "'"+group.rules[i].firstDropdownValue+"'"; // consider , drop down value will be text type by default
                    if(group.rules[i].field.dropdownDataSourceType == this.dropdownDataSourceType){
                        data = group.rules[i].firstDropdownValue;
                    }
                }

              // for between condition -------------------------------------

                var secondValue = undefined;
                var isBetweenCondition = false;

                if(this.htmlEntities(group.rules[i].condition) == this.betweenConditionName){
                    isBetweenCondition = true;
                    secondValue = group.rules[i].dataAnother;
                    if (group.rules[i].field.controlType == this.dropdownControlTypeName){

                        secondValue = "'"+group.rules[i].secondDropdownValue+"'"; // this is for text

                        if(group.rules[i].field.dropdownDataSourceType == this.dropdownDataSourceType){
                            secondValue = group.rules[i].secondDropdownValue;
                        }
                    }
                }

                var betweenConditionValue = '';
                if (isBetweenCondition){

                    betweenConditionValue = ' AND '+secondValue;

                }
                // for between condition -------------------------------------
                str += group.rules[i].group ? computed(group.rules[i].group) :   fieldName + " " + condition + " " + data +" "+betweenConditionValue;


            }

            return str ;
        }
    };
});

appHelperModule.directive('queryBuilder', ['$compile','controlVisibleFactory','LayerService',
 function ($compile,controlVisibleFactory,LayerService) {
    return {
        restrict: 'E',
        scope:{
            layerId: '=',
            group : '='
        },
        templateUrl: 'static/Scripts/Directives/QueryBuilder/query_builder_view.html',
        compile: function (element, attrs) {
            var content, directive;

            var betweenOperator = "BETWEEN" ;

            content = element.contents().remove();
            return function (scope, element, attrs) {

                 scope.conditionDictionary ={
                    undefined:[
                        { name: '<>',value:'<>' },
                        { name: '<',value: '<'  },
                        { name: '=',value: '=' },
                        { name: '<=' ,value:'<='},
                        { name: '>' ,value:'>'},
                        { name: '>=',value:'>=' },
                        { name: betweenOperator , value: 'BETWEEN'}
                    ],
                     text:[
                         {name:'Equals', value:'1'},
                         {name:'Does not equal', value:'2'},
                         {name:'Starts with', value:'3'},
                         {name:'Does not start with', value:'4'},
                         {name:'Ends with', value:'5'},
                         {name:'Does not end with', value:'6'},
                         {name:'Contains', value:'7'},
                         {name:'Does not contain', value:'8'}
                     ]
                };
                // scope.group={"a": "AND","rules": []};
                scope.options  = {
                    addGroup:false,
                    removeGroup:false,
                    customFields:[],
                };
                function generateOptions(featureTypesArray){
                   angular.forEach(featureTypesArray.properties,function(featureType){
                        if(featureType.type=='xsd:int'){
                            scope.options.customFields.push({name:featureType.name});
                        }else{
                            scope.options.customFields.push({name:featureType.name,controlType:"text"});
                        }
                   });
                }


                scope.$watch('layerId',function(newValue,oldValue){
                    if(newValue){
                        newValue=newValue.split(":")[1];
                        if(newValue){
                            LayerService.getLayerFeatureByName('http://172.16.0.247:8080/geoserver/',newValue).then(function(response){
                                if(response.featureTypes){
                                    if(response.featureTypes[0]){
                                        generateOptions(response.featureTypes[0]);
                                    }
                                }
                            });
                        }
                    }
                });

                scope.operators = [
                    { name: 'AND' },
                    { name: 'OR' }
                ];

                scope.operators = scope.options.customOperators ===undefined ? scope.operators:scope.options.customOperators;

                scope.fields = [
                    { name: 'Firstname' },
                    { name: 'Lastname' },
                    { name: 'Birthdate' },
                    { name: 'City' },
                    { name: 'Country' }
                ];

                scope.fields = scope.options.customFields ===undefined ? scope.fields:scope.options.customFields;

                scope.conditions = [
                    { name: '=' },
                    { name: '<>' },
                    { name: '<' },
                    { name: '<=' },
                    { name: '>' },
                    { name: '>=' },
                    { name: betweenOperator }
                ];

                scope.conditions = scope.options.customConditions ===undefined ? scope.conditions:scope.options.customConditions;

                scope.addCondition = function () {
                    scope.group.rules.push({
                        condition: '=',
                        field: '',
                        data: '',
                        dataAnother:''
                    });
                };

                scope.removeCondition = function (index) {
                    scope.group.rules.splice(index, 1);
                };

                scope.addGroup = function () {
                    scope.group.rules.push({
                        group: {
                            operator: 'AND',
                            rules: []
                        }
                    });
                };

                scope.removeGroup = function () {
                    "group" in scope.$parent && scope.$parent.group.rules.splice(scope.$parent.$index, 1);
                };

                scope.IsSecondInputBoxVisible = function (rule) {
                  return rule.condition ==betweenOperator && controlVisibleFactory.isTextControlVisible(rule.field.controlType);
                };
                scope.IsSecondDropdownBoxVisible = function (rule) {
                  return rule.condition ==betweenOperator && controlVisibleFactory.isDropdownControlVisible(rule.field.controlType);
                };

                scope.dropdownControlVisible = function (rule) {
                   return controlVisibleFactory.isDropdownControlVisible(rule.field.controlType);
                };
                scope.textControlVisible = function (rule) {
                   return controlVisibleFactory.isTextControlVisible(rule.field.controlType);
                };

                scope.attributeChange = function(rule){
                    var controlType = rule.field.controlType;
                    if(controlType == undefined){
                        scope.conditions = scope.conditionDictionary['undefined'];
                    }else{
                        scope.conditions = scope.conditionDictionary[controlType];
                    }
                };

                directive || (directive = $compile(content));

                element.append(directive(scope, function ($compile) {
                    return $compile;
                }));
            }
        }
    }
}]);
