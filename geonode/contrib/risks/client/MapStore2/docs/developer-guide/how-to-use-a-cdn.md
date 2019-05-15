The LeafletDraw plugin and the MapStore2 theme are linked via rawgit.com but in production it should be used a proper CDN.  
Once you have a stable version:
- upload the [LeafletDraw plugin](http://rawgit.com/Leaflet/Leaflet.draw/v0.2.4/dist/) and the [MapStore2 theme](https://github.com/geosolutions-it/MapStore2-theme/tree/master/theme/default) on your CDN
- edit the [index.html](https://github.com/geosolutions-it/MapStore2/blob/master/web/client/index.html) file to use your published resources.
