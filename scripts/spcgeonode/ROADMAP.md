# Roadmap

## Before merging to master

- CRITICAL : change rest.properties config
- CRITICAL : see if Geoserver authkey tokens expire (even when the key is deleted from the database, it's still possible to use it until manually clicking "sync user/group service". It looks like it's some cache, but I don't know if it expires. Maybe we need to use webservice instead of user property...)
- fix updatelayerip on startup (currently creates a mess in links when host/port changes and deletes custom thumbnails)
- make monitoring module work (currently it's disabled because of some exception during startup)
- move the README to the documentation
- move this roadmap to github issues

## Eventually

- check if everything is ok with auth_keys (it seems Geonode uses expired keys...)
- tweak nginx settings (gzip output, cache, etc...)
- use alpine for django as well
- migrate to spc repositories instead of olivierdalang
- see if we can have geoserver exit on error, in not at least implement proper healtcheck
- keep a version marker in the geodatadir directory in case of updates to the datadir
- set more reasonable logging for geoserver
- add at least some basic integration test to travis
- see if we can setup something for backups on local filesystem
- serve static files from django directly rather than from nginx when developping (to see changes without collectstatic)
- add a service to run grunt tasks when developping
