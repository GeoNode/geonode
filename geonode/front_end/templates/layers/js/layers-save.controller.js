(function() {
    'use strict';

    appModule.controller('LayerSaveController', LayerSaveController);

    LayerSaveController.$inject = ['layerService', '$modalInstance', 'surfToastr', 'projectService'];

    function LayerSaveController(layerService, $modalInstance, surfToastr, projectService) {
        var self = this;
        
        self.title = 'untitled';
        self.organizationId = null;
        self.categoryId = null;

        self.UserOrganizationList = [];
        self.CategoryList = [];


        self.save = function() {
            $modalInstance.close({
               layer_title: self.title,
               category: self.categoryId,
               organization: self.organizationId
            });
        };

        function errorFn() {

        }
        //load User Profile
        function getUserProfile() {
            projectService.getUserProfile()
                .then(function(res) {
                    getUserOrganizationList(res.data.id);
                }, errorFn);
        }
        // Load organization list
        function getUserOrganizationList(userId) {
            projectService.getUserOrganizationList(userId)
                .then(function(res) {
                    self.UserOrganizationList = res.data.objects;
                }, errorFn);
        }

        // Load Category List
        function getCategoryList() {
            projectService.getCategoryList()
                .then(function(res) {
                    self.CategoryList = res.data.objects;

                }, errorFn);
        }

        self.init = function (){
            getUserProfile();
            getCategoryList();
        };

        self.closeDialog = function() {
            $modalInstance.dismiss();
        };
    }
})();