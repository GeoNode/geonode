appModule.factory('subscriptionStatus', ['$http', 'urlResolver', 'surfToastr',
    function ($http, urlResolver, surfToastr) {

        var resourceUsage = {
            UploadBandwith: Number.MAX_VALUE,
            DownloadBandwith: Number.MAX_VALUE,
            DataStorage: Number.MAX_VALUE,
            ProjectsCount: Number.MAX_VALUE
        };

        var subscription = {
            MaxNumberOfProjects: -1,
            StorageLimitInBytes: -1,
            MonthlyBandwidthLimitInBytes: -1
        };

        var validators = {
            updateNumberOfProjects: function (projectsCount) {
                resourceUsage.ProjectsCount = parseInt(projectsCount);
            },
            decreaseNumberOfProjects: function () {
                resourceUsage.ProjectsCount--;
            },
            decreaseDataStorageUsage: function (dataSize) {
                resourceUsage.DataStorage -= dataSize;
            },
            increaseDataStorageUsage: function (dataSize) {
                resourceUsage.DataStorage += dataSize;
            },
            increaseDataStorageUsageForUpload: function (dataSize) {
                resourceUsage.DataStorage += dataSize;
                resourceUsage.UploadBandwith += dataSize;
            },
            validateAddProject: function () {
                var allow = resourceUsage.ProjectsCount < subscription.MaxNumberOfProjects;

                if (!allow) {
                    validators.showValidationFailMessage(appMessages.validation.maximumMapLimitReached);
                }
                return allow;
            },
            validateTotalStorageLimit: function (fileSize) {
                var allow = fileSize + resourceUsage.DataStorage <= subscription.StorageLimitInBytes;

                if (!allow) {
                    return appMessages.validation.maximumStorageLimitReached;
                }

                return false;
            },
            validateInBandwidthLimit: function (fileSize) {
                var allow = (fileSize + resourceUsage.UploadBandwith + resourceUsage.DownloadBandwith)
                    <= subscription.MonthlyBandwidthLimitInBytes;

                if (!allow) {
                    return appMessages.validation.maximumBandwidthLimitReached;
                }

                return false;
            },
            showValidationFailMessage: function (message) {
                surfToastr.error(message, appMessages.toastr.upgradeRequiredTitle());
            }
        };

        // (function getSubscriptionStatus() {
        //     $http.get(urlResolver.resolveUserProfile("GetResourceUsageInfo")).success(function (usageInfo) {
        //         resourceUsage = usageInfo || {};
        //     });

        //     $http.get(urlResolver.resolveUserProfile("GetSubscriptionInfo")).success(function (subscriptionInfo) {
        //         subscription = subscriptionInfo || {};
        //     });
        // })();

        return validators;
    }
]);
