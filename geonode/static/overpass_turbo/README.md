overpass turbo
==============

This is a GUI for testing and developing queries for the [Overpass-API](http://www.overpass-api.de/). It can also used for simple analysis of OSM data.

[![](http://wiki.openstreetmap.org/w/images/thumb/9/99/Overpass_turbo_showcase_1.png/600px-Overpass_turbo_showcase_1.png)](http://overpass-turbo.eu)

Getting Started
---------------

Just point your browser to [overpass-turbo.eu](http://overpass-turbo.eu) and start running your Overpass queries.

More Information about *overpass turbo* is found in the [OSM wiki](http://wiki.openstreetmap.org/wiki/Overpass_turbo).

Translating
-----------

Translations are managed using the [Transifex](https://www.transifex.com/projects/p/overpass-turbo) platform. After signing up, you can go to [overpass-turbo's project page](https://www.transifex.com/projects/p/overpass-turbo), select a language and click *Translate now* to start translating.

If your language isn't currently in the list, just drop me a [mail](mailto:tyr.asd@gmail.com) or open an [issue ticket](https://github.com/tyrasd/overpass-turbo/issues/new).

Development
-----------

[![Build Status](https://secure.travis-ci.org/tyrasd/overpass-turbo.png)](https://travis-ci.org/tyrasd/overpass-turbo)

### URL parameters

*overpass turbo* can be linked from other applications by using [URL parameters](http://wiki.openstreetmap.org/wiki/Overpass_turbo/Development#URL_Parameters).
For example, one can provide a query to load, set the initial map location, or instruct turbo to load a [template](http://wiki.openstreetmap.org/wiki/Overpass_turbo/Templates).

### git-branches

Development is done in the *master* branch, stable releases are commited to *gh-pages*.

### install & run

This application runs out of the box (no special installation is needed). Just put the repository on a web server (e.g. Apache or something [slimmer](https://gist.github.com/tmcw/4989751)) and point your browser to index.html. Recent versions of Chrome, Firefox and Opera have been tested and should work.

It is possible, to build a compacted/minified version of *turbo* out of the source files. For that, run `make && make install` after installing uglifyjs and csso: `npm install uglify-js csso pegjs`.

