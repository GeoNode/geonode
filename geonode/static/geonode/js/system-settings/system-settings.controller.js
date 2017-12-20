(function () {
    angular
        .module('SystemSettingsApp')
        .controller('SystemSettingsController', SystemSettingsController);

    SystemSettingsController.$inject = ['$scope', 'SettingsService'];

    function SystemSettingsController($scope, SettingsService) {
        //$scope.layerName = 'Layer Name!';

        var systemSettings = SettingsService.getSystemSettings();

        //console.log(systemSettings);


        systemSettings.then(function (value) {

            console.log(value);
            $.each(value, function (index, element) {

                if (element.settings_code == "location") {
                    $scope.layerName = element.value
                }
            });

            }, function (error) {
                // This is called when error occurs.
            }
        );

        var layerSettings = SettingsService.getLayers();


        var layersObject;

        layerSettings.then(function (value) {

                layersObject = value.objects;
                $.each(layersObject, function (index, element) {
                    var title = element.title;
                    if (element.title.length > 22) {
                        title = element.title.substring(0, 25) + "...";
                    }
                    $("#layer").append("<option value='" + element.uuid + "'>" + title + "</option>");
                    //console.log(element.id +" "+element.title);
                });

            }, function (error) {
                // This is called when error occurs.
            }
        );
        //debugger;
        //Promise.reso
        //console.log(layersObject);
        //console.log(typeof layerSettings);

    }
})();
