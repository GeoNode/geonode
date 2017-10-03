appHelperModule.factory('attributeValidator', [function () {

    function setValueOnValidation(isValid, valueObject, propertyKey, itemBeforeChange) {
        if (isValid) {
            itemBeforeChange[propertyKey] = valueObject[propertyKey];
        } else {
            valueObject[propertyKey] = itemBeforeChange[propertyKey];
        }
    }

    function isTextLengthValid(text, length) {
        return (text || '').length <= length;
    }

    function isNumberWithinRange(number, precision, scale) {
        if (!number || number.length == 0) return true;
        var absValue = number[0] == '-' ? number.substring(1) : number;

        var isValid;
        if (number.length == 0 || number == '-' || number == '.') {
            isValid = true;
        } else if (isNaN(absValue)) {
            isValid = false;
        } else {
            var parts = number.split('.');
            isValid = parts[0].length <= (precision - scale);

            if (isValid && parts.length == 2) {
                isValid = parts[1].length <= scale;
            }
        }
        return isValid;
    }

    return {
        validateText: function (valueObject, itemBeforeChange, propertyKey, length) {
            var isValid = isTextLengthValid(valueObject[propertyKey], length);
            setValueOnValidation(isValid, valueObject, propertyKey, itemBeforeChange);

            return isValid;
        },
        validateNumber: function (valueObject, itemBeforeChange, propertyKey, precision, scale) {
            var value = valueObject[propertyKey];

            var isValid = isNumberWithinRange(value, precision, scale);

            setValueOnValidation(isValid, valueObject, propertyKey, itemBeforeChange);

            return isValid;
        },
        isTextLengthValid: isTextLengthValid,
        isNumberWithinRange: isNumberWithinRange
    }
}]);