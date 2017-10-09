# this builds overpass turbo
# supported commands:
#   * all
#   * install
#   * clean
#   * test - runs the test suite
#   * translations - updates translations from Transifex
#   * presets - grabs presets and their translations from the iD-Project
#   * ffs - compiles the ffs/wizard parser
#   * icons - update icon sets))
# usage:
#   make && make install install_root=...
# set install_root for installing into a specific directory

UGLIFY = ./node_modules/uglify-js/bin/uglifyjs
JS_BEAUTIFIER = $(UGLIFY) -b -i 2 -nm -ns
JS_COMPILER = $(UGLIFY)
CSSO = ./node_modules/csso/bin/csso
CSS_COMPILER = $(CSSO)
PEGJS = ./node_modules/pegjs/bin/pegjs
install_root ?= build

all: \
	turbo.js \
	turbo.min.js \
	turbo.css \
	turbo.min.css \
	turbo.map.js \
	turbo.map.min.js

turbo.js: \
	libs/jquery/jquery-1.11.1.js \
	libs/lodash/lodash-2.4.1.js \
	libs/leaflet/leaflet-src.js \
	libs/polylineOffset/leaflet.polylineoffset.js \
	libs/jqueryui/jquery-ui.js \
	libs/CodeMirror/lib/codemirror.js \
	libs/CodeMirror/mode/javascript/javascript.js \
	libs/CodeMirror/mode/xml/xml.js \
	libs/CodeMirror/mode/clike/clike.js \
	libs/CodeMirror/mode/css/css.js \
	libs/CodeMirror/lib/util/multiplex.js \
	libs/CodeMirror/lib/util/closetag.js \
	libs/locationfilter/src/locationfilter.js \
	libs/mapbbcode/PopupIcon.js \
	js/jsmapcss/styleparser.js \
	js/jsmapcss/Condition.js \
	js/jsmapcss/Rule.js \
	js/jsmapcss/RuleChain.js \
	js/jsmapcss/Style.js \
	js/jsmapcss/StyleChooser.js \
	js/jsmapcss/StyleList.js \
	js/jsmapcss/RuleSet.js \
	libs/misc.js \
	libs/momentjs/moment-with-locales.min.js \
	libs/osmtogeojson/osmtogeojson.js \
	js/GeoJsonNoVanish.js \
	js/OSM4Leaflet.js \
	js/configs.js \
	js/settings.js \
	js/urlParameters.js \
	js/nominatim.js \
	js/query.js \
	js/autorepair.js \
	js/ffs.js \
	js/ffs/free.js \
	js/ffs/parser.js \
	js/i18n.js \
	js/overpass.js \
	js/ide.js \
	libs/html2canvas/html2canvas.patched.js \
	libs/html2canvas/jquery.plugin.html2canvas.js \
	libs/canvg/rgbcolor.js \
	libs/canvg/canvg.js \
	libs/tokml/tokml.js \
	libs/togpx/togpx.js \
	libs/Blob.js/Blob.js \
	libs/canvas-toBlob.js/canvas-toBlob.js \
	libs/FileSaver/FileSaver.js

turbo.js: Makefile
	@rm -f $@
	cat $(filter %.js,$^) > $@

turbo.map.js: \
	js/jsmapcss/styleparser.js \
	js/jsmapcss/Condition.js \
	js/jsmapcss/Rule.js \
	js/jsmapcss/RuleChain.js \
	js/jsmapcss/Style.js \
	js/jsmapcss/StyleChooser.js \
	js/jsmapcss/StyleList.js \
	js/jsmapcss/RuleSet.js \
	libs/osmtogeojson/osmtogeojson.js \
	js/GeoJsonNoVanish.js \
	js/OSM4Leaflet.js \
	libs/mapbbcode/PopupIcon.js \
	js/configs.js \
	js/overpass.js \
	js/query.js \
	js/map.js

turbo.map.js: Makefile
	@rm -f $@
	cat $(filter %.js,$^) > $@

%.min.js: %.js Makefile
	@rm -f $@
	$(JS_COMPILER) $< -c -m -o $@

turbo.css: \
	libs/leaflet/leaflet.css \
	libs/jqueryui/jquery-ui.css \
	libs/CodeMirror/lib/codemirror.css \
	libs/locationfilter/src/locationfilter.css \
	css/default.css

turbo.css: Makefile
	@rm -f $@
	cat $(filter %.css,$^) > $@

turbo.min.css: turbo.css Makefile
	@rm -f $@
	$(CSS_COMPILER) $< $@

install: all
	mkdir -p $(install_root)
	mkdir -p $(install_root)/css
	mkdir -p $(install_root)/img
	mkdir -p $(install_root)/images
	mkdir -p $(install_root)/locales
	mkdir -p $(install_root)/data
	cp LICENSE $(install_root)
	cp turbo.js turbo.min.js $(install_root)
	cp turbo.map.js turbo.map.min.js $(install_root)
	cp turbo.css turbo.min.css $(install_root)
	cp css/compact.css $(install_root)/css
	cp css/map.css $(install_root)/css
	cp turbo.png favicon.ico $(install_root)
	cp index_packaged.html $(install_root)/index.html
	cp map_packaged.html $(install_root)/map.html
	cp map-key.png $(install_root)
	cp locales/*.json $(install_root)/locales
	cp -R libs $(install_root)/libs
	cp -R icons $(install_root)/icons
	cp libs/locationfilter/src/img/* $(install_root)/img
	cp libs/leaflet/images/* $(install_root)/images
	cp libs/jqueryui/images/* $(install_root)/images
	cp data/*.json $(install_root)/data

clean:
	rm -f turbo.js
	rm -f turbo.min.js
	rm -f turbo.map.js
	rm -f turbo.map.min.js
	rm -f turbo.css
	rm -f turbo.min.css

test:
	./node_modules/mocha-phantomjs/bin/mocha-phantomjs tests/index.html

translations:
	node locales/update_locales

presets:
	wget "https://github.com/openstreetmap/iD/raw/master/data/presets/presets.json" -O data/iD_presets.json --no-check-certificate
	node data/get_preset_translations

ffs:
	$(PEGJS) -o size -e turbo.ffs.parser < misc/ffs.pegjs > js/ffs/parser.js

icons: icons-maki icons-mapnik icons-osmic

icons-maki:
	wget https://github.com/mapbox/maki/zipball/mb-pages -O icons/maki.zip
	yes | unzip -ju icons/maki.zip */renders/*.png -d icons/maki/
	rm icons/maki.zip

icons-mapnik:
	wget https://github.com/gravitystorm/openstreetmap-carto/archive/master.zip -O icons/mapnik.zip
	yes | unzip -ju icons/mapnik.zip */symbols/*.png -d icons/mapnik/
	rm icons/mapnik.zip

icons-osmic:
	git clone --depth 1 https://github.com/nebulon42/osmic.git
	./osmic/tools/export.py --basedir osmic/ osmic/tools/config/overpass-turbo-png.yaml
	optipng -o 2 osmic/export/*
	cp osmic/export/* icons/osmic/
	rm -rf osmic

osmtogeojson:
	wget https://github.com/tyrasd/osmtogeojson/raw/gh-pages/osmtogeojson.js -O libs/osmtogeojson/osmtogeojson.js -O libs/osmtogeojson/osmtogeojson.js

overpass-turbo-ffs.js: js/ffs.js js/ffs/free.js js/ffs/parser.js
	cat $^ > $@
