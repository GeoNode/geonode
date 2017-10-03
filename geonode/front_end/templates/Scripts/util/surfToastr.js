angular.module('surfToastr', []).factory("surfToastr", [
    function () {
        toastr.options = {
            positionClass: "toast-bottom-right",
            closeButton: true,
            showMethod: 'slideDown',
            hideMethod: 'fadeOut',
            timeOut: 5000
        };
        function removeToasters() {
            $('#toast-container').remove();
        }
        return {
            success: function (message, title) {
                removeToasters();
                toastr.success(message, title);
            },

            error: function (message, title) {
                removeToasters();
                toastr.error(message, title);
            },

            warning: function (message, title) {
                removeToasters();
                toastr.warning(message, title);
            },

            info: function (message, title) {
                removeToasters();
                toastr.info(message, title);
            }
        }
    }
]);