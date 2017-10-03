appModule.factory('csvHeaderMappingService', [
    function () {
        var validationMessages = ['Name can have a maximum of 10 characters.',
        "Name may not start with a digit and can be named using letters, numbers, and underscores.",
        "Names must be unique."];
        return {
            getValidName: function (name) {
                name = name.replace(/^[0-9]+/, "");
                name = name.replace(/[^a-zA-Z0-9_]+/g, "_");
                return name.substr(0, 10);
            },
            getUniqueNameValidationMessage: function (headers) {
                var temp = {};
                for (var i in headers) {
                    temp[headers[i].mappedName] = true;
                }
                if (Object.keys(temp).length != headers.length) {
                    return validationMessages[2];
                }
                return "";
            },
            getValidationMessage: function (name) {
                if (name.length > 10) {
                    return validationMessages[0];
                } else if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) {
                    return validationMessages[1];
                }
                return "";
            }
        };
    }
]);
