/* Downloads the latest translations from Transifex */

var request = require('request'),
    fs = require('fs');

var api = 'http://www.transifex.com/api/2/';
var project = api + 'project/overpass-turbo/';
var resource = ['main'];
var outdir = STATIC_FOLDER_URL+'locales/';

/*
 * Transifex oddly doesn't allow anonymous downloading
 *
 * auth is stored in transifex.auth in a json object:
 *  {
 *      "user": "username",
 *      "pass": "password"
 *  }
 */

var auth = JSON.parse(fs.readFileSync('./transifex.auth', 'utf8'));

asyncMap(resource, getResource, function(err, locales) {
    if (err) return console.log(err);

    locale = locales[0]; // only 1 resource -> no merging required

    for (var i in locale) {
        if (i === 'en') continue;
        fs.writeFileSync(outdir + i + '.json', JSON.stringify(locale[i], null, 2));
    }
});

function getResource(resource, callback) {
    resource = project + 'resource/' + resource + '/';
    getLanguages(resource, function(err, codes) {
        if (err) return callback(err);

        asyncMap(codes, getLanguage(resource), function(err, results) {
            if (err) return callback(err);

            var locale = {};
            results.forEach(function(result, i) {
                locale[codes[i]] = result;
            });

            callback(null, locale);
        });
    });
}

function getLanguage(resource) {
    return function(code, callback) {
        code = code.replace(/-/g, '_');
        var url = resource + 'translation/' + code;
        request.get(url, { auth : auth },
            function(err, resp, body) {
            if (err) return callback(err);
            callback(null, JSON.parse(JSON.parse(body).content));
        });
    };
}

function getLanguages(resource, callback) {
    request.get(resource + '?details', { auth: auth },
        function(err, resp, body) {
        if (err) return callback(err);
        callback(null, JSON.parse(body).available_languages.map(function(d) {
            return d.code.replace(/_/g, '-');
        }).filter(function(d) {
            return d !== 'en';
        }));
    });
}

function asyncMap(inputs, func, callback) {
    var remaining = inputs.length,
        results = [],
        error;

    inputs.forEach(function(d, i) {
        func(d, function done(err, data) {
            if (err) error = err;
            results[i] = data;
            remaining --;
            if (!remaining) callback(error, results);
        });
    });
}