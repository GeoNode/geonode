var repositoryModule = angular.module('repositoryModule', []).config([
    '$httpProvider',
    function ($httpProvider) {
        //$httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

        $httpProvider.interceptors.push('httpInterceptor');

        if (!window.debug) {
            window.onerror = function (msg, url, line, col, error) {
                errorMessageManager.showUnexpectedErrorMessage();
                return true;
            };
        }
    }
]).factory('httpInterceptor', ['$q', function ($q) {
    return function (promise) {
        return promise.then(function (response) {
            if (response.data.isError) {
                errorMessageManager.showUnexpectedErrorMessage();
                return $q.reject(response);
            } else {
                return response;
            }
        });
    };
}]);

// This is here because dirty state is related 
// to synchronization between server and client
repositoryModule.factory('dirtyManager', [
    function () {
        var _dirty = false;

        return {
            isDirty: function () {
                return _dirty;
            },
            setDirty: function (dirty) {
                _dirty = dirty;
            }
        };
    }
]);