var expect = require('expect');
var FeatureInfoUtils = require('../FeatureInfoUtils');

describe('FeatureInfoUtils', () => {
    // **********************************
    // HTML
    // **********************************
    const styleSample = '<style type="text/css">.sample {border:1px solid #ddd;}</style>';
    const bodySample = '<div class="sample">TEST text</div>';
    const rowHTML = '<html>'
        + '<head>'
        + '<title>Geoserver GetFeatureInfo output</title>'
        + styleSample
        + '</head>'
        + '<body>'
        + bodySample
        + '</body>'
        + '</html>';

    const bodyWithStyle = styleSample + bodySample;
    const emptyHTML = '<html>'
        + '<head>'
        + '<title>Geoserver GetFeatureInfo output</title>'
        + styleSample
        + '</head>'
        + '<body>'
        + '</body>'
        + '</html>';
    it('HTML Parser', () => {
        var parsedBody = FeatureInfoUtils.Parser.HTML.getBody(rowHTML);
        var parsedStyle = FeatureInfoUtils.Parser.HTML.getStyle(rowHTML);
        var parsedHTML = FeatureInfoUtils.Parser.HTML.getBodyWithStyle(rowHTML);
        expect(parsedBody).toBe(bodySample);
        expect(parsedStyle).toBe(styleSample);
        expect(parsedHTML).toBe(bodyWithStyle);

    });
    it('HTML Validator', () => {
        let results = FeatureInfoUtils.Validator.HTML.getValidResponses([{response: emptyHTML}, {response: rowHTML}]);
        expect(results.length).toBe(1);
        expect(results[0].response).toBe(rowHTML);

        let notValidResults = FeatureInfoUtils.Validator.HTML.getNoValidResponses([{response: emptyHTML}, {response: rowHTML}]);
        expect(notValidResults.length).toBe(1);
        expect(notValidResults[0].response).toBe(emptyHTML);

        // test regex
        let validRegex = "<div[^>]*>[\\s\\S]*<\\/div>";
        let invalidRegex = "<table[^>]*>[\\s\\S]*<\\/table>";

        let validRegexResults = FeatureInfoUtils.Validator.HTML.getValidResponses([{response: emptyHTML}, {response: rowHTML, layerMetadata: {regex: validRegex }}]);
        expect(validRegexResults.length).toBe(1);
        expect(validRegexResults[0].response).toBe(rowHTML);

        let invalidRegexResults = FeatureInfoUtils.Validator.HTML.getValidResponses([{response: emptyHTML}, {response: rowHTML, layerMetadata: {regex: invalidRegex }}]);
        expect(invalidRegexResults.length).toBe(0);

        validRegexResults = FeatureInfoUtils.Validator.HTML.getNoValidResponses([{response: emptyHTML}, {response: rowHTML, layerMetadata: {regex: validRegex }}]);
        expect(validRegexResults.length).toBe(1); // only the empty is not valid

        invalidRegexResults = FeatureInfoUtils.Validator.HTML.getNoValidResponses([{response: emptyHTML}, {response: rowHTML, layerMetadata: {regex: invalidRegex }}]);
        expect(invalidRegexResults.length).toBe(2); // both are not valid


    });

    // **********************************
    // TEXT
    // **********************************
    const baseTextGFI = 'GetFeatureInfo results:\n';
    const notValid = '';
    const validTEXT = baseTextGFI
        + '\n'
        + "Layer 'LimiteRegionale''\n"
        + "Feature 0:'\n"
        + "uuid = 'fc1132ee-cf89-4fb0-a25d-315bb3c34568''\n";

    it('TEXT Validator', () => {
        let results = FeatureInfoUtils.Validator.TEXT.getValidResponses([{response: notValid}, {response: validTEXT}]);
        expect(results.length).toBe(1);
        expect(results[0].response).toBe(validTEXT);

        let notValidResults = FeatureInfoUtils.Validator.TEXT.getNoValidResponses([{response: notValid}, {response: validTEXT}]);
        expect(notValidResults.length).toBe(1);
        expect(notValidResults[0].response).toBe(notValid);
    });

    // **********************************
    // JSON
    // **********************************
    const validJSON = {"type": "FeatureCollection", "totalFeatures": "unknown", "features": [{"type": "Feature", "id": "", "geometry": null, "properties": {"precip30min": 816}}], "crs": null};
    const emptyJSON = {"type": "FeatureCollection", "totalFeatures": "unknown", "features": [], "crs": null};
    it('JSON Validator', () => {
        let results = FeatureInfoUtils.Validator.JSON.getValidResponses([{response: validJSON}, {response: emptyJSON}]);
        expect(results.length).toBe(1);
        expect(results[0].response).toBe(validJSON);

        let notValidResults = FeatureInfoUtils.Validator.JSON.getNoValidResponses([{response: validJSON}, {response: emptyJSON}]);
        expect(notValidResults.length).toBe(1);
        expect(notValidResults[0].response).toBe(emptyJSON);
    });

});
