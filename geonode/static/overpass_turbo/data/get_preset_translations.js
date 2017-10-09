/* Downloads preset translations from iD editor github repo */

var request = require('request'),
    fs = require('fs');

var api = 'https://github.com/openstreetmap/iD/raw/master/dist/locales/';
var outdir = './data/';
//var localesdir = './locales/';
var localesdir = STATIC_FOLDER_URL+'locales/';


var locales = fs.readdirSync(localesdir).filter(function(filename) { return filename.match(/\.json$/); });

locales.forEach(function(locale) {
    locale = locale.replace('.json', '');
    request(api + locale + '.json', function(err, resp, body) {
        console.log(locale);
        if (err) return;
        try { var data = JSON.parse(body); } catch (e) { return; }
        data = data.presets.presets;
        fs.writeFileSync(outdir + 'iD_presets_' + locale + '.json', JSON.stringify(data, null, 2));
    });
});

