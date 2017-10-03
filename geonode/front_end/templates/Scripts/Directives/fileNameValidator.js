appHelperModule.directive('validatefilename', ['surfToastr',
    function (surfToastr) {
        return {
            require: '?ngModel',
            link: function(scope, elem, attrs, ngModelController) {
                if (!attrs.ngModel) {
                    var oldValue = elem.val();
                    elem.on('keyup', function(e) {
                        if (isInvalidCharacter(elem.val())) {
                            elem.val(oldValue);
                        }
                        oldValue = elem.val();
                    });
                    return;
                }
                scope.$watch(attrs.ngModel, function(newVal, oldVal) {
                    if (!newVal) return;
                    if (isInvalidCharacter(newVal)) {
                        ngModelController.$setViewValue(oldVal);
                        ngModelController.$render();
                    }
                }, true);

                function isInvalidCharacter(fileName) {
                    if (fileName[0] == ".") {
                        surfToastr.error(appMessages.toastr.invalidStartCharacter(), appMessages.toastr.invalidCharacterTitle());
                        return true;
                    }
                    var length = fileName.length;
                    for (var i = 0; i < length; i++) {
                        var c = fileName[i];
                        if (c == '/' || c == '\\' || c == '<' || c == '>' || c == ':' || c == '?' || c == '*' || c == '"' || c == '|') {
                            surfToastr.error(appMessages.toastr.invalidFileNameCharacter(c), appMessages.toastr.invalidCharacterTitle());
                            return true;
                        }
                    }
                    return false;
                }
            }
        };
    }
]);