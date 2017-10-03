angular.module('handsOnTableModule', []).directive('handsOnTable', [
        function () {
        	return {
        		scope: {
        			handsOnTable: '=',
        			config: '='
        		},
        		link: function (scope, elem, attrs, controller) {
        			var settings = angular.extend({
        				data: scope.handsOnTable
        			}, scope.config);
        			
        			var table = new Handsontable(elem[0], settings);
		            scope.config.table = table;
		        }
        	}
        }
]);
