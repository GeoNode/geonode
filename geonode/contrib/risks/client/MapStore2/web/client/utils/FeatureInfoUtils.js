
const INFO_FORMATS = {
    "TEXT": "text/plain",
    "HTML": "text/html",
    "JSONP": "text/javascript",
    "JSON": "application/json",
    "GML2": "application/vnd.ogc.gml",
    "GML3": "application/vnd.ogc.gml/3.1.1"
};

const INFO_FORMATS_BY_MIME_TYPE = {
    "text/plain": "TEXT",
    "text/html": "HTML",
    "text/javascript": "JSONP",
    "application/json": "JSON",
    "application/vnd.ogc.gml": "GML2",
    "application/vnd.ogc.gml/3.1.1": "GML3"
};

const regexpXML = /^[\s\S]*<gml:featureMembers[^>]*>([\s\S]*)<\/gml:featureMembers>[\s\S]*$/i;

const regexpBody = /^[\s\S]*<body[^>]*>([\s\S]*)<\/body>[\s\S]*$/i;
const regexpStyle = /(<style[\s\=\w\/\"]*>[^<]*<\/style>)/i;

function parseHTMLResponse(res) {
    if ( typeof res.response === "string" && res.response.indexOf("<?xml") !== 0 ) {
        let match = res.response.match(regexpBody);
        if ( res.layerMetadata && res.layerMetadata.regex ) {
            return match && match[1] && match[1].match(res.layerMetadata.regex);
        }
        return match && match[1] && match[1].trim().length > 0;
    }
    return false;
}

function parseXMLResponse(res) {
    if ( typeof res.response === "string" && res.response.indexOf("<?xml") !== -1 ) {
        let match = res.response.match(regexpXML);
        return match && match[1] && match[1].trim().length > 0;
    }
    return false;
}

const Validator = {
    HTML: {
        /**
         *Parse the HTML to get only the valid html responses
         */
        getValidResponses(responses) {
            return responses.filter(parseHTMLResponse);
        },
        /**
         * Parse the HTML to get only the NOT valid html responses
         */
        getNoValidResponses(responses) {
            return responses.filter((res) => {return !parseHTMLResponse(res); });
        }
    },
    TEXT: {
        /**
         *Parse the TEXT to get only the valid text responses
         */
        getValidResponses(responses) {
            return responses.filter((res) => res.response !== "" && (typeof res.response === "string" && res.response.indexOf("no features were found") !== 0) && (typeof res.response === "string" && res.response.indexOf("<?xml") !== 0));
        },
        /**
         * Parse the TEXT to get only the NOT valid text responses
         */
        getNoValidResponses(responses) {
            return responses.filter((res) => res.response === "" || (typeof res.response === "string" && res.response.indexOf("no features were found") === 0) || res.response && (typeof res.response === "string" && res.response.indexOf("<?xml") === 0));
        }
    },
    JSON: {
        /**
         *Parse the JSON to get only the valid json responses
         */
        getValidResponses(responses) {
            return responses.filter((res) => res.response && res.response.features && res.response.features.length);
        },
        /**
         * Parse the JSON to get only the NOT valid json responses
         */
        getNoValidResponses(responses) {
            return responses.filter((res) => res.response && res.response.features && res.response.features.length === 0);
        }
    },
    GML3: {
        /**
         *Parse the HTML to get only the valid html responses
         */
        getValidResponses(responses) {
            return responses.filter(parseXMLResponse);
        },
        /**
         * Parse the HTML to get only the NOT valid html responses
         */
        getNoValidResponses(responses) {
            return responses.filter((res) => {return !parseXMLResponse(res); });
        }
    }
};
const Parser = {
    HTML: {
        getBody(html) {
            return html.replace(regexpBody, '$1').trim();
        },
        getStyle(html) {
            // gets css rules from the response and removes which are related to body tag.
            let styleMatch = regexpStyle.exec(html);
            let style = styleMatch && styleMatch.length === 2 ? regexpStyle.exec(html)[1] : "";
            style = style.replace(/body[,]+/g, '');
            return style;
        },
        getBodyWithStyle(html) {
            return Parser.HTML.getStyle(html) + Parser.HTML.getBody(html);
        }
    }
};

module.exports = {
    INFO_FORMATS,
    INFO_FORMATS_BY_MIME_TYPE,
    Validator,
    Parser,
    parseXMLResponse,
    parseHTMLResponse};
