angular.module('truncateModule', []).filter('truncate', function () {
    function countSmallLetters(string) {
        var smallLetters = string.match(/([a-z])/g) || [];
        return smallLetters.length;
    }
    function getActualReturnTextLength(text, length) {
        var smallLettersCount = countSmallLetters(text.substr(0, length - 1));
        var otherCounts = length - smallLettersCount;
        var lengthToBeSubtracted = Math.ceil(otherCounts * 0.2);
        return length - lengthToBeSubtracted;
    }

    return function (text, length, dotPosition) {
        text = text + "";
        var textLengthToBeShown = getActualReturnTextLength(text, length);

        if (text.length > textLengthToBeShown) {
            var leadingPart, trailingPart;
            if (dotPosition || dotPosition === 0) {
                leadingPart = text.substring(0, dotPosition);
                trailingPart = text.substring(text.length - (textLengthToBeShown - dotPosition));
            } else {
                var lengthOfEachPart = Math.floor((textLengthToBeShown - 3) / 2);
                leadingPart = text.substring(0, lengthOfEachPart);
                trailingPart = text.substring(text.length - lengthOfEachPart - 1, text.length);
            }
            
            return leadingPart + "..." + trailingPart;
        }
        return text;
    }
});
