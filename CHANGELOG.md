# Change Log

## [3.1.1](https://github.com/GeoNode/geonode/tree/3.1.1) (2021-04-30)

[https://github.com/GeoNode/geonode/compare/3.0...3.1](https://github.com/GeoNode/geonode/compare/3.1...3.1.1)

## [3.2.0](https://github.com/GeoNode/geonode/tree/3.2.0) (2021-04-29)
### Breaking Changes

 - Bump to postgresql-13; *do not upgrade the docker image or be prepared to do a dump/restore of the DB*
 - Based on MapStore client [2.1.3](https://github.com/GeoNode/geonode-mapstore-client/releases/tag/2.1.3)
 - MapStore client is no more compatible with 3.0.x train
 - ResourceBase Model `BBOX` now is a geometry; that is no more compatible with the 3.1.x one
 - [GNIP-81: GeoNode Core Cleanup](https://github.com/GeoNode/geonode/issues/6917):
   - Removed GeoNetwork support
   - Removed QGIS-Server support
   - Removed SPC GeoNode support
 - Advanced Resources Publishing Logic has been revised (see below)

### Features

 - Python upgrade 3.7+
 - Django upgrade 2.2.16+
 - GeoServer upgrade 2.18.2
 - MapStore2 Client Updates:
   * Save Search Services to the Map
   * Save Map Preferences into the adapter model
   * Advanced Style Editor with graphical UI
   * Improved Map Save Widget, specific for GeoNode
   * New MapStore client configuration subsystem
   * Group Layer as named groups
 - Upgraded `Dokerfile` and `docker-compose` to version 3.4
 - Migration of CI from Travis to CircleCI
 - General Code Quality and Performance Improvements

 - Highlights GeoNode 3.2:
   * [GNIP-76: Add RTL Support](https://github.com/GeoNode/geonode/issues/6156)
   * [GNIP-77: GetFeatureInfo Templating For GeoNode](https://github.com/GeoNode/geonode/issues/6182)
   * [GNIP-78: GeoNode generic "Apps" model to include pluggable entities into the framework](https://github.com/GeoNode/geonode/issues/6684)
     - Added MapStore GeoStories as part of the GeoNode MapStore client
   * [GNIP-79: GeoNode REST APIs (v2)](https://github.com/GeoNode/geonode/issues/6685)
   * [GNIP-82: Thesauri improvements](https://github.com/GeoNode/geonode/issues/6925)
   * [GNIP-83: ResourceBase for metadata-only resources](https://github.com/GeoNode/geonode/issues/7057)
   * [GNIP-84: Upload Page Enhancements](https://github.com/GeoNode/geonode/issues/7154)
     - Improved Async Upload of Layers
     - GeoServer Importer Uploads are now stateful and can be resumed or canceled
   * [GNIP-85: Map legend](https://github.com/GeoNode/geonode/issues/7254)
   * [GNIP 86: metadata parsing and storing](https://github.com/GeoNode/geonode/issues/7263)
   * [GNIP-87: Reduce information returned to users to only what is strictly required and accessible](https://github.com/GeoNode/geonode/issues/7282)
   * Append data to an existing layer
   * Improved Metadata Editors, now able to handle HTML tags
   * Improved Catalog and Thesauri
   * Improved Thumbnails creation logic which is now relies on GetMap instead of outdated GeoServer Print Plugin
   * Possibility to Upload RDF thesaurus via web
   * Pluggable CSW prefiltering from external apps
   * New Contrib module: [GeoNode Keycloak Support](https://github.com/GeoNode/geonode-contribs/tree/master/django-geonode-keycloak)
   * Delete existing table on restore command feature (general improvements to Backup/Restore machinery)
   * Advanced Upload Workflow Improvements:
     - Non admin user cannot change permission
     - Disable edit permissions globally when read-only mode is active
     - RESOURCE_PUBLISHING:
        1. "unpublished" won't be visible to Anonymous users
        2. "unpublished" will be visible to registered users **IF** they have view permissions
        3. "unpublished" will be always visible to the owner and Group Managers
        By default the uploaded resources will be "unpublished".
        The owner will be able to change them to "published" **UNLESS** the ADMIN_MODERATE_UPLOADS is activated.
        If the owner assigns unpublished resources to a Group, both from Metadata and Permissions, in any case the Group "Managers" will be able to edit the Resource.
     - ADMIN_MODERATE_UPLOADS:
        1. The owner won't be able to change to neither "approved" nor "published" state (unless he is a superuser)
        2. If the Resource belongs to a Group somehow, the Managers will be able to change the state to "approved"
          but **NOT** to "published". Only a superuser can publish a resource.
        3. Superusers can do anything.
     - GROUP_PRIVATE_RESOURCES:
        The "unapproved" and "unpublished" Resources will be accessible **ONLY** by owners, superusers and members of the belonging groups.
     - GROUP_MANDATORY_RESOURCES:
        Editor will be **FORCED** to select a Group when editing the resource metadata.

 - Documentation Updates:
   * [GetFeatureInfo Templating For GeoNode](https://docs.geonode.org/en/master/usage/managing_maps/exploring_maps/get_fetureinfo.html?highlight=GetFeatureInfo)
   * [HowTo: Geonode with QGIS](https://docs.geonode.org/en/master/usage/other_apps/qgis/index.html)
   * [Improve GeoNode OpenID SP Protocol in order to be able to provide access to external clients](https://docs.geonode.org/en/master/usage/other_apps/qgis/index.html?highlight=Connect%20to%20Private%20layers%20by%20using%20OAuth2#connect-to-private-layers-by-using-oauth2)
   * [Document the use of slide show in themes](https://docs.geonode.org/en/master/admin/admin_panel/index.html?highlight=Slide%20show#slide-show)
   * [Update Advanced Installation steps to work against Ubuntu 20.04LTS](https://docs.geonode.org/en/master/install/advanced/core/index.html?highlight=Ubuntu%2020.04LTS#ubuntu-20-04lts)
   * [Update Advanced Installation steps to work against RHEL 7.x](https://docs.geonode.org/en/master/install/advanced/core/index.html?highlight=Ubuntu%2020.04LTS#rhel-7-x)
   * [How to setup rabbitmq, supervisor and memcached in order to fully enable async workers](https://docs.geonode.org/en/master/install/advanced/core/index.html?highlight=Enabling%20Fully%20Asynchronous%20Tasks#enabling-fully-asynchronous-tasks)
   * [How to Upgrade from 2.10.x / 3.0](https://docs.geonode.org/en/master/admin/upgrade/index.html?highlight=Upgrade%20from%202.10.x)
   * [Docs to connect production docker to external postgreSQL db server](https://github.com/GeoNode/documentation/pull/74)
   * [Documentation for new metadata settings](https://github.com/GeoNode/documentation/pull/75)
   * [Refers #6925: add documentation for thesaurus configuration](https://github.com/GeoNode/documentation/pull/77)
   * [Refers #6952: add documentation for uuidhandler](https://github.com/GeoNode/documentation/pull/78)
   * [Adding new settings in order to let the optional metadata in metadata wizard to become required](https://github.com/GeoNode/documentation/pull/84)
   * [Remove outdated/misleading SPC GeoNode documentation](https://github.com/GeoNode/documentation/pull/85)
   * [Relates to #7089 Delete existing table on restore](https://github.com/GeoNode/documentation/pull/86)
   * [Allow XSL customization](https://github.com/GeoNode/documentation/pull/87)
   * [Relates to #7150 Doc for upload thesaurus from admin interface](https://github.com/GeoNode/documentation/pull/88)
   * [Relates to #7194 Append data to layer](https://github.com/GeoNode/documentation/pull/89)
   * [Refers to #7214 Sorting Thesauri](https://github.com/GeoNode/documentation/pull/90)
   * [Relates to #6995 Documentation for ADVANCED_EDIT_EXCLUDE_FIELD](https://github.com/GeoNode/documentation/pull/91)

 - Improving GeoNode Theme Library: introducing Jumbotron Slides
 - Implementation of an action to assign bulk permissions on layer to users selected from People and/or Group Django admin forms enhancement #6582
 - Review of the current advanced resource workflow implementation enhancement security #6551
 - File system operations do not adhere to Django file storage API enhancement in progress #6414
 - Nav Toolbar gets distorted when multiple navbar items are added by the admin enhancement frontend major #6412
 - Allow only admins to edit/create keywords enhancement regression #6360
 - In home page show only ISO categories currently assigned to some dataset enhancement frontend #6332
 - Modify the admin theme customisation feature to allow for the use of a slide show in the home page enhancement feature frontend #6301
 - Improve GeoNode OpenID SP Protocol in order to be able to provide access to external clients enhancement security #6273
 - Limit "maps using this layer" to maps the user has permission to see enhancement security #6261
 - Prevent integrity errors on singleton model save enhancement #6223

 - **[Full list of Implemented GNIP](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Agnip)**
 - **[Full list of Implemented Features](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Afeature)**
 - **[Full list of Implemented Enhancements](https://github.com/GeoNode/geonode/issues?page=1&q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Aenhancement&utf8=%E2%9C%93)**
 - **[Full list of Dependencies Updates](https://github.com/GeoNode/geonode/issues?q=is%3Aclosed+milestone%3A3.2+label%3Adependencies+)**
 - **[Full list of Fixed Security Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Asecurity)**
 - **[Full list of Fixed Security Pull Requests](https://github.com/GeoNode/geonode/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+label%3Asecurity+milestone%3A3.2+)**
 - **[Full list of Resolved Regressions](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Aregression)**
 - **[Full list of Fixed Critical Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Ablocker)**
 - **[Full list of Fixed Major Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Amajor)**
 - **[Full list of Fixed Minor Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Aminor)**
 - **[Full list of Updated Translations](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.2+label%3Atranslations)**
 - **[All Closed Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A3.2)**

### Full Changelog

[https://github.com/GeoNode/geonode/compare/3.1...3.2.0](https://github.com/GeoNode/geonode/compare/3.1...3.2.x)

## [3.1](https://github.com/GeoNode/geonode/tree/3.1) (2020-11-30)

 - **[Implemented Features](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.1+label%3Afeature)**

 - **[Dependencies Updates](https://github.com/GeoNode/geonode/pulls?q=is%3Apr+is%3Aclosed+label%3Adependencies+milestone%3A3.1)**

 - **[Updated Doccumentations](https://github.com/GeoNode/documentation/issues?q=label%3A3.1+is%3Aclosed)**

 - **[Updated Documentations Diff](https://github.com/GeoNode/documentation/compare/6bd973af2bb9385f74840093615a87316fdd5400...d8be339725a02b40ba64a13d60ecacf5b32de0d2)**

 - **[Fixed Security Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A3.1+label%3Asecurity)**

 - **[Fixed Security Pull Requests](https://github.com/GeoNode/geonode/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+label%3Asecurity+milestone%3A3.1+)**

 - **[Resolved Regressions](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.1+label%3Aregression)**

 - **[Fixed Critical Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.1+label%3Ablocker)**

 - **[Fixed Major Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.1+label%3Amajor)**

 - **[Fixed Minor Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.1+label%3Aminor)**

 - **[Updated Translations](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.1+label%3Atranslations)**

 - **[All Closed Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A3.1)**

## Full Changelog

[https://github.com/GeoNode/geonode/compare/3.0...3.1](https://github.com/GeoNode/geonode/compare/3.0...3.1)


## [3.0](https://github.com/GeoNode/geonode/tree/3.0) (2020-05-18)

 - **[Implemented Features](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.0+label%3Afeature)**

 - **[Dependencies Updates](https://github.com/GeoNode/geonode/pulls?q=is%3Apr+is%3Aclosed+label%3Adependencies+milestone%3A3.0)**

 - **[Updated Doccumentations](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.0+label%3Adocs)**

 - **[Updated Doccumentations Pull Requests](https://github.com/GeoNode/geonode/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+label%3Adocs+milestone%3A3.0)**

 - **[Fixed Security Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A3.0+label%3Asecurity)**

 - **[Fixed Security Pull Requests](https://github.com/GeoNode/geonode/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+label%3Asecurity+milestone%3A3.0+)**

 - **[Resolved Regressions](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.0+label%3Aregression)**

 - **[Fixed Critical Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.0+label%3Ablocker)**

 - **[Fixed Major Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.0+label%3Amajor)**

 - **[Fixed Minor Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.0+label%3Aminor)**

 - **[Updated Translations](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A3.0+label%3Atranslations)**

 - **[All Closed Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A3.0)**

## [2.10.4](https://github.com/GeoNode/geonode/tree/2.10.4) (2020-05-18)

 - **[Implemented Features](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4+label%3Afeature)**

 - **[Dependencies Updates](https://github.com/GeoNode/geonode/pulls?q=is%3Apr+is%3Aclosed+label%3Adependencies+milestone%3A2.10.4)**

 - **[Updated Doccumentations](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4+label%3Adocs)**

 - **[Updated Doccumentations Pull Requests](https://github.com/GeoNode/geonode/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+label%3Adocs+milestone%3A2.10.4)**

 - **[Fixed Security Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4+label%3Asecurity)**

 - **[Fixed Security Pull Requests](https://github.com/GeoNode/geonode/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+label%3Asecurity+milestone%3A2.10.4+)**

 - **[Resolved Regressions](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4+label%3Aregression)**

 - **[Fixed Critical Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4+label%3Ablocker)**

 - **[Fixed Major Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4+label%3Amajor)**

 - **[Fixed Minor Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4+label%3Aminor)**

 - **[Updated Translations](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4+label%3Atranslations)**

 - **[All Closed Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A2.10.4)**

## [Full Changelog](https://github.com/GeoNode/geonode/compare/2.10.1...2.10.4)


## [2.10.1](https://github.com/GeoNode/geonode/tree/2.10.1) (2019-11-12)

 - **[Implemented Features](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1+label%3Afeature)**

 - **[Dependencies Updates](https://github.com/GeoNode/geonode/pulls?q=is%3Apr+is%3Aclosed+label%3Adependencies+milestone%3A2.10.1)**

 - **[Updated Doccumentations](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1+label%3Adocs)**

 - **[Updated Doccumentations Pull Requests](https://github.com/GeoNode/geonode/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+label%3Adocs+milestone%3A2.10.1)**

 - **[Fixed Security Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1+label%3Asecurity)**

 - **[Fixed Security Pull Requests](https://github.com/GeoNode/geonode/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+label%3Asecurity+milestone%3A2.10.1+)**

 - **[Resolved Regressions](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1+label%3Aregression)**

 - **[Fixed Critical Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1+label%3Ablocker)**

 - **[Fixed Major Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1+label%3Amajor)**

 - **[Fixed Minor Issues](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1+label%3Aminor)**

 - **[Updated Translations](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1+label%3Atranslations)**

 - **[All Closed Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A2.10.1)**

## [Full Changelog](https://github.com/GeoNode/geonode/compare/2.10...2.10.1)

<li> 2019-11-12: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/cf38e9f3c99b7ffa44c5c5027ea654d54c5c3290" target="blank"> Bump urllib3 from 1.25.6 to 1.25.7</a></li> 
<li> 2019-11-12: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/0c5c400bef8a842456cb4fd628dffbb3d07248f5" target="blank"> Bump deprecated from 1.2.6 to 1.2.7</a></li> 
<li> 2019-11-12: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/d423179a71a5e043c1e4f42df56445ee63b37ba0" target="blank"> Bump sqlalchemy from 1.3.10 to 1.3.11</a></li> 
<li> 2019-11-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/061f627ca8ea4137a1516900cc93d4d907b7bb7b" target="blank"> Bump pytest-django from 3.6.0 to 3.7.0</a></li> 
<li> 2019-11-11: afabiani <a href="http://github.com/geonode/geonode/commit/0e37af02269101729cc3e409bd4977e79bc1c1a1" target="blank"> [Fixes #5223] Layer details broken if no store identified</a></li> 
<li> 2019-11-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/d1da8ca5a9af24784d07ab8681e9c07087ed44da" target="blank"> Bump tqdm from 4.37.0 to 4.38.0</a></li> 
<li> 2019-11-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/283f497c7359b7f1c24cd31dadeb997a9d9806c5" target="blank"> Bump amqp from 2.5.1 to 2.5.2</a></li> 
<li> 2019-11-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/35eb680dcfbbc5bc2259644083f3281b20238109" target="blank"> Bump django-geonode-mapstore-client from 1.4.5 to 1.4.6</a></li> 
<li> 2019-11-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/6d31b96d200650652f242309b9c166ae681aa282" target="blank"> Bump django-mapstore-adapter from 1.0.11 to 1.0.12</a></li> 
<li> 2019-11-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/41accba57643d3ad487722ff88e19f5d9608fc30" target="blank"> Bump twisted from 19.7.0 to 19.10.0</a></li> 
<li> 2019-11-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/27bfe3b2348de0b91c3c8469ddcd7eb4fcbf67bf" target="blank"> Bump kombu from 4.6.5 to 4.6.6</a></li> 
<li> 2019-11-09: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/f2a3d709714887a252c2d8748ba13c64c21acdc4" target="blank"> added unicode tests for Menu, MenuItem and MenuPlaceholder</a></li> 
<li> 2019-11-08: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/e49cf46e55dafca22c26a10953025229001cc450" target="blank"> Revert "Bump amqp from 2.5.1 to 2.5.2"</a></li> 
<li> 2019-11-08: gioscarda <a href="http://github.com/geonode/geonode/commit/4bfce88c32d2267aa0e0139fe6804f17712c8306" target="blank"> [Fixes #5214] Fix regression on monitoring countries endpoint</a></li> 
<li> 2019-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/763c5ef085f5010f714711ddececb64fdfa6810e" target="blank"> [Fixes #5209] MapStore client critical slow-down with latest Chrome updates</a></li> 
<li> 2019-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/2e3a117540b9b63855459fb14f892a106d7d8f16" target="blank"> [Hardening] layer_detail typo</a></li> 
<li> 2019-11-08: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/d78f6b213da2ec91d3c27e509ced6dfd5a58ebf0" target="blank"> Bump amqp from 2.5.1 to 2.5.2</a></li> 
<li> 2019-11-08: gioscarda <a href="http://github.com/geonode/geonode/commit/c3485492c6918fc71f401879608f3df503ccae31" target="blank"> [Fixes #5203] avoid count label in countries, add missing flags</a></li> 
<li> 2019-11-06: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/9b36abf56b1ca8c5296dc1351027d5d2dc639938" target="blank"> Update six requirement from <1.11.0 to <1.14.0</a></li> 
<li> 2019-11-06: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/9a6626836bb43fe73431b45b8a42a6ab78cb8092" target="blank"> Bump psutil from 5.6.4 to 5.6.5</a></li> 
<li> 2019-11-05: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/1049179634edb7aaf5262f75451c3702f4adf409" target="blank"> fixed pep8 errors</a></li> 
<li> 2019-11-05: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/60929576a1bb0b45202b7f02905214f8d3af7bf4" target="blank"> fixes #5197</a></li> 
<li> 2019-11-04: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/cc244c0ba35bd1ea71153c6b28819f11cc8cdaa3" target="blank"> Bump psutil from 5.6.3 to 5.6.4</a></li> 
<li> 2019-11-04: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/31c4d6312ca5a890e5218cbd1cccda7933c81c3b" target="blank"> Bump django from 1.11.25 to 1.11.26</a></li> 
<li> 2019-11-04: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/068ad9b820e15426785c984002d1428efac8450d" target="blank"> Bump python-dateutil from 2.8.0 to 2.8.1</a></li> 
<li> 2019-11-04: afabiani <a href="http://github.com/geonode/geonode/commit/e473fa75859d999e13311d7abf286f987d97a846" target="blank">  - _resourcebase_info_panel is showing the tkeywords only if THESAURUS is enabled and adding commas between words</a></li> 
<li> 2019-11-04: afabiani <a href="http://github.com/geonode/geonode/commit/bccca80ee5849fe9ea2166a2f5d2a5569aa2b4ee" target="blank"> [Fixes #5181] Wrong words in French translation</a></li> 
<li> 2019-10-31: Fanevanjanahary <a href="http://github.com/geonode/geonode/commit/7cee43ce1063ee8f8e0a79523e81c167929c36dd" target="blank"> Changed wrong words in French version</a></li> 
<li> 2019-11-04: afabiani <a href="http://github.com/geonode/geonode/commit/d2fa2b0669e67009604544b609692f4895d55405" target="blank">  - Fixes "field" rendering error when Thesauri have been enabled</a></li> 
<li> 2019-11-01: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b792f1e7913358c17166d4d6f858b90ca8a31071" target="blank"> Bump tqdm from 4.36.1 to 4.37.0</a></li> 
<li> 2019-11-01: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/9ef6bc45998a2d312ce3a719fdcf29092d6d0b28" target="blank"> [Fixes #5172] Add fix for import thesaurus</a></li> 
<li> 2019-11-01: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/a4cf6a67869471fb6cf59cc03be48e0e06aa357d" target="blank"> [Fixes #5172] Add docs for thesaurus</a></li> 
<li> 2019-10-31: afabiani <a href="http://github.com/geonode/geonode/commit/42c3eeca00898f752efe9976ec590508791ff000" target="blank"> [Fixes #5158] Update thesaurus management command and fix autocomplete</a></li> 
<li> 2019-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/a305f3218d57bbc15cea7a5cba531b401b74b5bf" target="blank"> [Fixes #4661] Replace Layer functionality incomplete/broken</a></li> 
<li> 2019-09-05: capooti <a href="http://github.com/geonode/geonode/commit/8c2c3363ea464b293809edaa46656b9aec709e35" target="blank"> Mitigates possibilities for error #2932</a></li> 
<li> 2019-10-30: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/321f972000100797798346f6a69ddcf9a896e1c8" target="blank"> Bump setuptools from 41.5.1 to 41.6.0</a></li> 
<li> 2019-10-30: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/0c9bab560835ff7181ed1134093ca2a0ad446446" target="blank"> [Fixes #5105] Error when using THESAURI</a></li> 
<li> 2019-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/7f0ad22a4c16fa01469e40f561cd373e4c31ec52" target="blank"> [Docs] Cleaning up misleading instructions</a></li> 
<li> 2019-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/f0073e84298a8bce5b716d7888b0920a72c58760" target="blank"> [Fixes #5136] Assignment of users to member groups should be done at activation time</a></li> 
<li> 2019-10-29: capooti <a href="http://github.com/geonode/geonode/commit/58b6e14b766b1e260c7e4f58f9ffeb706fc54155" target="blank"> [Implements #5149] Add documentation for migrating GeoNode from 2.4 to 2.10.1</a></li> 
<li> 2019-10-29: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/5a8476e0b2f95ae4fa9aa204e4cca08ba87353df" target="blank"> [Fixes #5117] Publishing layers of two remote services with same (#5135)</a></li> 
<li> 2019-10-29: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/8d261cc3abb3d78fd17fdad7a054e4391ff3d278" target="blank"> Bump setuptools from 41.5.0 to 41.5.1 (#5139)</a></li> 
<li> 2019-10-29: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/010aa1f5d781233237cc75df31a8bfae2f21499a" target="blank"> [Fixes #5138] Fix assertation error</a></li> 
<li> 2019-10-29: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/04dc9b7044629e6ff5897d9adc7b7cd2c2957b8d" target="blank"> [Fixes #5138] Fix blank space</a></li> 
<li> 2019-10-29: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/38dfa27c1f7dd6a589396db77f72a94fc243ceaf" target="blank"> Bump flake8 from 3.7.8 to 3.7.9</a></li> 
<li> 2019-10-29: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/95d4993bc5dab28d21e9eb712be29888cefe9ce5" target="blank"> [Fixes #5138] Fix Flake8</a></li> 
<li> 2019-10-29: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/fdd2c85fe7723795069f27fca3e5bd9890433c90" target="blank"> [Fixes #5138] Escape Hierarchical-tags</a></li> 
<li> 2019-10-29: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/7bab9e1234f36a4201b024c85220fd351bc32228" target="blank"> [Fixes #5137] Striptags for service resources</a></li> 
<li> 2019-10-28: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/367220a2bcbfef6217539025a24b4ec951ffbcc1" target="blank"> Bump setuptools from 41.4.0 to 41.5.0</a></li> 
<li> 2019-10-28: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/c9a9e738dd5789389b4bdcf41a142282244496f0" target="blank"> Bump decorator from 4.4.0 to 4.4.1</a></li> 
<li> 2019-10-28: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/2de1a63d5341b7d75231f9e6a1a935bf30299072" target="blank"> Update django-modeltranslation requirement</a></li> 
<li> 2019-10-25: capooti <a href="http://github.com/geonode/geonode/commit/7de17f048aa34caab64093de9779a81c264c2bcd" target="blank"> [Fixes #5121] ResourceBase API returns an error if a curated thumbnail img file is not existing anymore</a></li> 
<li> 2019-10-25: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/9f4009ccff7c65874d2624580c3951c564a8da78" target="blank"> [Fixes #4827] Line layer uploaded to GeoNode is rendered as point layer (#5116)</a></li> 
<li> 2019-10-24: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6015531af9bf0fe6d4f182b6210b81113527be68" target="blank"> [Fixes #4827] Line layer uploaded to GeoNode is rendered as point layer (#5092)</a></li> 
<li> 2019-10-24: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/5ed36dc33d2a2d8da7228566ef41e3f235a7f9fd" target="blank"> Update django-floppyforms requirement from <=1.7.0 to <1.9.0</a></li> 
<li> 2019-10-23: capooti <a href="http://github.com/geonode/geonode/commit/01b511d19cf95b4aff692ca26cef824f464b0b7b" target="blank"> Enable thesauri api load only if a thesauri is defined</a></li> 
<li> 2019-10-23: afabiani <a href="http://github.com/geonode/geonode/commit/83b805fa98446c91974441d7a9c47fa877bfee32" target="blank"> [Documentation] Fixed .env docker description for geonode-project</a></li> 
<li> 2019-10-23: afabiani <a href="http://github.com/geonode/geonode/commit/fef9d1631e16742ce95ff7c83d8aab08a8035eb4" target="blank"> [Documentation] Fixed typo goenode to geonode</a></li> 
<li> 2019-10-22: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/b2709d7128c7cc4867a4788ea7e5f0fdd22b83e3" target="blank"> Update settings.py</a></li> 
<li> 2019-10-22: afabiani <a href="http://github.com/geonode/geonode/commit/f1a329c946dc21c61fbb5fffada2f0ae20e251be" target="blank"> [Fixes #5096] Disabling geonode.monitoring causes model exceptions on views</a></li> 
<li> 2019-10-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/bedd1172a63b3c211ecb0fd1c6a6c41954d32cfe" target="blank"> Bump pillow from 6.2.0 to 6.2.1</a></li> 
<li> 2019-10-22: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/c3ab4da3df18ebe92503c9e679f876edc93e72c1" target="blank"> Update index.html</a></li> 
<li> 2019-10-21: afabiani <a href="http://github.com/geonode/geonode/commit/ebf16f4ae29e3bb2e2a393c780072b7b352afc64" target="blank"> [Testing] Code Coverage / CHANGELOG updates</a></li> 
<li> 2019-10-21: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/a36afcc8af06a3ed0a6a85ecebef2697899b81b8" target="blank"> Bump python-slugify from 3.0.6 to 4.0.0</a></li> 
<li> 2019-10-21: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/35bf8a730200aba471373393d869f89a690f6a05" target="blank"> Bump psycopg2 from 2.8.3 to 2.8.4</a></li> 
<li> 2019-10-21: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/fab32b6c15d0b5ab0b9ade3858f09905618688ee" target="blank"> Bump django-celery-beat from 1.1.1 to 1.5.0</a></li> 
<li> 2019-10-21: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/ee8a56181d842802b30f1dc3e32de943351a4771" target="blank"> Bump django-leaflet from 0.24.0 to 0.25.0</a></li> 
<li> 2019-10-21: afabiani <a href="http://github.com/geonode/geonode/commit/9e63d26c46b0571d07cc6922d5780f60e53de906" target="blank"> [Testing] Code Coverage</a></li> 
<li> 2019-10-21: afabiani <a href="http://github.com/geonode/geonode/commit/3c810432938aa7a54d82c1f558f63000ae7b4fbb" target="blank"> [Testing] Code Coverage</a></li> 
<li> 2019-10-19: Toni <a href="http://github.com/geonode/geonode/commit/0bb703c93dc2f4b8ef289b31e75c00b7736d48f1" target="blank"> [Fixes #5073] Added blank line</a></li> 
<li> 2019-10-19: Toni <a href="http://github.com/geonode/geonode/commit/17cc5c767a4df811539e47395db0bbfd4e6fde03" target="blank"> [Fixes #5073] Update install docs</a></li> 
<li> 2019-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/4eae34702e64dfcdedc8212626db25ad438d944d" target="blank"> [Fixes #5070] Add Bing background layer config to MapStore2 adapter if apiKey is provided</a></li> 
<li> 2019-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/6054cb2d0ffe9ce1f7459f57eb35db582defd0b1" target="blank"> [Hardening] coverage run integration tests too</a></li> 
<li> 2019-10-18: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/9b173a7e3a4b1a23c32777153ffb0f139f151913" target="blank"> [Fixes: #4659] Double message on Submit invite users</a></li> 
<li> 2019-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/7a2fc0982ae3a59bf4d7d9353ed2f9a2c2d04abf" target="blank"> [Hardening] coverage run integration tests too</a></li> 
<li> 2019-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/b3c7dcf55c1049b5b95e51bfe6cd08b94a3ea6ef" target="blank"> [Hardening] coverage run integration tests too</a></li> 
<li> 2019-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/4f86f69febacc335a3340ca87367c44328c94e63" target="blank"> [Hardening] coverage run integration tests too</a></li> 
<li> 2019-10-18: gioscarda <a href="http://github.com/geonode/geonode/commit/ca1e7ac19ddf2b8fbf627a4310507e35a0be5bfc" target="blank"> [Fixes #5051] arrangement for geonode_logstash contrib app</a></li> 
<li> 2019-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/8922cb7dcb6c9467e901e26c1f9df41c1fbef4fe" target="blank"> [Hardening] A bit more robust logical check</a></li> 
<li> 2019-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/3cac72dc845b428dad933b82a850590af2dade4b" target="blank"> [Hardening] Original Dataset link: skip checks for external links</a></li> 
<li> 2019-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/48940dce227a2b4802fcf380b6d4d2d6bc4515b3" target="blank"> [Hardening] A bit more robust logical check</a></li> 
<li> 2019-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/a57165cd619ba9f1a0d31e9e5e1ecf80f7c001b5" target="blank"> [Fixes #4942] Download layer filter not sending CQL filter anymore</a></li> 
<li> 2019-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/6336b199bec4735328a5456225ed07f7f6c3ec48" target="blank"> [Fixes #4956] "Original Dataset" Link behavior improvements</a></li> 
<li> 2019-10-17: gioscarda <a href="http://github.com/geonode/geonode/commit/8a547f11d3c8cbe847d1e0c5e019c258c43a4822" target="blank"> [Fixes #5031] Disable monitoring by default</a></li> 
<li> 2019-10-17: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/8c3343423dfd4fd08a2a443723b9ff1dbef57aeb" target="blank"> Bump pytest-django from 3.5.1 to 3.6.0</a></li> 
<li> 2019-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/bee9e0808fa3ffda4862dd87e804764ac24e869c" target="blank"> [Documentation] Add "OAUTH2_API_KEY" setting to the settings list</a></li> 
<li> 2019-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/bf08e9bcfef8ea9bf8c11fc600925b2be8d70a4a" target="blank">  - Hide "private" groups to "non-members"</a></li> 
<li> 2019-10-16: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/0a784c09be2028c8fa51f76758aed0195b8d009a" target="blank"> Update gnip.md</a></li> 
<li> 2019-10-16: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/c0c9d583dc844994b5208c6f3721f26007213ab4" target="blank"> fix flake8 issue with _</a></li> 
<li> 2019-10-16: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/6680b26d5d254c2c8c6d89c7dac1dde7860b9433" target="blank"> #5054 | 5053 Update Translations</a></li> 
<li> 2019-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/35912240ac0f953ad7d94359c151de62f86f5b6c" target="blank"> [Hardening] Fix backup/restore GeoServer rest endpoints</a></li> 
<li> 2019-10-15: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/adfd579162b9110171ae2bd16f61cd8e0ecc0c19" target="blank"> Bump pytest from 4.6.5 to 4.6.6</a></li> 
<li> 2019-10-13: Lilian Guimarães <a href="http://github.com/geonode/geonode/commit/4f19cb45550f2f9b7d3e323995e2e00377d3440f" target="blank"> Remove plusone (Closes #4929)</a></li> 
<li> 2019-10-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/7654c3ea55e3105cbe59b91be2e4108cf2defdaa" target="blank"> Bump python-slugify from 3.0.4 to 3.0.6</a></li> 
<li> 2019-10-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/f92aa2126128a82363247f22b7798bf3e9ea14f9" target="blank"> Bump sqlalchemy from 1.3.9 to 1.3.10 (#5032)</a></li> 
<li> 2019-10-11: Toni <a href="http://github.com/geonode/geonode/commit/52fe1e19197f25700eb476f18132672876bf5b0b" target="blank"> #4930 Remove Edit Data button for RASTER layer (#5035)</a></li> 
<li> 2019-10-10: Paolo Corti <a href="http://github.com/geonode/geonode/commit/eb0e2b138916821a4256f2af31179c390a89cac5" target="blank"> Fixes #5005 (#5027)</a></li> 
<li> 2019-10-09: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/5dac976b26702cb370d7e6e0cbae8a6dec5151e6" target="blank"> Bump django-geonode-mapstore-client from 1.4.3 to 1.4.4 (#5029)</a></li> 
<li> 2019-10-08: afabiani <a href="http://github.com/geonode/geonode/commit/0bf61c0cd43687aa920a78186f6092274cfcbeed" target="blank"> [Documentation] Loading (and Processing) external data / importlayers and updatelayers Management Commands</a></li> 
<li> 2019-10-08: afabiani <a href="http://github.com/geonode/geonode/commit/d0627973fd37839f2f3fc56a0e220e1993253ced" target="blank"> [Documentation] Backporting GeoNode/GeoServer AA Sections - update GeoFence db config</a></li> 
<li> 2019-10-08: afabiani <a href="http://github.com/geonode/geonode/commit/5d4b2487bd84587a5673da5f0a1057f482a7bb52" target="blank"> [Documentation] Backporting GeoNode/GeoServer AA Sections</a></li> 
<li> 2019-10-08: afabiani <a href="http://github.com/geonode/geonode/commit/ab60609c3ca0a5800112cb9aa704330d1b5b06a4" target="blank"> [Documentation] LDAP Contrib Module Documentation</a></li> 
<li> 2019-10-08: afabiani <a href="http://github.com/geonode/geonode/commit/5f9df01611ae777fdbca81c29f48f8d0d66ccd74" target="blank"> [Hardening] Cleanup unneeded deps</a></li> 
<li> 2019-10-08: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/40c8961621def0a31d755a8774905fb0b6cc4351" target="blank"> Adding LiliGuimaraes to CLA</a></li> 
<li> 2019-10-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b92738cbee750139c39642207209abaed1117dd6" target="blank"> Bump django-mapstore-adapter from 1.0.8 to 1.0.9</a></li> 
<li> 2019-10-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/47f0b90df975d16d1d5fe5fbfa2a492cceb739e3" target="blank"> Bump sqlalchemy from 1.3.8 to 1.3.9</a></li> 
<li> 2019-10-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/af0611a0421c7e863d022ad8ac5f7118fdfea6e3" target="blank"> Bump beautifulsoup4 from 4.8.0 to 4.8.1</a></li> 
<li> 2019-10-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/62ab45b1ead7a4b9e15d9a925f6c243d91865f1e" target="blank"> Bump django-geonode-mapstore-client from 1.4.2 to 1.4.3</a></li> 
<li> 2019-10-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/a6f33d9b88a98db113aa0bec0e59a9f69f2e716b" target="blank"> Bump pytz from 2019.2 to 2019.3</a></li> 
<li> 2019-10-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/77b0532edd57131ce9e524b715364e0dc4e352ff" target="blank"> Bump setuptools from 41.2.0 to 41.4.0</a></li> 
<li> 2019-10-07: afabiani <a href="http://github.com/geonode/geonode/commit/75d746174ea5e04d26a4e5a2964d4a7331094f5b" target="blank"> [Revert][Hardening] http_client caching requests</a></li> 
<li> 2019-10-07: afabiani <a href="http://github.com/geonode/geonode/commit/2fc74f9a4bf4ecd631549db644ae171bb03baf7f" target="blank"> [Hardening] http_client caching requests</a></li> 
<li> 2019-10-07: afabiani <a href="http://github.com/geonode/geonode/commit/6b6a5d12d9cfbe3101c44fcaa1c935a1f53cd0c2" target="blank"> [Hardening] - Get rid of redoundant/unuseful methods</a></li> 
<li> 2019-10-07: afabiani <a href="http://github.com/geonode/geonode/commit/4d2652f6d1ec8f23002a22d19d08b49d2ea566ef" target="blank">  - Add 'spatialreference.org' to default settings</a></li> 
<li> 2019-10-07: Toni <a href="http://github.com/geonode/geonode/commit/b802e3685bc1f5c16dd571cb697c00489656e256" target="blank"> [Fixes: #5000] Update Frontend section</a></li> 
<li> 2019-10-06: Steffen Berger <a href="http://github.com/geonode/geonode/commit/ac8bcb43816e5ffafbfd227295baecc5a26f91ed" target="blank"> [Fixes #4954] only needed attributes added to cookie, when adding layer to cart (#4968)</a></li> 
<li> 2019-10-06: Toni <a href="http://github.com/geonode/geonode/commit/6648b8b9d4305d1ef18c85a979571541d7935e75" target="blank"> [Fixes: 4988] Rework static build process (#4989)</a></li> 
<li> 2019-10-02: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/b51c2748065e663240e57e189347c4f8a8774104" target="blank"> [Hardening] Make master more resilient to errors</a></li> 
<li> 2019-10-04: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/1835dc24d1585e3ba834a9208ef96318cf288af2" target="blank"> Bump docker from 4.0.2 to 4.1.0</a></li> 
<li> 2019-10-04: gioscarda <a href="http://github.com/geonode/geonode/commit/ad0af3d937eeb3928422ec947fffc98f02490020" target="blank"> [Fixes #4990] fix set_layers_permissions managament command</a></li> 
<li> 2019-10-04: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/578224ce8857b9b6ee72f406f5084c158d4f8c0b" target="blank"> Adding "sjohn-atenekom" to the authorized list of users</a></li> 
<li> 2019-10-02: afabiani <a href="http://github.com/geonode/geonode/commit/0a505d20086a8ebe0b966ece449016f030d635d2" target="blank"> [Docs] Updating installation instructions for GeoNode Project</a></li> 
<li> 2019-10-01: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/f4591dc1481079426fd14cde93f23c84ac236046" target="blank"> Bump pillow from 6.1.0 to 6.2.0</a></li> 
<li> 2019-10-01: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/af246395eb75c8fdb032f72baaadce123d23121b" target="blank"> Bump django from 1.11.24 to 1.11.25</a></li> 
<li> 2019-09-30: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/62f2229bf670e86c40f2f062d62de5f53298f8f9" target="blank"> Bump amqp from 2.5.1 to 2.5.2</a></li> 
<li> 2019-09-30: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/14c585510a398ad547596376afc20adb9e072049" target="blank"> Bump kombu from 4.6.4 to 4.6.5</a></li> 
<li> 2019-09-30: afabiani <a href="http://github.com/geonode/geonode/commit/a06bbce3766fd97b2fa9d09b9f6e971ede2f5a99" target="blank"> [Docs] update geonode-project setup instructions</a></li> 
<li> 2019-09-30: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/53cbda1c3fd5022901a68316c18d2d98d7e31b1d" target="blank"> [Fixes #4959] By using UPLOADER=geonode.rest we are facing a timing issues on signals (#4960)</a></li> 
<li> 2019-09-30: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/203ba3dea700add27671fae7d99e6f951364b38a" target="blank"> [Fixes #4964] Date widget has gone (#4969)</a></li> 
<li> 2019-09-27: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6825a06c6e0f2d2b971964f2eab603c4cf3f4b96" target="blank"> [Fixes #4949] UnicodeEncodeError in upload.models.update_from_session (#4958)</a></li> 
<li> 2019-09-27: zoran995 <a href="http://github.com/geonode/geonode/commit/dd87201ef5de8bda5e4a68f4cca728924c412ab2" target="blank"> Use Tomcat 8.5.46</a></li> 
<li> 2019-09-27: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/2ffc5756e3b47dff9964d0c5e471c7159f19f3fd" target="blank"> Update httplib2 requirement from <0.13.2 to <0.14.1</a></li> 
<li> 2019-09-27: afabiani <a href="http://github.com/geonode/geonode/commit/60f4f693379d3ae564763a73bbc1657462e8ba9a" target="blank"> [Fixes #4739] Layer post_save deletes links to external thumbnails / data</a></li> 
<li> 2019-09-26: afabiani <a href="http://github.com/geonode/geonode/commit/bcaec711e895d6650333121f535cb3acb26110dd" target="blank"> [Hardening] Missing link name on "set_all_layers_metadata" mgmt command</a></li> 
<li> 2019-09-26: afabiani <a href="http://github.com/geonode/geonode/commit/9a72c75b7ffb382f219cf49582e22e4382590ccd" target="blank"> [Hardening] Sanity checks on links number</a></li> 
<li> 2019-09-26: afabiani <a href="http://github.com/geonode/geonode/commit/9b0b32f9d82e24a0f0b3bf7afcb2e4a7f38618ce" target="blank"> [Hardening] Correct bbox checks on geoext JS</a></li> 
<li> 2019-09-25: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/90336f9b68941b5297467427fbdc42be1c6f3988" target="blank"> Bump urllib3 from 1.25.5 to 1.25.6</a></li> 
<li> 2019-09-23: root <a href="http://github.com/geonode/geonode/commit/11b7ae5cb1abf74af696cbeeebd9be5477962be3" target="blank"> [Hardening] Make gslurp resilient to errors in case 'ignore_errors' has been specified</a></li> 
<li> 2019-09-23: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/7ebf7552bb95d0c3b3d3df2b24ee44252fe54667" target="blank"> Bump python-slugify from 3.0.3 to 3.0.4</a></li> 
<li> 2019-09-23: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/4d31e9113876c38226cc933e1a4ebd8f8b4e816a" target="blank"> [Hardening] Favourite model _unicode resilient to None</a></li> 
<li> 2019-09-23: Toni <a href="http://github.com/geonode/geonode/commit/833b8c6571e0c1b22e3bbd68dcd69648da435284" target="blank"> [Fixes: #4963] Fix wrong template include for all_auth</a></li> 
<li> 2019-09-23: afabiani <a href="http://github.com/geonode/geonode/commit/cc5b941265c9c1d85cca6d4b590ec9f377cf9d10" target="blank"> [Hardening] Add metadata links names to 'set_all_layers_metadata' mgmt cmd</a></li> 
<li> 2019-09-23: afabiani <a href="http://github.com/geonode/geonode/commit/a61632f846e4fdd3f3e5a4b485963d2f753f5545" target="blank"> [Hardening] Add metadata links names to 'set_all_layers_metadata' mgmt cmd</a></li> 
<li> 2019-09-22: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/45baa01d7e9b722d1c0c5dd300c6804d4cfd6aa7" target="blank"> #4933 forgot password in modal</a></li> 
<li> 2019-09-20: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b5f4132235c467c59218bc34a12f6891562ef4fd" target="blank"> Bump urllib3 from 1.25.3 to 1.25.5</a></li> 
<li> 2019-09-20: afabiani <a href="http://github.com/geonode/geonode/commit/cd419b55779deb13e54f19c8ee1b3fe028812e09" target="blank"> [Fixes #4907] Add the possibility of enabling "captcha" on GeoNode signup form</a></li> 
<li> 2019-09-19: afabiani <a href="http://github.com/geonode/geonode/commit/d2213335220d24e7acfb34c9870e52c6662785e9" target="blank"> [Hardening] Exposing to env AVATAR_GRAVATAR_SSL option</a></li> 
<li> 2019-09-19: afabiani <a href="http://github.com/geonode/geonode/commit/489aebada2bd690c4ee4ee24f273c26f2d634444" target="blank"> [Hardening] Exposing to env AVATAR_GRAVATAR_SSL option</a></li> 
<li> 2019-09-19: afabiani <a href="http://github.com/geonode/geonode/commit/cdb6607c6b59053ed7f482d1594f812abb8218ec" target="blank"> Bump django-mapstore-adapter to 1.0.8</a></li> 
<li> 2019-09-19: afabiani <a href="http://github.com/geonode/geonode/commit/b5f860f9c590ace9c9515c0ac9ce7a872fd28348" target="blank"> [Hardening] Removing redundant float conversion of coordinates</a></li> 
<li> 2019-09-19: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/bb9c98040713e290d9f5b98fb572489743ab1929" target="blank"> Bump tqdm from 4.36.0 to 4.36.1</a></li> 
<li> 2019-09-19: afabiani <a href="http://github.com/geonode/geonode/commit/28755ed905bd8c0dd446e878ad8b887e0c90247a" target="blank"> [Fixes #4924] Add member to Group is broken</a></li> 
<li> 2019-09-19: Toni <a href="http://github.com/geonode/geonode/commit/a7e5303743b123a186e05ed3b551b68e2c561001" target="blank"> [Fixes: #4920] Footer Display Code on Detail Layer pages</a></li> 
<li> 2019-09-18: Toni <a href="http://github.com/geonode/geonode/commit/4aeed98f76f6f3882e9de59cd133fbcc5b316545" target="blank"> #fixes 4916 – show featured items</a></li> 
<li> 2019-09-18: GeoSolutions <a href="http://github.com/geonode/geonode/commit/f35ac7adcc16ab766c66a5bc8f467967a7e9d830" target="blank"> [Hardening] Minor refactoring: check in a more pythonic way</a></li> 
<li> 2019-09-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/c5a40e8103cbdea9e2a9aeb04b2acf5501f20d6a" target="blank"> Bump tqdm from 4.35.0 to 4.36.0</a></li> 
<li> 2019-09-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/37d905ab271d747d09727b4ec29fe2da6be7849f" target="blank"> Bump geoserver-restconfig from 1.0.3 to 1.0.4</a></li> 
<li> 2019-09-18: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/80c8de7f62998e6400eb1b927031fadd6d3de3b3" target="blank"> [Fixes #4911] On Monitoring plugin the uptime is not correctly computed (#4912)</a></li> 
<li> 2019-09-18: afabiani <a href="http://github.com/geonode/geonode/commit/bc20458439ebb2aa191ebb115166083643b43dfd" target="blank">  - updating Italian translations</a></li> 
<li> 2019-09-17: GeoSolutions <a href="http://github.com/geonode/geonode/commit/e03a4383f3021fd0b92b3f3593ddbede78f7ac46" target="blank"> [Hardening] Remove code warnings</a></li> 
<li> 2019-09-17: GeoSolutions <a href="http://github.com/geonode/geonode/commit/c005c21b05d7095f472a323d1492449c0eaa93c2" target="blank"> [Hardening] Remove code warnings</a></li> 
<li> 2019-09-17: gioscarda <a href="http://github.com/geonode/geonode/commit/3927a3a0c64958dec7fe0f74e312b05eac23671b" target="blank"> [Fixes #4908] change monitoring label</a></li> 
<li> 2019-09-17: afabiani <a href="http://github.com/geonode/geonode/commit/823d8d6a73f7ea1f93fc04e64baedcc74b5cdc16" target="blank"> [Hardening] Make 'set_all_layers_metadata' management command more robust</a></li> 
<li> 2019-09-17: gioscarda <a href="http://github.com/geonode/geonode/commit/ef3162acca365065945ba0b1d1ee6f09870f8497" target="blank"> [Fixes #4903] fixing hits count</a></li> 
<li> 2019-09-14: afabiani <a href="http://github.com/geonode/geonode/commit/8e20c826563363ab40a5a8008fb1263636e021ca" target="blank"> [Hardening] Get rid of harmful logging</a></li> 
<li> 2019-09-13: afabiani <a href="http://github.com/geonode/geonode/commit/c15fa9ad873a400afc0b58412d147b3ae6c34069" target="blank"> [Fixes #4790] Issue adding remote service with non-ascii characters in the service name - 'ascii' codec can't encode character u'\xe9' in position 8: ordinal not in range(128)</a></li> 
<li> 2019-09-13: gioscarda <a href="http://github.com/geonode/geonode/commit/5156cbd5b1aa2e19845926801c9d0ead9e868670" target="blank"> [Fixes #4896] fixing data in response</a></li> 
<li> 2019-09-13: afabiani <a href="http://github.com/geonode/geonode/commit/08c1a36206f20326966ebfea5ccb118baf61e14d" target="blank"> [Hardening] Get rid of crazy cycle over the GeoServer catalog</a></li> 
<li> 2019-09-12: afabiani <a href="http://github.com/geonode/geonode/commit/7d1a6a13d6153f9b1d388f2ded71baeff081db89" target="blank"> [Fixes #4884] Attached SLD works only with ZIP files when "geonode.importer" method is enabled</a></li> 
<li> 2019-09-13: afabiani <a href="http://github.com/geonode/geonode/commit/6cc6f71fbce861e42fb2410ae4f3c5de00a475de" target="blank"> [Hardening] Upgrade angular from 1.5.0 to 1.6.0</a></li> 
<li> 2019-09-12: root <a href="http://github.com/geonode/geonode/commit/4070dbfa77e9cadf188227c2a311a9a844eb1339" target="blank"> [Hardeninig] Remove unuseful computation</a></li> 
<li> 2019-09-12: afabiani <a href="http://github.com/geonode/geonode/commit/640ddae08dff034d15d99282ec7759dba2f5f961" target="blank"> [Hardening] Refresh js deps</a></li> 
<li> 2019-09-12: afabiani <a href="http://github.com/geonode/geonode/commit/2ab57c0e31fd5c811fadd065fad94ebc2e9ffdd3" target="blank"> [Fixes #4881] Improve initial generate thumbnail quality</a></li> 
<li> 2019-09-12: afabiani <a href="http://github.com/geonode/geonode/commit/8e541b9f461f201352a3ed766440f6a6acf43fe6" target="blank"> [Fixes #4886] Permissions "Select2" widget not correctly forwarding values to the form</a></li> 
<li> 2019-09-12: gioscarda <a href="http://github.com/geonode/geonode/commit/e1f8a8b5436de0e7e06b81e7abc85bd3597d54cf" target="blank"> [Fixes #4883] monitoring frontened refactoring</a></li> 
<li> 2019-09-12: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/1b29ac9f290cbe9c220cc32a784e51b480e687a6" target="blank"> Bump django-geonode-mapstore-client from 1.4.0 to 1.4.1</a></li> 
<li> 2019-09-11: root <a href="http://github.com/geonode/geonode/commit/31e968b113354a55dc948e795f99386b64c33e13" target="blank"> [Hardening] Check for duplicates links on 'set_all_layers_metadata' management command</a></li> 
<li> 2019-09-11: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b745569fb420322650ecb31e32a28aae1522139f" target="blank"> Bump django-storages from 1.7.1 to 1.7.2</a></li> 
<li> 2019-09-11: afabiani <a href="http://github.com/geonode/geonode/commit/5c5a304220e8e74f7752b36a02ed981611f8e8b4" target="blank"> [Hardening] Javascript deps</a></li> 
<li> 2019-09-11: gioscarda <a href="http://github.com/geonode/geonode/commit/df9c85892851ee24b0d469e020696c7174d43e82" target="blank"> fixing monitoring tests</a></li> 
<li> 2019-09-11: afabiani <a href="http://github.com/geonode/geonode/commit/e11d80ec8915757653369e4faa2e42dc9a1b2de3" target="blank"> [Hardening] Javascript deps</a></li> 
<li> 2019-09-10: capooti <a href="http://github.com/geonode/geonode/commit/5dc3ef0a6478ead4ba5ce7ed0e6eb8f920514cfa" target="blank"> Fixes #4827</a></li> 
<li> 2019-09-10: capooti <a href="http://github.com/geonode/geonode/commit/f5c57b4e76f9c3536b3a83258d4f39d7ba2ce8eb" target="blank"> Fixes #4846 and #4866</a></li> 
<li> 2019-09-10: afabiani <a href="http://github.com/geonode/geonode/commit/6e2634652553a89cf108bda7b44e6e0ecd1f0ae0" target="blank"> [Fixes #4863] Trying to assign permission to more than one users, fails</a></li> 
<li> 2019-09-10: afabiani <a href="http://github.com/geonode/geonode/commit/3b00b30eeb664dce24f315c53b7b55f37f095be6" target="blank"> - Fixing integration test-cases</a></li> 
<li> 2019-09-10: afabiani <a href="http://github.com/geonode/geonode/commit/2cdad844432e5828f5a6269b83f8212d45a914c0" target="blank"> - Fixing integration test-cases</a></li> 
<li> 2019-09-10: gioscarda <a href="http://github.com/geonode/geonode/commit/b5763fe17b7ed2312d29405fea69c6a5cd7c0da2" target="blank"> [Fixes #4861] improved monitoring api filtering</a></li> 
<li> 2019-09-10: afabiani <a href="http://github.com/geonode/geonode/commit/7c196ac048b2137c4f91d8fdd9cc429622698835" target="blank"> - Fixing integration test-cases</a></li> 
<li> 2019-09-10: afabiani <a href="http://github.com/geonode/geonode/commit/9bb5b96871e10706b242d8cc2bf3d35f08142053" target="blank">  - Fixing integration test-cases</a></li> 
<li> 2019-09-10: afabiani <a href="http://github.com/geonode/geonode/commit/7b4b3fbafa5d42f5b29a1a4754de759326350580" target="blank"> [Fixes  #4855] Download links always return whole world bbox</a></li> 
<li> 2019-09-09: afabiani <a href="http://github.com/geonode/geonode/commit/5c534ab3945f16bb51bf466c71a5c65f2f98d158" target="blank"> Bump gn-gsimporter from 1.0.10 to 1.0.12</a></li> 
<li> 2019-09-09: afabiani <a href="http://github.com/geonode/geonode/commit/e392ce1de9d56ffead25744b4e7324f2fa44017c" target="blank"> Bump django-mapstore-adapter from 1.0.6 to 1.0.7</a></li> 
<li> 2019-09-09: gioscarda <a href="http://github.com/geonode/geonode/commit/e093ffe98bf35f26a44bb5813379b81863b9cd34" target="blank"> [Fixes #4849] retrieve cpu and mem usage metric data</a></li> 
<li> 2019-09-08: afabiani <a href="http://github.com/geonode/geonode/commit/c2c33a486623405e368031a5a0ead1193db94034" target="blank">  Fixes #4844</a></li> 
<li> 2019-09-06: capooti <a href="http://github.com/geonode/geonode/commit/6f056430e9b48d38efe16e1c7641b09e6444a625" target="blank"> Fixes #4844</a></li> 
<li> 2019-09-06: gioscarda <a href="http://github.com/geonode/geonode/commit/0ca109fd891e98d1abd0962e08bbd4bc52501533" target="blank"> Added docs related new monitoring requests</a></li> 
<li> 2019-09-06: root <a href="http://github.com/geonode/geonode/commit/329e79d61d2ed16a7bbf941bd76efb0cde602c94" target="blank"> [Hardening] 'set_resource_default_links' avoid hitting GeoServer catalog if it is not needed</a></li> 
<li> 2019-09-06: root <a href="http://github.com/geonode/geonode/commit/065e8385e2ae9fa00744c4325189482ab5cf664b" target="blank"> [Hardening] HTTP connector resilient to SSL invalid certs</a></li> 
<li> 2019-09-06: afabiani <a href="http://github.com/geonode/geonode/commit/be978a07fe954aa42eb4009762766d6b7f261194" target="blank"> [JS] Fix GeoExplorer layer bbox parsing</a></li> 
<li> 2019-09-06: gioscarda <a href="http://github.com/geonode/geonode/commit/1cfedec45dbff9c0de3ee3ad8da09498811a8da9" target="blank"> [Fixes #4842] Monitoring APIs improvements</a></li> 
<li> 2019-09-06: afabiani <a href="http://github.com/geonode/geonode/commit/6cd3ec5b06bbd578694b5298e38138e6150dc194" target="blank"> [Hardening] More readable name for celery files results store / serialized JS async calls on LayerInfo upload prototype</a></li> 
<li> 2019-09-06: afabiani <a href="http://github.com/geonode/geonode/commit/b1ed20de3609ec16692e63b4898df4f9f4b3262e" target="blank"> Bump django-mapstore-adapter from 1.0.5 to 1.0.6</a></li> 
<li> 2019-09-06: afabiani <a href="http://github.com/geonode/geonode/commit/6af327ffbbae4c639e68ce6627f5e5d1f7f50ef8" target="blank"> [Fixes #4831] GeoNode Importer mode not really asynchronous</a></li> 
<li> 2019-09-05: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/d236c79a0dc851abc897861224a8d0d25a2d6889" target="blank"> Bump geonode-oauth-toolkit from 1.1.4.5 to 1.1.4.6</a></li> 
<li> 2019-09-05: root <a href="http://github.com/geonode/geonode/commit/c6cf9fd4140633efaed0bfa2f51030be149cd7d1" target="blank"> [Hardening] Reduce db connection idle timeout / Assert the GeoServer resource actually exists and throw an exception accordingly</a></li> 
<li> 2019-09-05: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/f5b73883ebb7a7884763d053caef4ebac3d66e25" target="blank"> Bump geoserver-restconfig from 1.0.2 to 1.0.3</a></li> 
<li> 2019-09-05: afabiani <a href="http://github.com/geonode/geonode/commit/7ce3d5f163cf74457aaba35c3ea170e00e4bcd93" target="blank"> [Hardening] Reduce db connection idle timeout / Assert the GeoServer resource actually exists and throw an exception accordingly</a></li> 
<li> 2019-09-05: afabiani <a href="http://github.com/geonode/geonode/commit/2e0e6e1fa02b3054c1d33b0c9bc1fa3df9d4420a" target="blank"> [Hardening] Reduce db connection idle timeout / Assert the GeoServer resource actually exists and throw an exception accordingly</a></li> 
<li> 2019-09-04: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/8afb793f03154332524ac4a71f9c425a491e8ad5" target="blank"> [Fixes #4813] Removing a layer is broken - Celery error (#4817)</a></li> 
<li> 2019-09-04: afabiani <a href="http://github.com/geonode/geonode/commit/906cf544bdcca71de3f9088df83c96cab4fb2920" target="blank"> [Fixes #4772] Get rid of deprecated "Publish local map layers as WMS layer group"</a></li> 
<li> 2019-09-04: afabiani <a href="http://github.com/geonode/geonode/commit/257b31d8a13cf11c725df387ca05b5a2845e3bdc" target="blank"> [Hardening] allow monitoring and serviceprocessors to perform internal requests against non verified SSL urls</a></li> 
<li> 2019-09-04: afabiani <a href="http://github.com/geonode/geonode/commit/4c67a952d30ec8039694764e37f48cb8b820280d" target="blank"> [Minor] fix tooltip blinking on home page after bootstrap CSS updates</a></li> 
<li> 2019-08-30: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/241646931524d40bf6b7e40ee33955db71fa2f29" target="blank"> Update .clabot</a></li> 
<li> 2019-09-02: afabiani <a href="http://github.com/geonode/geonode/commit/d86784ce17ae8d70b00edd4a4a9c333aad02ea6b" target="blank"> [Fixes #4809] Static assets still using Select2 3.5 instead of Select2 4</a></li> 
<li> 2019-09-02: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/fa5a5afb28f55ab3afcf86e3b4946ad715f9dd6e" target="blank"> Bump django from 1.11.23 to 1.11.24</a></li> 
<li> 2019-09-02: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/4b455ce821547432a6e0f6e49886ad0f0ba6f23b" target="blank"> updated angular, select2, bootstrap</a></li> 
<li> 2019-09-01: afabiani <a href="http://github.com/geonode/geonode/commit/1bcf487b7cabefb670a2945c71a3aa612c73450a" target="blank">  - Using YARN instead of BOWER (deprecated) and update dependencies</a></li> 
<li> 2019-08-30: Toni <a href="http://github.com/geonode/geonode/commit/6a29e4645818a2becb658a0c1fd79dd7af347e97" target="blank"> Add missing ngCookies when DEBUG_STATIC true</a></li> 
<li> 2019-08-30: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/b452d1b37cf86c7e855fafc28617e8d81622479f" target="blank"> Update .clabot</a></li> 
<li> 2019-08-30: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/494a1faa2a272b402761cd8698234705b3040bbc" target="blank"> Update .clabot</a></li> 
<li> 2019-08-30: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/8d38cd6e76711e74e80ac259e883967819cb5187" target="blank"> Bump django-allauth from 0.39.1 to 0.40.0</a></li> 
<li> 2019-08-29: afabiani <a href="http://github.com/geonode/geonode/commit/254682551e7b30a2afa61fc9501a92a873339a2f" target="blank"> OSGeo Project logo</a></li> 
<li> 2019-08-29: afabiani <a href="http://github.com/geonode/geonode/commit/fd3971d644d8ccc53ba345bc80f201fefc0b5722" target="blank"> Updating "CONTRIBUTING" policies ad instructions</a></li> 
<li> 2019-08-29: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/dfe786c091cb9e71493342bdab45105ffec1b31d" target="blank"> Update .clabot</a></li> 
<li> 2019-08-29: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/d477ca6058f4d0e3ef8891448e5b299599bb1378" target="blank"> Update .clabot</a></li> 
<li> 2019-08-29: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/4eeae3434500271652a9b35abda1f3ff159c2c1e" target="blank"> Update .clabot</a></li> 
<li> 2019-08-29: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/0360aa3199956c8565aaf6a3b0387e8b6b8c2f50" target="blank"> Create .clabot</a></li> 
<li> 2019-08-29: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/20c5409ebd2aafd7b9f37d996139f3d6e1d98c69" target="blank"> Delete signatures</a></li> 
<li> 2019-08-29: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/587b057448059cc88cf8f061dbfe22456859c34f" target="blank"> Create signatures</a></li> 
<li> 2019-08-29: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/e209234733a251203f84b1a78bf89116a185d920" target="blank"> Create CODE_OF_CONDUCT.md</a></li> 
<li> 2019-08-28: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/0cb87a29b97c9f9d1c28399fcc4df5dc17b096a7" target="blank"> Bump sqlalchemy from 1.3.7 to 1.3.8</a></li> 
<li> 2019-08-28: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/97ff15430d68d7528939d81c344b60c62a8b6b40" target="blank"> improved upload error handling</a></li> 
<li> 2019-08-28: Toni <a href="http://github.com/geonode/geonode/commit/f4a50778c8c1b3a22b11db96828ffd17b65734e4" target="blank"> Add sentence regarding minimal requirements</a></li> 
<li> 2019-08-27: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/af48a63557a130771db19c26ac6504f2069f563c" target="blank"> Removed autocomplete from password fields</a></li> 
<li> 2019-08-26: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/3c75de395f4bdaedd6de688f5718a3c68db3f8d5" target="blank"> Bump tqdm from 4.34.0 to 4.35.0</a></li> 
<li> 2019-08-21: gioscarda <a href="http://github.com/geonode/geonode/commit/c797c33cd00a44f6eb30f30d73c72d16e522103b" target="blank"> [Fixes #4759] Merging of the user analytics PR and resolving conflicts</a></li> 
<li> 2019-08-22: afabiani <a href="http://github.com/geonode/geonode/commit/3e8f78999c927a4fb7748a8af3187ccfc21be33e" target="blank"> Update issue templates</a></li> 
<li> 2019-08-22: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/81d51c0c772843f3f62d60dc6141e1b2a61f8699" target="blank"> Update issue templates</a></li> 
<li> 2019-08-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/0b340b977d75ce1fa4b0e2985f362df4e77c6d47" target="blank"> Bump geoserver-restconfig from 1.0.1 to 1.0.2</a></li> 
<li> 2019-08-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/57e52e26cbbb6f49f3cea2009d6c1e03a2c58bc3" target="blank"> Update idna requirement from <2.7,>=2.5 to >=2.5,<2.9</a></li> 
<li> 2019-08-22: afabiani <a href="http://github.com/geonode/geonode/commit/b296be0ff25b5e268476ba87ba85e8529ff24d6f" target="blank"> Bump django-mapstore-adapter to 1.0.5</a></li> 
<li> 2019-08-22: afabiani <a href="http://github.com/geonode/geonode/commit/3e9fd0252a03ad52da867103bd6a90dba8a28fc4" target="blank"> Removing Bower which is deprecated: installing Yarn instead</a></li> 
<li> 2019-08-22: afabiani <a href="http://github.com/geonode/geonode/commit/8429a88d18fb5a7e2113f65f9f589819063b9083" target="blank"> [Docs] Updating GeoNode release tag</a></li> 
<li> 2019-08-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/fe5006642de2dc2f0b3eb7de6d9b2c6407e4bbb3" target="blank"> Bump setuptools from 41.1.0 to 41.2.0</a></li> 
<li> 2019-08-21: afabiani <a href="http://github.com/geonode/geonode/commit/7b702ce26822f58f791fa75f86f45feecefdfca9" target="blank"> Update django-tastypie requirement from <=0.14.0 to <0.15.0</a></li> 
<li> 2019-08-21: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/cbcc28ad2b6705ce0cb799ef220acf9e0323e29d" target="blank"> Bump pytest-bdd from 3.2.0 to 3.2.1</a></li> 
<li> 2019-08-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/f1e82ef125b4afea5ac3e8732c91384c74f05d10" target="blank"> [Fixes #4713] Attributes are not added in layers_attributes table when a layer is uploaded (#4751)</a></li> 
<li> 2019-08-20: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/8159c92a5c7b3c7cbad11524288d391de3c30a6b" target="blank"> Bump pytest-bdd from 3.1.1 to 3.2.0</a></li> 
<li> 2019-08-20: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/c0030957faed29228cb543353ee85733a6e4b443" target="blank"> Bump tqdm from 4.33.0 to 4.34.0</a></li> 
<li> 2019-08-19: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/c053eff58b6f66f6520808af61199c7c189c3c32" target="blank"> Update pyproj requirement from <2.2.2.0,>=1.9.5 to >=1.9.5,<2.2.3.0</a></li> 
<li> 2019-08-19: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/e476d583119845d68ddbbffd91f8664e7905eb5c" target="blank"> Update django-jsonfield requirement from <1.2.1 to <1.3.2</a></li> 
<li> 2019-08-19: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6aecd514586f207a631e86154f6fe15e62696bae" target="blank"> Bump geonode-oauth-toolkit from 1.3.1 to 1.1.4.1rc0 (#4745)</a></li> 
<li> 2019-08-16: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/edcf4f13db1ecf86e7356158f1008fbe2c0a2d8b" target="blank"> Bump kombu from 4.6.3 to 4.6.4</a></li> 
<li> 2019-08-15: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/89f2dd1f884a1561e28e102d7e5d47b2ecf571db" target="blank"> Bump amqp from 2.5.0 to 2.5.1</a></li> 
<li> 2019-08-15: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/abc4ab616365b23ab7d08f75fa6a9eb0307a8f2f" target="blank"> Bump sqlalchemy from 1.3.6 to 1.3.7</a></li> 
<li> 2019-08-14: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/856b8d51d8132e6dc3e94fc6e1f199ef5f57bd40" target="blank"> Bump lxml from 4.4.0 to 4.4.1</a></li> 
<li> 2019-08-14: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/47d452d5637ef8c28a5e53754fdc6495968bceb3" target="blank"> Bump setuptools from 41.0.1 to 41.1.0</a></li> 
<li> 2019-08-14: afabiani <a href="http://github.com/geonode/geonode/commit/3d9384aa74802060024ec360f1ce99fab89a1ad7" target="blank">  - Fix typo</a></li> 
<li> 2019-08-14: capooti <a href="http://github.com/geonode/geonode/commit/4d2e840afa3975cf5d58be98fd2b9f733821a835" target="blank"> Restore base/tests.py</a></li> 
<li> 2019-08-14: capooti <a href="http://github.com/geonode/geonode/commit/e7dcab4b23e18a83773097c754872b5f8472616f" target="blank"> Implement GNIP curated-thumbs</a></li> 
<li> 2019-08-14: afabiani <a href="http://github.com/geonode/geonode/commit/69d1b0ca0bc84ec173d1f4b62e2c7daa2b6f806d" target="blank"> Bump django-geonode-mapstore-client from 1.3.1 to 1.4.0</a></li> 
<li> 2019-08-13: afabiani <a href="http://github.com/geonode/geonode/commit/4ddd60e455fe5e4dc63517e470c45818c410c11a" target="blank">  - Update spcgeonode template docker images</a></li> 
<li> 2019-08-13: afabiani <a href="http://github.com/geonode/geonode/commit/c83673e78bf84a3d5f7b3cffaf09f051f065d910" target="blank"> Bump gn-gsimporter from 1.0.9 to 1.0.10</a></li> 
<li> 2019-08-13: afabiani <a href="http://github.com/geonode/geonode/commit/0515e50079b0e7f0c0e4d06e77635ad602c39c2d" target="blank">  - Update static assets</a></li> 
<li> 2019-08-13: afabiani <a href="http://github.com/geonode/geonode/commit/e73f6d8aaa4765c886bbbe9404f1031871c2ddc5" target="blank"> - Updated Italian translations</a></li> 
<li> 2019-08-13: afabiani <a href="http://github.com/geonode/geonode/commit/10f61d7b53fe27c88a036a3007b59ed5c56cdacc" target="blank">  - Updated French translations</a></li> 
<li> 2019-08-13: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/1fe776186d85af0e623e8ec561905568d6678770" target="blank"> added missing imports</a></li> 
<li> 2019-08-09: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/43d01861e26d6392e864ffb5c65afd1ebd5bbeb8" target="blank"> Bump tqdm from 4.32.2 to 4.33.0</a></li> 
<li> 2019-08-08: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/765f3468664fb5cc20fda33ee558d83fb2553699" target="blank"> added defusedxml  requirements.txt</a></li> 
<li> 2019-08-08: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/5cfe0a1800d155ec6b609bae3d83e1eeb6fdaa75" target="blank"> used defusedxml for parse and fromstring</a></li> 
<li> 2019-08-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/f48779478796acfa8d86d9c1ca10927edefc54b5" target="blank"> Bump mercantile from 1.1.1 to 1.1.2</a></li> 
<li> 2019-08-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/bd2d691a2c0b9437c600da8c9db79926c4c36677" target="blank"> Bump pytest from 4.6.4 to 4.6.5</a></li> 
<li> 2019-08-07: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/546f59f246ed8805f6b3f73c08d198b7ba4c73d1" target="blank"> Bump invoke from 1.2.0 to 1.3.0</a></li> 
<li> 2019-08-06: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/4faf28c5c7aaf58642b44d29cbd0a97e5a99bd49" target="blank"> Bump twisted from 19.2.1 to 19.7.0</a></li> 
<li> 2019-08-01: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b18a2b1499f57018ec466b6aff2dac360e588946" target="blank"> Bump pytz from 2019.1 to 2019.2</a></li> 
<li> 2019-08-01: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/38bbdc7783624f4dcbd444e3b8ce2886e8b5d848" target="blank"> Bump django from 1.11.22 to 1.11.23</a></li> 
<li> 2019-07-31: Joseph Stachelek <a href="http://github.com/geonode/geonode/commit/4786b91c6c7bf57ceccd8ed3af4512d7b1eff207" target="blank"> typo fix</a></li> 
<li> 2019-07-30: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/72692acb3241341fc85d373b3635fa83fec6bb14" target="blank"> Bump coverage from 4.5.3 to 4.5.4</a></li> 
<li> 2019-07-29: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/ff4bebb653b75126dd5b11e2dd333e08fb0dabd0" target="blank"> Bump python-slugify from 3.0.2 to 3.0.3</a></li> 
<li> 2019-07-29: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/f1ccf2d6dd52d19bc393f825a4151f43856b395e" target="blank"> Bump lxml from 4.3.4 to 4.4.0</a></li> 
<li> 2019-07-29: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/8deaf751b255e551a881b4a41af96dc60d565573" target="blank"> Update httplib2 requirement from <0.13.1 to <0.13.2</a></li> 
<li> 2019-07-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/e217ac3eb7f461240a3e1f219258daf8be7cef63" target="blank"> Update stale.yml</a></li> 
<li> 2019-07-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/7ee944edfb175d66cfbc0f5e3fe494046faca256" target="blank"> Create stale.yml</a></li> 
<li> 2019-07-25: afabiani <a href="http://github.com/geonode/geonode/commit/1989f7acac587129ba1a0e3af7682d11deca27c5" target="blank">  - Update django-geonode-mapstore-client</a></li> 
<li> 2019-07-24: Francesco Pennica <a href="http://github.com/geonode/geonode/commit/be2956124c8a284ae05fe7259aab38cdd71c7512" target="blank"> updated some strings in the italian translation</a></li> 
<li> 2019-07-24: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/ace925231a5b8ecff89f5e1d75793081b2e19a9b" target="blank"> Bump beautifulsoup4 from 4.7.1 to 4.8.0</a></li> 
<li> 2019-07-23: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/3be2141e5a0aa01fb89ea1778d58b3766f45de9e" target="blank"> Update django-modeltranslation requirement</a></li> 
<li> 2019-07-23: Sylvain POULAIN <a href="http://github.com/geonode/geonode/commit/16b716e6150158ebc7cd47b1e8d8e11c4b5501e6" target="blank"> Update django.po</a></li> 
<li> 2019-07-23: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b51120d75ad40ae4256766158b98935738baebcf" target="blank"> Bump sqlalchemy from 1.3.5 to 1.3.6</a></li> 
<li> 2019-07-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/6758284856ac9404fbcc81fd6efb3327a5af2f4a" target="blank"> Bump django-polymorphic from 2.0.3 to 2.1.2</a></li> 
<li> 2019-07-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/bc4aa80a43d0448c7f131acbc334f2621ffe3057" target="blank"> Bump pytest-bdd from 3.1.0 to 3.1.1</a></li> 
<li> 2019-07-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/8d1750b9ac15ee2021e3dcbb2b17554574e55347" target="blank"> Bump docker from 3.7.0 to 4.0.2</a></li> 
<li> 2019-07-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/db02ff8ad3f8ac2f64c541811ed3898fbac7b69c" target="blank"> Bump parse-type from 0.4.1 to 0.5.2</a></li> 
<li> 2019-07-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/363c05cc218dbb5468814cc2256ff462e19adf70" target="blank"> Bump amqp from 2.4.2 to 2.5.0</a></li> 
<li> 2019-07-22: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/ba98e4262123d0b5925d2b5090d28fa29f168226" target="blank"> Update httplib2 requirement from <=0.10.3 to <0.13.1</a></li> 
<li> 2019-07-22: afabiani <a href="http://github.com/geonode/geonode/commit/045d07934f45dab2fa2fc4b9f13801d99c8d1d09" target="blank">  - docker-compose uses image: geonode/geonode:latest</a></li> 
<li> 2019-07-20: Vanessa Bremerich <a href="http://github.com/geonode/geonode/commit/91f6d7850c0b0df69f2de47041bcee616c4fca57" target="blank"> typo in map_panels.html, broken link</a></li> 
<li> 2019-07-19: Tobias <a href="http://github.com/geonode/geonode/commit/c7946a9222790ff8ed4775e1df0e0a329204a918" target="blank"> Fixes #4649 Internal proxy handling of relative URL segments breaks MS2</a></li> 
<li> 2019-07-19: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/e883d785ec87e4d67e9ff07ffb67b73836d29a05" target="blank"> Fix geonode docker image version</a></li> 
<li> 2019-07-19: Athanasios Fotis <a href="http://github.com/geonode/geonode/commit/72bbb261ce8f54c359ecde7180a1f075b5f79352" target="blank"> Add some missing translation for Greek locale</a></li> 
<li> 2019-07-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/a1cebc9e2fc97f8696ea3a5d7e916f7c15a30165" target="blank"> Update pyproj requirement from <2.2.1.0,>=1.9.5 to >=1.9.5,<2.2.2.0</a></li> 
<li> 2019-07-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/ad31ecca9b2dac9411a01370478bc86145a555a0" target="blank"> Bump decorator from 4.3.2 to 4.4.0</a></li> 
<li> 2019-07-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b8a2189645b48d4e1f3a4b9183cade3af6aefea9" target="blank"> Update django-modeltranslation requirement</a></li> 
<li> 2019-07-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/68258277a640816935864300bd16d80164ea2498" target="blank"> Bump mercantile from 1.0.4 to 1.1.1</a></li> 
<li> 2019-07-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/5b42acc1b38301cb198da4e80da9c971ddb8961a" target="blank"> Bump sqlalchemy from 1.3.3 to 1.3.5</a></li> 
<li> 2019-07-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/f2a0e8cb3863ef796d7f3401da610070ce91908b" target="blank"> Update elasticsearch requirement from <3.0.0,>=2.0.0 to >=2.0.0,<8.0.0</a></li> 
<li> 2019-07-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/0fafa2575936cdaa0fbad96ca655ff049006ae64" target="blank"> Bump readthedocs-sphinx-ext from 0.6.0 to 1.0.0</a></li> 
<li> 2019-07-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/56a961167d7be18bf9a004f3bc7a2a49fae6f6bc" target="blank"> Bump jdcal from 1.4 to 1.4.1</a></li> 
<li> 2019-06-07: srto <a href="http://github.com/geonode/geonode/commit/9143ca4fcfa5cf8f23b056135be72980660b8247" target="blank"> Make templates use static url set by Django</a></li> 
<li> 2019-07-18: afabiani <a href="http://github.com/geonode/geonode/commit/73e983c38cd865182d9493aad674a7f43f004207" target="blank"> Bump owslib from 0.17.1 to 0.18.0</a></li> 
<li> 2019-07-18: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/18d4ca9ef8639fdf2d53fdd843a750772a5395be" target="blank"> added gannebamm to authors</a></li> 
<li> 2019-07-18: afabiani <a href="http://github.com/geonode/geonode/commit/2f05453ff6f37e126be7a3b9793d2f7f19ba9875" target="blank"> [Fixes #4656] When DEBUG=False configured remote services should be PROXY ALLOWED</a></li> 
<li> 2019-07-17: afabiani <a href="http://github.com/geonode/geonode/commit/04a5235ac54a5f682330605109d9fa2bccd12371" target="blank"> [Fixes #4653] Use GeoServer 2.15.2</a></li> 
<li> 2019-07-17: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/600595dfe850d278ebf1756d3281dad93e254e4a" target="blank"> Bump pytest from 4.6.3 to 4.6.4</a></li> 
<li> 2019-07-17: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/c168b66c7ca3e1e7281adfa5d04e07ff71ed77e0" target="blank"> Bump kombu from 4.4.0 to 4.6.3</a></li> 
<li> 2019-07-17: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/6490b09f734f848030aff3f13869805f8fe25220" target="blank"> Bump django-cors-headers from 2.5.2 to 3.0.2</a></li> 
<li> 2019-07-17: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/83eaa0a1d858e378cc2b599be9665cec1e94de35" target="blank"> Update xmltodict requirement from <=0.10.2 to <0.12.1</a></li> 
<li> 2019-07-16: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/070310736a573188a9104b4854dbbea4671ab86e" target="blank"> Bump flake8 from 3.7.7 to 3.7.8</a></li> 
<li> 2019-07-16: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/c1dfb4d334248c22e1302a623bc55e682a84d6fe" target="blank"> Update mock requirement from <=2.0.0 to <4.0.0</a></li> 
<li> 2019-07-15: afabiani <a href="http://github.com/geonode/geonode/commit/e19140cd2f81659ce40fada13623252ea60bd02e" target="blank">  - Bump to version 2.10.1 'maintenance' 0</a></li> 
<li> 2019-07-15: afabiani <a href="http://github.com/geonode/geonode/commit/92ed66c7d6e20147414e9a28a3f63f43ba0b76fd" target="blank"> [Fixes #4639] Switch library "gsconfig" to "geoserver-restoconfig"</a></li> 
<li> 2019-07-12: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/d771ddbd15d46bb5aa8bea30d0b9411440c33186" target="blank"> Add PULL_REQUEST_TEMPLATE.md</a></li> 
<li> 2019-07-12: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/32472d6105b1f2f2896fd53b54fc40d3d0d36fa5" target="blank"> Bump oauthlib from 3.0.1 to 3.0.2</a></li> 
<li> 2019-07-12: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/6026c69bb76c28e0a28228a789e1ff50da70702d" target="blank"> Bump lxml from 4.3.3 to 4.3.4</a></li> 
<li> 2019-07-11: Sylvain POULAIN <a href="http://github.com/geonode/geonode/commit/a7d254363bc2710eed950e395862d707ce804bf8" target="blank">  Geoserver doesn't restart with https</a></li> 
<li> 2019-07-10: prbordon <a href="http://github.com/geonode/geonode/commit/a2703137c2091033853fb3e1482983b11caf97dc" target="blank"> spanish translation update</a></li> 
<li> 2019-07-10: afabiani <a href="http://github.com/geonode/geonode/commit/468fb0281f27a3ff561b975a3c21bbfe8b6e640b" target="blank"> [Social Account Settings] LinkedIn profile fields updated</a></li> 
<li> 2019-07-10: afabiani <a href="http://github.com/geonode/geonode/commit/f8b1bf596ee2ded41e509b0ab76d9fda82d6062b" target="blank">  - Updating README.md links to the doc</a></li> 
<li> 2019-07-10: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/0b6e64f822c3cd0ccf024955a8d8f4619de89776" target="blank"> Align nginx tag value driven by .env variable (#4624)</a></li> 
<li> 2019-07-10: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/adebc2ee6865a799b2fa9da3de266167603bbe56" target="blank"> Align nginx tag value driven by .env variable (#4623)</a></li> 
<li> 2019-07-10: afabiani <a href="http://github.com/geonode/geonode/commit/a6f418d56d2867732ade9dbb5a8b5bff0ba81704" target="blank">  - 2.10 stable release</a></li> 
<li> 2019-07-08: afabiani <a href="http://github.com/geonode/geonode/commit/5bcbe01386a8fb1b1a4bdf46aebac59fccaa7862" target="blank">  - Make sure the DB is available</a></li> 
<li> 2019-07-08: afabiani <a href="http://github.com/geonode/geonode/commit/c3b0e85a8bcc4ecfb162f4805fc474a5c3dfd66d" target="blank">  - Make sure we have updated migrations</a></li> 
<li> 2019-07-08: afabiani <a href="http://github.com/geonode/geonode/commit/004f2c57973dfeaf0f0c6165647920748c95306c" target="blank"> - Make sure the DB is available</a></li> 
<li> 2019-07-08: afabiani <a href="http://github.com/geonode/geonode/commit/b2404d678bd7210327ec78a3970f968bb6afe84b" target="blank">  - Make sure the DB is available</a></li> 
<li> 2019-06-25: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/b97e0a10b99d18961a6afccc9e85fa7869bffb55" target="blank"> Try spcgeonode with mapstore2 and postgis</a></li> 
<li> 2019-06-10: afabiani <a href="http://github.com/geonode/geonode/commit/91b7ebab4a59f738e3f68551b2aa022f9ce9b63f" target="blank"> [SPCgeonode] GeoServer 2.14.3</a></li> 
<li> 2019-06-10: afabiani <a href="http://github.com/geonode/geonode/commit/c4a29c3a518eee8f404af8e2c03d10495487c548" target="blank"> - Fix travis</a></li> 
<li> 2019-03-08: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/ced835ebccd6e49fbb98fcbba86ba4b52d20b216" target="blank"> Test standard docker setup with geonode-selenium</a></li>

## [2.10](https://github.com/GeoNode/geonode/tree/2.10.0-release) (2019-07-10)

 - **[MapStore2 Client v1.3.1](https://github.com/geosolutions-it/geonode-mapstore-client/releases/tag/v1.3.1)**

 - **[MapStore2 v2019.01.01](https://github.com/geosolutions-it/MapStore2/releases/tag/v2019.01.01)**

 - **[Implemented enhancements](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+label%3Afeature+milestone%3A2.10)**

 - **[Security fixes](https://github.com/GeoNode/geonode/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aclosed+milestone%3A2.10+label%3Asecurity+)**

 - **[New Docs](https://github.com/GeoNode/geonode/pulls?q=is%3Apr+is%3Aclosed+new-docs+milestone%3A2.10)**

 - **[Fixed Critical Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+label%3Ablocker+milestone%3A2.10)**

 - **[Fixed Major Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A2.10+label%3Amajor)**

 - **[Closed Issues](https://github.com/GeoNode/geonode/issues?q=is%3Aissue+is%3Aclosed+milestone%3A2.10)**

## [Full Changelog](https://github.com/GeoNode/geonode/compare/2.8.1...2.10.0-release)

<li> 2019-07-10: afabiani <a href="http://github.com/geonode/geonode/commit/a6f418d56d2867732ade9dbb5a8b5bff0ba81704" target="blank">  - 2.10 stable release</a></li> 
<li> 2019-07-09: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/d38143129b62017b41d3138752a14226319278fa" target="blank"> Bump psutil from 5.6.1 to 5.6.3</a></li> 
<li> 2019-07-09: afabiani <a href="http://github.com/geonode/geonode/commit/3c669d6bdb720413713a8fd86cc160da0576ac16" target="blank">  - GeoServer Render Thumbnails using the correct auth headers</a></li> 
<li> 2019-07-09: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/5f766d06496507f2b7c9f123be5d0083263aa7ed" target="blank"> Bump pillow from 6.0.0 to 6.1.0</a></li> 
<li> 2019-07-09: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/f25d59f2a233562b9d6243b28ed5b5cc7b1f65c6" target="blank"> Bump tqdm from 4.31.1 to 4.32.2</a></li> 
<li> 2019-07-09: afabiani <a href="http://github.com/geonode/geonode/commit/068ac0b3b199c7d2b96f571900572fdda19a89d5" target="blank">  - Improve Monitoring Request Filter Logging</a></li> 
<li> 2019-07-09: afabiani <a href="http://github.com/geonode/geonode/commit/4c7ac25c0d86e8b66da507dc66a2f846283c17c8" target="blank">  - use correct resolved object when saving metadata</a></li> 
<li> 2019-07-09: afabiani <a href="http://github.com/geonode/geonode/commit/4d07ff44a8e26624a672ba3c0e394ca239931945" target="blank">  - use correct resolved object when saving metadata</a></li> 
<li> 2019-07-08: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/a443472e697d449e55608a5ec398e18635210bd4" target="blank"> Bump pytz from 2018.9 to 2019.1</a></li> 
<li> 2019-07-08: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/d92142ceb6b9a88e862512fe74e6b922847f04b3" target="blank"> Bump splinter from 0.10.0 to 0.11.0</a></li> 
<li> 2019-07-08: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/b86b881c0ad409ebcf00ddd6038de9cc5008d5d2" target="blank"> switched to latest tags for docker images to</a></li> 
<li> 2019-07-05: Sylvain POULAIN <a href="http://github.com/geonode/geonode/commit/47ff46a932e23c4d2c6f67043ee09457cf06f53d" target="blank"> Update Dockerfile</a></li> 
<li> 2019-07-04: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/c72c6edf6ffa46b2f59207d10205734f571f2109" target="blank"> [Security] Bump django from 1.11.21 to 1.11.22</a></li> 
<li> 2019-07-02: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b7ed7d94a31e0c841b37f0a6438bce9082eb2f03" target="blank"> Bump pytest-django from 3.4.8 to 3.5.1</a></li> 
<li> 2019-07-02: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/f36e6f02dcbd110936cc47ba12496b21de8b44c9" target="blank"> Bump python-slugify from 3.0.1 to 3.0.2</a></li> 
<li> 2019-07-02: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b7816c0f47ff572c25bbe3c65bf2c789d2ea83cf" target="blank"> Bump readthedocs-sphinx-ext from 0.5.17 to 0.6.0</a></li> 
<li> 2019-07-02: Sylvain POULAIN <a href="http://github.com/geonode/geonode/commit/12585dbea3f25baa752f92f03268bf1d1fbd4845" target="blank"> Solve letsencrypt ssl error</a></li> 
<li> 2019-07-01: Toni <a href="http://github.com/geonode/geonode/commit/0d7820133b29d295f4bf8ec3b6028c949db4bfcf" target="blank"> Added numpy for SPC</a></li> 
<li> 2019-07-01: Toni <a href="http://github.com/geonode/geonode/commit/116937fd5671cbbfa58c956b5d91642052d33380" target="blank"> Added numpy to requirements.txt</a></li> 
<li> 2019-07-01: Toni <a href="http://github.com/geonode/geonode/commit/9d85bff6f9f8ec6ae6313e19129f84a3015a71e0" target="blank"> Simplify pygdal installation</a></li> 
<li> 2019-06-30: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/f47f752f50423516b410547ec01f22aed2527f2e" target="blank"> Add dev mode with regular Docker (#4514)</a></li> 
<li> 2019-06-30: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/0bd23aeff27b9f15e09d649aeca3561e114186af" target="blank"> fixed typos on start</a></li> 
<li> 2019-06-29: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/2ba5c757d6afcb372245c44d667a24a103e17b7b" target="blank"> added ansible to docs</a></li> 
<li> 2019-06-28: Lorenzo Pini <a href="http://github.com/geonode/geonode/commit/9d833bdab50b0b0f9cf304099f5ec2902d7d0b5b" target="blank"> Add vim text editor, fix typos</a></li> 
<li> 2019-06-28: gioscarda <a href="http://github.com/geonode/geonode/commit/80254c8bd1804055d8a3018c245d48ebeaf93dd9" target="blank"> [docs] fixing typos in basic index</a></li> 
<li> 2019-06-28: gioscarda <a href="http://github.com/geonode/geonode/commit/2337d30a89cffd72af7be336a746436086c2133c" target="blank"> [docs] GeoNode Project Themes</a></li> 
<li> 2019-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/52ad47df89548d44b81076c5e13da8c432068bca" target="blank"> [Docs] Getting Started part 4</a></li> 
<li> 2019-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/78ae0d2f2276501c888979f3189357b9db9459de" target="blank"> [Docs] Getting Started part 3</a></li> 
<li> 2019-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/aa47b5b67d2b299fe8c85527a4a75f5112be82c7" target="blank"> [Docs] Getting Started part 2</a></li> 
<li> 2019-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/717a2af63515b960c8f12f054fccc9ed99c1fd78" target="blank"> [Docs] Getting Started part 1</a></li> 
<li> 2019-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/af04b522eccadb851816927cba605ae5a1436606" target="blank"> [Docs] Removing misleading contents</a></li> 
<li> 2019-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/4de9be391e6bf366e1ddb00127e07a4c871dd4f1" target="blank"> [Docs] Removing misleading contents</a></li> 
<li> 2019-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/a93d802a8828028175ba63d8a8e9031a8017ff21" target="blank"> [Docs] Administering GeoNode: OAuth2 Access Tokens management</a></li> 
<li> 2019-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/cbe54051c4a27993f003850d1f95896b1d42acfb" target="blank"> [Docs] finalize geonode-project debug setup and startup section</a></li> 
<li> 2019-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/4f0f03935a513d79f2acb4f23f6bacd9df48b819" target="blank"> [Docs] Monitoring</a></li> 
<li> 2019-06-27: capooti <a href="http://github.com/geonode/geonode/commit/951a0bbd60e0dbeb24fc0276b074e237fc4958bd" target="blank"> Implement #4429</a></li> 
<li> 2019-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/bb5cb130f14e9f165a957d396cd55503ee232ba6" target="blank"> [Docs] Manage the base metadata choices using the admin panel</a></li> 
<li> 2019-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/0b1ceb25ea1d0bb0756c36fef508e38fe6e83cff" target="blank"> [Docs] Announcemnts and Dismissals</a></li> 
<li> 2019-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/bc55bec6bd07a7b96d25d00c8eefb68e89288c4c" target="blank">  - Add AnnouncementPermissionsBackend to default AUTHENTICATION_BACKENDS</a></li> 
<li> 2019-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/68daf73ec172b58511d8e3d99e649c645e99f537" target="blank"> [Closes #4584] Allow admins to decide if the Topic Category should be mandatory or not</a></li> 
<li> 2019-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/96f9f009c35b3ec075d2c8e346468354d505db51" target="blank"> [Closes #4584] Allow admins to decide if the Topic Category should be mandatory or not</a></li> 
<li> 2019-06-27: gioscarda <a href="http://github.com/geonode/geonode/commit/29be5c7dc5441a357e498f7de707a0363fd812ad" target="blank"> [docs] added groups management sections</a></li> 
<li> 2019-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/765ab23e51e7ba7db17052ecd5228feb98323d52" target="blank"> [Static assets] Refresh/update static assets</a></li> 
<li> 2019-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/bb345cbf1da5d568e6b41422f95ea78cdab7affd" target="blank"> [Dependencies] Updating monitoring static assets in order to remove vulnerabilities</a></li> 
<li> 2019-06-26: Lorenzo Pini <a href="http://github.com/geonode/geonode/commit/f8b7cde4894af90edfc528ccf4e81d672bcd7ae1" target="blank"> Update index.rst</a></li> 
<li> 2019-06-26: gioscarda <a href="http://github.com/geonode/geonode/commit/21891310afd344bb6f86e77f89fba042cebaaf8b" target="blank"> [docs] group categories and group profiles</a></li> 
<li> 2019-06-26: afabiani <a href="http://github.com/geonode/geonode/commit/7e702790b27064b3601ff67129aa099a8ea16f71" target="blank"> [Fixes #4579] Set Thumbnail tool broken (GeoExplorer only)</a></li> 
<li> 2019-06-26: afabiani <a href="http://github.com/geonode/geonode/commit/f2decb275572aaa16d311634f9f5f47889ba3e7d" target="blank">  - Allow members_only announcements also</a></li> 
<li> 2019-06-26: afabiani <a href="http://github.com/geonode/geonode/commit/88ca841ac449a5173e70df1904cc8b6234a2a3aa" target="blank"> [Docs] Manage Profiles, Layers, Maps and Documents from the Admin panel</a></li> 
<li> 2019-06-26: afabiani <a href="http://github.com/geonode/geonode/commit/40dd12008fa4e9e10c332fae680e22cca22ac3ba" target="blank">  - Show Contact Roles again on the Profile Admin panel</a></li> 
<li> 2019-06-26: afabiani <a href="http://github.com/geonode/geonode/commit/96605c45945531cd3645c17272d3aa23b8b14268" target="blank"> [Docs] Group based advanced data workflow</a></li> 
<li> 2019-06-26: afabiani <a href="http://github.com/geonode/geonode/commit/0ea2149a920154b4fe76cec0dac99d60722ecb9f" target="blank"> [Fixes #4575] Group Category summary page does not show associated group details</a></li> 
<li> 2019-06-26: gioscarda <a href="http://github.com/geonode/geonode/commit/bc8ef4072a79e4c1c08e8fd26c1fa0e870e90822" target="blank"> [docs] manage users from admin</a></li> 
<li> 2019-06-25: geosolutions <a href="http://github.com/geonode/geonode/commit/fccb3763cbcd4ee49f927e554a74840999849455" target="blank"> [Optimization] optimize thumb generation algo</a></li> 
<li> 2019-06-25: gioscarda <a href="http://github.com/geonode/geonode/commit/73391b499ed4937bdb2c0e3ba663707e7c1526fd" target="blank"> [Docs] fixing typos</a></li> 
<li> 2019-06-25: gioscarda <a href="http://github.com/geonode/geonode/commit/f3b6675135a24e3c629d31cbae4c01aef9beb2f1" target="blank"> accessing admin panel, change admin password</a></li> 
<li> 2019-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/92370ad8fa2c98f694c76462e0080de1282fc580" target="blank"> [Docs] Administering > Simple Theming</a></li> 
<li> 2019-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/dfbca3e74fed57247d81771486a97c5c6d5702d9" target="blank"> [Docs] Administering > Simple Theming (work in progress)</a></li> 
<li> 2019-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/f116fdeb539a866a793b8a9741a67f2fec5c7cd0" target="blank"> [Docs] Administering > Simple Theming (work in progress)</a></li> 
<li> 2019-06-25: gioscarda <a href="http://github.com/geonode/geonode/commit/4778c81ff8b573a81af42b643794bb5e5095824e" target="blank"> fixing typos</a></li> 
<li> 2019-06-25: gioscarda <a href="http://github.com/geonode/geonode/commit/c526019576ec1a2ad10e023c54e316dc1e11dd7d" target="blank"> remote service types in user guide</a></li> 
<li> 2019-06-25: Lorenzo Pini <a href="http://github.com/geonode/geonode/commit/f1f8c4e581f310750632bc36c2d88ad3b35ff452" target="blank"> Typos in installation document</a></li> 
<li> 2019-06-25: Toni <a href="http://github.com/geonode/geonode/commit/7f0e247f14714e089a6a8dfb2b8a16128102e163" target="blank"> Fixed SESSION_EXPIRED_CONTROL_ENABLED to True</a></li> 
<li> 2019-06-25: gioscarda <a href="http://github.com/geonode/geonode/commit/222ad1fa7139fe87074292f7011992ff7228b56a" target="blank"> linking docs with resources explanation in user guide</a></li> 
<li> 2019-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/b70c93d8ff21fbe7e0ae1468f5409e612de62e68" target="blank"> [Docs] Administering index structure / Change the default langs</a></li> 
<li> 2019-06-25: gioscarda <a href="http://github.com/geonode/geonode/commit/bdb352bce8c3a6fe6d16fa408e05a4d0c559712f" target="blank"> fixing typos</a></li> 
<li> 2019-06-25: gioscarda <a href="http://github.com/geonode/geonode/commit/11d2771528ec5bda43be4c5415c30faab39b9557" target="blank"> exif images docs</a></li> 
<li> 2019-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/61ceb60f24d46d602046e1dc78ba265ac9ce75b1" target="blank"> [Docs] About GeoNode / SPC GeoNode</a></li> 
<li> 2019-06-25: gioscarda <a href="http://github.com/geonode/geonode/commit/97de82d58bdf2d3046deed6e05afa4f8a78e6cf3" target="blank"> publishing data usage docs</a></li> 
<li> 2019-06-24: Angelos Tzotsos <a href="http://github.com/geonode/geonode/commit/beeeaa966f69b7a5c31f37543be6dc4fc4e492c0" target="blank"> Reclassifying requirements based on Ubuntu available packages</a></li> 
<li> 2019-06-24: afabiani <a href="http://github.com/geonode/geonode/commit/f97efcdb499045e0884e8e5f279109aa8bec8f82" target="blank">  - fix travis</a></li> 
<li> 2019-06-24: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/6d1873f95a8df9a34c8cb39e395910f7d6eb2ec1" target="blank"> Update django-jsonfield requirement from <=1.0.1 to <1.2.1</a></li> 
<li> 2019-06-24: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/83a87c79faac8f74f48cc17c86a42788829482a8" target="blank"> Bump owslib from 0.16.0 to 0.17.1</a></li> 
<li> 2019-06-24: afabiani <a href="http://github.com/geonode/geonode/commit/07d7dad3bca9e5b3e982933c7ff19029bb75045c" target="blank"> [hardening] make sure we do not fall into dangeruos huge loops</a></li> 
<li> 2019-06-24: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/b9bfff87f39637510355bc0bd55b6cb86f38b38a" target="blank"> Bump django-activity-stream from 0.7.0 to 0.8.0</a></li> 
<li> 2019-06-24: afabiani <a href="http://github.com/geonode/geonode/commit/123b870b6b5c149ef5d3779affb068f6764ea8fa" target="blank"> Bump Django MapStore Adapter to version 1.0.3</a></li> 
<li> 2019-06-21: Toni <a href="http://github.com/geonode/geonode/commit/400218f5519dc21ffbdcb2594a8a059d5fb4a9f3" target="blank"> Fixed Typos</a></li> 
<li> 2019-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/d5371dd9c81ed2b25ef3020c2ce5fcb8064d9fb7" target="blank">  - GeoServer Proxy should allow PUBLIC_LOCATION to fetch security headers too</a></li> 
<li> 2019-06-21: gioscarda <a href="http://github.com/geonode/geonode/commit/f113074c146c9b2369c03449e08661031c7bb9be" target="blank"> managing_maps</a></li> 
<li> 2019-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/729cad5635c9e962e3789b441d4b84e89cc4e8b5" target="blank">  - Fix travis tests</a></li> 
<li> 2019-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/3d72c5e1faebfada80805de2b4290ce67238d09d" target="blank">  - Fix GeoServer version to 2.14.3</a></li> 
<li> 2019-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/bb609b1196e4d06d9762f5a3f01154c4690ee212" target="blank">  - Travis-selenium tentative fix</a></li> 
<li> 2019-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/782e583320193717078df87682bd500c3d3bc5c3" target="blank"> [Fixes #4552] Improve/fix thumbnail generation for Layers and Maps at creation time</a></li> 
<li> 2019-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/e379994d2d1ae45f0295deca34c0fa17ac3126fd" target="blank"> [Fixes #4553] Exception thrown when trying to upload features with non UTF-8 encoding</a></li> 
<li> 2019-06-20: afabiani <a href="http://github.com/geonode/geonode/commit/cd733408a60e5d911138861c1cf444bed2d4b332" target="blank"> - Travis-selenium tentative fix</a></li> 
<li> 2019-06-20: afabiani <a href="http://github.com/geonode/geonode/commit/70838d180cc6532b5807ee43d4f8d0b0d7185605" target="blank">  - Travis-selenium tentative fix</a></li> 
<li> 2019-06-19: capooti <a href="http://github.com/geonode/geonode/commit/d62722a558319c35a651d72c73103e2575273523" target="blank"> Fixes #4534</a></li> 
<li> 2019-06-19: afabiani <a href="http://github.com/geonode/geonode/commit/239d6c8767bd0957a638961fc8ab2adb8c56e2bb" target="blank">  - spcgeonode settings tune up</a></li> 
<li> 2019-06-19: afabiani <a href="http://github.com/geonode/geonode/commit/09c7ab9e5c7639d82b5c16678ea88e2be2e5f218" target="blank"> [Fixes #4547] "set_all_layers_metadata" deletes Thumbnail metadata links</a></li> 
<li> 2019-06-19: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/3c10f4c30453b66426d2d1be9a0b58af962f6fd9" target="blank"> Bump pytest from 4.3.1 to 4.6.3</a></li> 
<li> 2019-06-18: afabiani <a href="http://github.com/geonode/geonode/commit/5e993d86851333ae6d497430f79369a1ebdefc22" target="blank"> [Fixes #4545] MapStore2 print button broken with 1.1 client release</a></li> 
<li> 2019-06-18: afabiani <a href="http://github.com/geonode/geonode/commit/283fe98afa96b8dec7f8b534f5df5f77c997c54a" target="blank"> [Fixes #4543] Enforce GeoNode REST service API security</a></li> 
<li> 2019-06-18: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/ceb422ed5a0a95224cac6aeed13eacad3b242b7d" target="blank"> [Closes #4532] Add search filters for groups and group categories (#4533)</a></li> 
<li> 2019-06-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/14a6be48582e4ffcd213408acade37eebb0987a5" target="blank"> [Security] Bump twisted from 18.9.0 to 19.2.1</a></li> 
<li> 2019-06-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/7d74b0c5ca954f502e07fe924e65298909f9a7a1" target="blank"> Update pyproj requirement from <=1.9.5.1,>=1.9.5 to >=1.9.5,<2.2.1.0</a></li> 
<li> 2019-06-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/e63594e99f959ee33db09648fba1052fcf7f6086" target="blank"> [Security] Bump urllib3 from 1.24.1 to 1.24.2</a></li> 
<li> 2019-06-18: afabiani <a href="http://github.com/geonode/geonode/commit/8c8d6a85303b6b9bf1503d10395ab16723159109" target="blank"> [Fixes #4541] Wrong permissions inconsistency message when changing layer permisions</a></li> 
<li> 2019-06-18: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/4b7dbff0ea884c9aa5f9ce45ad1eab9dc7ccb083" target="blank"> Use python_requires</a></li> 
<li> 2019-06-18: afabiani <a href="http://github.com/geonode/geonode/commit/fd8b9d382481bde0ec8f580867ae929fca28e617" target="blank"> [Fixes #4538] Guardian returns the whole list of permissions associated with a resource.</a></li> 
<li> 2019-06-18: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/36357ff3f0b36bdf0190bbae51a1254af7480174" target="blank"> Bump pillow from 5.4.1 to 6.0.0</a></li> 
<li> 2019-06-17: dependabot-preview[bot] <a href="http://github.com/geonode/geonode/commit/d22e2fe97976b02cfad983eaf0c33fdc5a8f2538" target="blank"> Bump setuptools from 40.8.0 to 41.0.1</a></li> 
<li> 2019-06-17: afabiani <a href="http://github.com/geonode/geonode/commit/c6e45f8cb395af51eeae7a88bbb542ff4c64394f" target="blank">  - updating requirements: django_geoexplorer-4.0.43</a></li> 
<li> 2019-06-17: afabiani <a href="http://github.com/geonode/geonode/commit/922cd5f658af8515bbf69c3b2fdcf4140f0e4bdc" target="blank"> [Closes #4519] Option to regenerate resource links at migration or not</a></li> 
<li> 2019-06-15: afabiani <a href="http://github.com/geonode/geonode/commit/637aec80e5c1f3d789f07c3ca11b34769b4ffe93" target="blank">  - updating requirements</a></li> 
<li> 2019-06-15: afabiani <a href="http://github.com/geonode/geonode/commit/ef245346919937c8eb127590253b89b8a681bde1" target="blank">  - Fix get started link on index page</a></li> 
<li> 2019-06-15: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/ec7b63a3320a5725f3166a99bd68686d62122f2d" target="blank"> removed opensource heart</a></li> 
<li> 2019-06-15: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/2712adba406860997420553061f8005a1ddd9b2a" target="blank"> added image again</a></li> 
<li> 2019-06-15: Toni <a href="http://github.com/geonode/geonode/commit/4e3d6ca25575232eb9dc62c396fc42cb60946403" target="blank"> Added logo, correct 404 to new docs.</a></li> 
<li> 2019-06-14: afabiani <a href="http://github.com/geonode/geonode/commit/b209e6781da1c0f6189c6b3175e8c3cfd280e4dc" target="blank"> Fix build</a></li> 
<li> 2019-06-14: afabiani <a href="http://github.com/geonode/geonode/commit/e94244e249d320fba99d78907cbe3ab701fc4580" target="blank">  - Minor Adjustments to README and settings</a></li> 
<li> 2019-06-14: Toni <a href="http://github.com/geonode/geonode/commit/bda3a92a5f1fc2fdd4f4603c2b4897dfc95b668c" target="blank"> Added t-book to authors.</a></li> 
<li> 2019-06-13: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/5548dec2836bb5ecc050eae2542fe634c8e7ea40" target="blank"> Add new geotiff for Travis CI (#4507)</a></li> 
<li> 2019-06-13: Toni <a href="http://github.com/geonode/geonode/commit/30371e50458550197dcc70c28c10192bae1129bb" target="blank"> Push Travis again.</a></li> 
<li> 2019-06-13: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/5aad4d53201aa3c4a657ac5883abafabbdfa400e" target="blank"> changed basemap for thumbnails to wikimedia, fixes #4459</a></li> 
<li> 2019-06-13: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/1f4347410575fe694fa994027ce1627a22669a8c" target="blank"> Fixes: #4478</a></li> 
<li> 2019-06-13: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/818652247825405bf951a5de7b49c3fb5e92c715" target="blank"> defuzzyied the translations</a></li> 
<li> 2019-06-13: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/5db9e43093c13209e168d08a290725a7a2a00144" target="blank"> Update docker-compose.yml</a></li> 
<li> 2019-06-13: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/31ee5a3b020e0e56ba2cf341c053a8bd85e07a8c" target="blank"> fixes #4354</a></li> 
<li> 2019-06-13: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/1be8c64a421483a92ba069c235c62b4e96ddb024" target="blank"> added postgis 10.x, importer, pgdumper for geo/nogeo dbs</a></li> 
<li> 2019-06-13: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/2952d4c6dd6c4e948a7bbcaf8eae149b738c2763" target="blank"> merge with global master (#11)</a></li> 
<li> 2019-06-12: afabiani <a href="http://github.com/geonode/geonode/commit/d194c7255baa82c1bdc18a34bd2312af83c09b4a" target="blank"> [Fixes #4487] Issue adding remote services - FAILED - could not convert string to float: EPSG:4326</a></li> 
<li> 2019-06-13: Toni <a href="http://github.com/geonode/geonode/commit/5cf836fe112a99d50ccea355c04a80dacc9bd146" target="blank"> Updated arabic translation</a></li> 
<li> 2019-06-13: Toni <a href="http://github.com/geonode/geonode/commit/aecb39ebe384ad58d432fd0ba67cdd4368cce998" target="blank"> Fixed OpenSource Image</a></li> 
<li> 2019-06-12: florian <a href="http://github.com/geonode/geonode/commit/8e4383d33c2ed67746c0334ae79ae234ff6c60d0" target="blank"> fixes geoserver auth button #4335</a></li> 
<li> 2019-06-12: florian <a href="http://github.com/geonode/geonode/commit/8fee085822155ee9b6055ef7bc82a7460637189a" target="blank"> fixes geoserver auth button #4335</a></li> 
<li> 2019-06-12: Toni <a href="http://github.com/geonode/geonode/commit/945bfd1cbe86edce2614e20f0d1fdd7b47fc9a84" target="blank"> Fixed Readme Header</a></li> 
<li> 2019-06-12: ppasq <a href="http://github.com/geonode/geonode/commit/64c285c7609b1c1a019191dfb1498bdcf4286b33" target="blank"> Make the menu item Invite users available for authenticated users only</a></li> 
<li> 2019-06-12: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/115f1fd481b458c91844a05beb407747d5d6b568" target="blank"> Close #4472</a></li> 
<li> 2019-06-12: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/175763056be483ea7143d085c292fe02dda29dc4" target="blank"> Add ISSUE_TEMPLATE.md</a></li> 
<li> 2019-06-12: ppasq <a href="http://github.com/geonode/geonode/commit/add3df79f6c40039c4d034fa256ac7d0ed066704" target="blank"> Make the user message disappear after 5 secs</a></li> 
<li> 2019-06-12: ppasq <a href="http://github.com/geonode/geonode/commit/ab9da36991be39e68f95b8c588eebefb5b167393" target="blank"> Fix less file not aligned to corresponding css</a></li> 
<li> 2019-06-09: afabiani <a href="http://github.com/geonode/geonode/commit/c815569ad10024cd1f1dfb06d82c1660463cf0dd" target="blank"> - Docker optimizations</a></li> 
<li> 2019-06-07: afabiani <a href="http://github.com/geonode/geonode/commit/1a51a48a0f106b6b3bd491de6d4794cbb2907294" target="blank">  - Fix travis</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/e2d40c2e379c299f68607eb3de80874db4374884" target="blank"> [Links] Fix Metadata Catalogue Records Update</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/cda82f9e1e25498c4522a178bbbd88040956e09f" target="blank">  - Fix travis</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/58e9c4cfac57cffe00e42179ee58b7633d9ff4dc" target="blank"> [Links] fix download links bbox generation</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/e29ab255145c6c3e73faba2940d31d968a2e384a" target="blank">  - Travis fix</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/e0ce2bc78ee88364c89cc6047bf7cd3172f066b9" target="blank">  - Travis fix</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/6007ea56f1fde0fa4d4eaab31c3a8e5f8de6c41f" target="blank">  - Travis fix</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/bdde105e61a1fa28742f5982fab0a0c4e781bdd2" target="blank"> [Links] Remove old instances breaking the command execution</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/b8dddf9dadc1bbbb7701e9586a33df0b5d08bb56" target="blank"> [Proxy Hotfix] self.username overrides user param</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/a8d76b638711c2abdc9b55bc86d3c68693904a4e" target="blank"> [Settings] Make client hooksets auto-configurable via env GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/d405258c7c3c7630f21f9ef2f6368256f32b1ca2" target="blank"> [Settings] Make client hooksets auto-configurable via env GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/77b041ee8f47189dc9ba3248d6c28015c141820f" target="blank"> [Settings] Make client hooksets auto-configurable via env GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY</a></li> 
<li> 2019-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/8f3b065acdf5bd89b3c4fd1569951b4a2309e30c" target="blank"> [Settings] Make client hooksets auto-configurable via env GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY</a></li> 
<li> 2019-06-06: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/2ddeb046edb101371470461fca8386f539e36691" target="blank"> Update requirements.txt</a></li> 
<li> 2019-06-06: srto <a href="http://github.com/geonode/geonode/commit/0ac6ec3ae8d51e7ff6e9df49b9217f62279b5f80" target="blank"> Store filename returned by storage API</a></li> 
<li> 2019-06-05: Tobi <a href="http://github.com/geonode/geonode/commit/488882efba28fd6215e5a1fb0f02717075c0b8dd" target="blank"> Use Django file storage API to construct media URL</a></li> 
<li> 2019-06-05: afabiani <a href="http://github.com/geonode/geonode/commit/d99d7005bca41d8a2bb79ecc74a5b96bcb342f96" target="blank"> [Settings] Removing refuses</a></li> 
<li> 2019-06-05: afabiani <a href="http://github.com/geonode/geonode/commit/a193d45eadde4edd54eaf00ef7193fd4f5084534" target="blank"> [Monitoring] relax host name constraint</a></li> 
<li> 2019-06-03: afabiani <a href="http://github.com/geonode/geonode/commit/45e35a0defd5c6c31e8435d93c8ff2bfe0897396" target="blank">  - Travis fixes</a></li> 
<li> 2019-06-03: afabiani <a href="http://github.com/geonode/geonode/commit/aca042e405f8f5e71a96b773e8be59b373077df6" target="blank">  - Improve docker build</a></li> 
<li> 2019-06-03: afabiani <a href="http://github.com/geonode/geonode/commit/155ac7c71ad1728265ef7105e5b625f9b64b0c90" target="blank"> [Fixes #4450] Thumbnails on layers not showing</a></li> 
<li> 2019-06-03: afabiani <a href="http://github.com/geonode/geonode/commit/f0ff9d71b163f8acdccd06f0df998645814d9569" target="blank"> [Settings] Restoring /gs to /geoserver by default</a></li> 
<li> 2019-05-30: afabiani <a href="http://github.com/geonode/geonode/commit/08ce1b9982a0c1ad165a53c44d2cf01984d3d673" target="blank">  - MapStore2 Client as default</a></li> 
<li> 2019-05-30: afabiani <a href="http://github.com/geonode/geonode/commit/a610b5c2bbe04bb089f10b8d0dd1e832d614fcbb" target="blank">  - MapStore2 Client as default</a></li> 
<li> 2019-05-29: afabiani <a href="http://github.com/geonode/geonode/commit/0c314508311b8bf8072672a3a0843d4af919fd82" target="blank">  - MapStore2 Client as default</a></li> 
<li> 2019-05-30: afabiani <a href="http://github.com/geonode/geonode/commit/4b07f181f9b36ea4698b2b317ebc602f03b954df" target="blank"> [Fixes #4447] Database locked when using sqlite/spatialite databases</a></li> 
<li> 2019-05-30: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/6f2e83fdad7d8b9dcd8cc9cfb49cf8201b62083c" target="blank"> fixes #4440 correct float on people profile small screens</a></li> 
<li> 2019-05-30: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/bbd4839e6c6b763637e26b7d802ccbd80c63232f" target="blank"> Fixes: #4443 issues translations on index</a></li> 
<li> 2019-05-29: afabiani <a href="http://github.com/geonode/geonode/commit/6eb66451e96961e094d6a58982c79c20fd0c2342" target="blank">  - Removing contrib apps deps</a></li> 
<li> 2019-05-29: afabiani <a href="http://github.com/geonode/geonode/commit/bfa712f3a408a9c0c91fd3035da726ce9983d751" target="blank"> [Monitoring] Decimal digits on model</a></li> 
<li> 2019-05-28: afabiani <a href="http://github.com/geonode/geonode/commit/7513820894b8b9d7bdd8384bbb5ca3e5a0ee412b" target="blank"> [Fixes #4437] [Monitoring] collect_metrics often timeouts</a></li> 
<li> 2019-05-28: afabiani <a href="http://github.com/geonode/geonode/commit/c417076c18c64d4dea72740fea3cae7feae05af8" target="blank"> [Fixes #4352] TemplateSyntaxError at trans in backups/confirm_cancel.html</a></li> 
<li> 2019-05-28: afabiani <a href="http://github.com/geonode/geonode/commit/c247a43cadc354b1c4942d0d5b519d0a332d09b8" target="blank">  - Fix travis</a></li> 
<li> 2019-05-28: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6e9e887b231794f059fb4861d3e07437fa5edd2d" target="blank"> [Fixes #4428] refactor linkedin field extraction (#4435)</a></li> 
<li> 2019-05-28: afabiani <a href="http://github.com/geonode/geonode/commit/06523308a69b0f52a65d6a9df29c81f803af9042" target="blank">  - simplify the PR changes and get rid of UPDATE_THUMBS_ON_STYLE_CHANGE additional setting</a></li> 
<li> 2019-05-28: afabiani <a href="http://github.com/geonode/geonode/commit/19db6505fde47923d441ae8a79042dd58d4dcdc4" target="blank"> [Minor] Hardening GeoNode checks and settings</a></li> 
<li> 2019-05-28: afabiani <a href="http://github.com/geonode/geonode/commit/2e3d49d3cb411ccab05dce6edcc060cc4edf154d" target="blank"> [Minor] Hardening GeoNode checks and settings</a></li> 
<li> 2019-05-27: afabiani <a href="http://github.com/geonode/geonode/commit/6c940c2e8b1a1496db5c0173e9a5b95f5b4f009e" target="blank"> - Fix Tests</a></li> 
<li> 2019-05-27: afabiani <a href="http://github.com/geonode/geonode/commit/7efd502d7bec6105ead8680363e96c155cdf7b62" target="blank"> [Minor] Hardening GeoNode checks</a></li> 
<li> 2019-05-27: afabiani <a href="http://github.com/geonode/geonode/commit/72ee5f7b16f4a6d8766f2f87ee87c3fcdcddc7ed" target="blank">  - Fix Tests</a></li> 
<li> 2019-05-27: afabiani <a href="http://github.com/geonode/geonode/commit/203e3f0ba3db6969619d20a4379316716cf72670" target="blank"> GeoNode Cleanup and Test Coverage</a></li> 
<li> 2019-05-27: afabiani <a href="http://github.com/geonode/geonode/commit/7f9dea1b9af0ff2a33d8b1301cf12cec384516fb" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / database_shards,worldmap,geotiffio,geosites extracted</a></li> 
<li> 2019-05-27: afabiani <a href="http://github.com/geonode/geonode/commit/95d39812df2674b86a0ec28ac68d21f57cab4c1d" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / favorite,exif,monitoring promoted / slack,nlp,mp removed</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/0237cbcfe99038053ac2677186dbfeaa43c8d25d" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/c4b8d66b73ca8ccdd1e0065475bd2fd8db70453e" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/60c87cecdcb6e79df9d820e405c933ea009d6abd" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/7dd69716d713871acfb1859d1543e160c6815706" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/a950caf6580d8b62d3a26204655d3ab48fbb0282" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/2854d1f6fa3aa394ea4d4ad79874c3cba127ab52" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/f7c3e7b800fa12cf7696d6e2ce3a490ea61b4f47" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / metadataxsl promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/497910b99ee7226208d7f44757ab4a407f812041" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / metadataxsl promoted</a></li> 
<li> 2019-05-23: capooti <a href="http://github.com/geonode/geonode/commit/5a5a29a21ca7928c300e7b3718147540b5c38d0c" target="blank"> Add UPDATE_THUMBS_ON_STYLE_CHANGE setting - refs #4092</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/6e5cf59c3f8c60a8e63137a3e5562eb390bbcf3c" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/a0a7bc4fc18da934b10b3233d41b78fe8ea9fd18" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: Jonathan Doig <a href="http://github.com/geonode/geonode/commit/7b2877adf31fa5e07eee8d344a199988a487e78e" target="blank"> Fix TemplateSyntaxError at trans</a></li> 
<li> 2019-05-23: Jonathan Doig <a href="http://github.com/geonode/geonode/commit/c14cf2a7335c6933a6453de8dfe1f7cb803525aa" target="blank"> Fix Geonode issue 4352</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/388129f389b14aa25bfc771a9a4eab4f90e15337" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / createlayer promoted</a></li> 
<li> 2019-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/cad085b5b2eb4a7bf623a0b0d0af9b9b75a5e5d3" target="blank"> [Ref #4311] GNIP: Contrib apps cleanup on GeoNode / metadataxsl promoted</a></li> 
<li> 2019-05-22: afabiani <a href="http://github.com/geonode/geonode/commit/26ff8db8498b3d89822329d19bcbba6b9ac29f66" target="blank"> [Minor Improvements] Few more checks with the email backend</a></li> 
<li> 2019-05-22: afabiani <a href="http://github.com/geonode/geonode/commit/1e455412b9acefa799922b674b22aef454f1cfb6" target="blank"> [Fixes #4424] Reverting back to GeoServer 2.14.2</a></li> 
<li> 2019-05-21: afabiani <a href="http://github.com/geonode/geonode/commit/de34e4f422667bc8e14c43fb2b0ba71a6de63487" target="blank">  - Convert pinax templates bodies to HTML</a></li> 
<li> 2019-05-21: geosolutions <a href="http://github.com/geonode/geonode/commit/dad94b27e0d04ab37f65af38a996f6f2ddfef8ea" target="blank">  - Custom PINAX Email Backend: allows html notifications</a></li> 
<li> 2019-05-20: afabiani <a href="http://github.com/geonode/geonode/commit/4d92e12308fc9a35e52df13ad7518c57128b10d4" target="blank"> [Fixes #4417] 'ows_api' for GetCapabilities, should provide public urls anyway</a></li> 
<li> 2019-05-20: afabiani <a href="http://github.com/geonode/geonode/commit/d87e50538c95d9e2ff66e1f38905bf7daa570539" target="blank"> [Fixes #4418] General SLD management misbehavior</a></li> 
<li> 2019-05-19: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/5592a808b0e92a297401ee8d531045aae08b1865" target="blank"> Update requirements.txt</a></li> 
<li> 2019-05-19: afabiani <a href="http://github.com/geonode/geonode/commit/5a5bcb2769436888ec086151ca0736a4c00d53d8" target="blank"> [Hardenining] Avoid hard failure if GeoServer resource is not reachable</a></li> 
<li> 2019-05-19: afabiani <a href="http://github.com/geonode/geonode/commit/d12f8fe78ab5749c91cd03484808ce51967bb4c3" target="blank"> [Closes #4415] Upgrade PyCSW version to 2.4.0</a></li> 
<li> 2019-05-17: afabiani <a href="http://github.com/geonode/geonode/commit/1a9dad94851c291eec48dc613bd1d752873320ce" target="blank"> [Fixes #4410] Avoid re-writing thumbnail every time a Layer is saved</a></li> 
<li> 2019-05-17: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/3531c9c798483c7333af891d5cba785d4390c319" target="blank"> Revert "Allow for https as public protocol"</a></li> 
<li> 2019-05-17: afabiani <a href="http://github.com/geonode/geonode/commit/28556926d6c1b3bd7fba5c4d5f88a311d31dc17f" target="blank"> [Closes #4408] Expose 'settings' variable to env</a></li> 
<li> 2019-05-17: afabiani <a href="http://github.com/geonode/geonode/commit/0ab2b1d5c0c1d10eaf2655fe3e59554a94e87d9f" target="blank"> [Monitoring] timeout decorator to collect_metrics management command; avoids stucking on db connections</a></li> 
<li> 2019-05-17: Jonathan Doig <a href="http://github.com/geonode/geonode/commit/3974ee7fde4ea8df8fb1b24cee221f263dee9c77" target="blank"> Updates as requested for Geonode PR 4403</a></li> 
<li> 2019-05-17: Jonathan Doig <a href="http://github.com/geonode/geonode/commit/8c8e3adb15ad00f49152a79326e895d963121f45" target="blank"> Infer protocol from port if defined</a></li> 
<li> 2019-05-17: afabiani <a href="http://github.com/geonode/geonode/commit/c6356bf3daa17469c294f15c940a3b5452b3a820" target="blank"> [Monitoring] timeout decorator to collect_metrics management command; avoids stucking on db connections</a></li> 
<li> 2019-05-16: afabiani <a href="http://github.com/geonode/geonode/commit/856705bc5b7ccdb909245dff49d6fc0e13fce4c1" target="blank"> [Close #4405] [GeoNode 2.10] Upgrade GeoServer version to 2.15.1</a></li> 
<li> 2019-05-16: afabiani <a href="http://github.com/geonode/geonode/commit/3cf053bd961c8bb46c6b427576d1f5fe96dfa7fd" target="blank"> [Fixes #4404] Performance issue with resource base apis</a></li> 
<li> 2019-05-16: afabiani <a href="http://github.com/geonode/geonode/commit/3a6ebefc6f4b554564fbc2a06ad1d7b3ae89a3c8" target="blank"> [Maps Model] Removing CharField 200 length limitation</a></li> 
<li> 2019-05-16: Jonathan Doig <a href="http://github.com/geonode/geonode/commit/94e3a4d6770d55c383a7fdd53bd0f905c1ba5a21" target="blank"> Add default GEONODE_LB_PROTOCOL to docker-compose files</a></li> 
<li> 2019-05-16: Jonathan Doig <a href="http://github.com/geonode/geonode/commit/0c27f4033565040d25845e03c5e240331794fda9" target="blank"> Allow for https as public protocol</a></li> 
<li> 2019-05-15: afabiani <a href="http://github.com/geonode/geonode/commit/c2f0e6d37e8732e368fc05b7eef05a3b7aab534e" target="blank"> [Minor fix] Do not break the map if cannot read the syles from GeoServer</a></li> 
<li> 2019-05-15: afabiani <a href="http://github.com/geonode/geonode/commit/12bd465a3009d7eecf66eea788a69387f353b3cd" target="blank"> [Minor updates] Aligning with 2.8.2</a></li> 
<li> 2019-05-15: afabiani <a href="http://github.com/geonode/geonode/commit/c6090ad36cf467a79fd29670b3b287fff9adc3b0" target="blank"> [Release] GeoNode 2.8.1</a></li> 
<li> 2019-05-15: afabiani <a href="http://github.com/geonode/geonode/commit/775bb113ffd28e57ee9515fda712fbf26aac500d" target="blank"> [Release] Preparing 2.8rc1</a></li> 
<li> 2019-05-14: geosolutions <a href="http://github.com/geonode/geonode/commit/ed8fa37f112b718aba14ea7a09bf7dfbecf9d4ae" target="blank"> [Cleanup] cleanup settings and exposing some of them as env variables</a></li> 
<li> 2019-05-14: geosolutions <a href="http://github.com/geonode/geonode/commit/5b42deaf4a3b679ef6ce915a92537f72c984d230" target="blank"> [Cleanup] cleanup settings and exposing some of them as env variables</a></li> 
<li> 2019-05-14: geosolutions <a href="http://github.com/geonode/geonode/commit/9330b9e66a0f8642d67cb295beae8d7cb69119df" target="blank"> [Cleanup] cleanup settings and exposing some of them as env variables</a></li> 
<li> 2019-05-13: Hayden Elza <a href="http://github.com/geonode/geonode/commit/d121f4f00c8c7f434e240e765ddc485ae31155ea" target="blank"> Spelling</a></li> 
<li> 2019-05-13: afabiani <a href="http://github.com/geonode/geonode/commit/9cb15fc8ab1f6abc8450f71a51d59c80ce99d6aa" target="blank">  - Removing geonode.contrig.sites app by default</a></li> 
<li> 2019-05-13: afabiani <a href="http://github.com/geonode/geonode/commit/26d862c0b0efca1d1ef3b7a5ec6b00b1d3de62d5" target="blank"> [Minor fix] do not overwrite thumbnail if it already exists</a></li> 
<li> 2019-05-10: geosolutions <a href="http://github.com/geonode/geonode/commit/8a746f19f495ee34eff52f120da34f920da7be07" target="blank"> [Template] minor improvements</a></li> 
<li> 2019-05-10: afabiani <a href="http://github.com/geonode/geonode/commit/e41d5c4edc1a0fa9b83172d90d39c723bf617417" target="blank">  - More Theme options</a></li> 
<li> 2019-05-10: afabiani <a href="http://github.com/geonode/geonode/commit/9a56c992fa4397c1128a4b03ec93dc2b1cdb45cb" target="blank"> [Themes] Add more nav customization options</a></li> 
<li> 2019-05-10: geosolutions <a href="http://github.com/geonode/geonode/commit/e26017ece8d9c602922da50b27cdea33ebcb4ccf" target="blank"> [Template] typo</a></li> 
<li> 2019-05-10: afabiani <a href="http://github.com/geonode/geonode/commit/da891dd437d2ed0eba6fa054c46cb5a8e461ec82" target="blank"> [Themes] Add more nav customization options</a></li> 
<li> 2019-05-10: afabiani <a href="http://github.com/geonode/geonode/commit/dc6e1f2c912d0045fa07689967e6b4a02a22ec5e" target="blank"> [Minor fixes] settings typos and fixoauth mgt commands</a></li> 
<li> 2019-05-10: afabiani <a href="http://github.com/geonode/geonode/commit/9c5311178e1983ec1d415d5ebdf8aedca2810da9" target="blank"> [Minor fixes] settings typos and fixoauth mgt commands</a></li> 
<li> 2019-05-10: afabiani <a href="http://github.com/geonode/geonode/commit/19743509eda6b6304a538314927413a2d573ea5b" target="blank"> [Minor improvements] Allow requests get to use timeouts / expose Monitoring variables</a></li> 
<li> 2019-05-09: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/f053c136517028957bdfe4de15f62f7ad10f3c2c" target="blank"> Update local_settings.py.geoserver.sample</a></li> 
<li> 2019-05-09: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/cd3940113abb05556da437c2b4818939c9462275" target="blank"> revert wrong setting</a></li> 
<li> 2019-05-09: afabiani <a href="http://github.com/geonode/geonode/commit/3f047692923432a91122f192537de1f7dcdbc2d6" target="blank"> [Minor optimizations] settings X_FRAME_OPTIONS allow localhost / add geoserver local services paths to geoserver proxy</a></li> 
<li> 2019-05-08: afabiani <a href="http://github.com/geonode/geonode/commit/99c548e8636a31fc70b2a3f2dad8a74b48f350bb" target="blank">  - [Minor fix] Proxy will attach access_token only if remote netloc matches the local one</a></li> 
<li> 2019-05-06: Angelos Tzotsos <a href="http://github.com/geonode/geonode/commit/46f8c6fee12b4ad6d97700d2e0b051a61c6a3d77" target="blank"> Update Greek translations</a></li> 
<li> 2019-05-04: Angelos Tzotsos <a href="http://github.com/geonode/geonode/commit/c736c8f70ac3ffad74693a66bb97d8c89fe5965d" target="blank"> Regenerate Greek translations</a></li> 
<li> 2019-05-04: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/60f245afbae308f82d6c7aca6f67ecf8ec39c96c" target="blank"> Remove refuses from index.html</a></li> 
<li> 2019-05-03: afabiani <a href="http://github.com/geonode/geonode/commit/8addcc9a20410f741198bcd76eb5825bdae895fb" target="blank"> [Closes #4384] Add a Cookies & Privacy policy customization section to GeoNode Themes</a></li> 
<li> 2019-05-02: afabiani <a href="http://github.com/geonode/geonode/commit/a4be20299cb4bedf3e950be30e062892f09d8621" target="blank"> [Minor Refactoring] Avoid code duplication: centralize 'create_geoserver_db_featurestore' on geoserver helpers classes only</a></li> 
<li> 2019-05-02: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/61355744536cdae6a8afda9490468555d087d166" target="blank"> Rebuild static files, missing in #4380</a></li> 
<li> 2019-04-30: afabiani <a href="http://github.com/geonode/geonode/commit/c96b64413cb6bb1cf35c40c3996bcd4023a75a68" target="blank"> [Minor fix] Trying to parse geoserver error messages in a cleanest way</a></li> 
<li> 2019-04-30: Toni <a href="http://github.com/geonode/geonode/commit/0617a238cd434703b1961d082a765c65c91d7d0b" target="blank"> Delete dsgvo.html</a></li> 
<li> 2019-04-30: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/3815dcf71975d8d43c67312e35b8bc3411525c01" target="blank"> fixes profile text overflow UI glitch #4376</a></li> 
<li> 2019-04-29: afabiani <a href="http://github.com/geonode/geonode/commit/9de35045b64ee34cd8964a7f9b08534374058091" target="blank"> [Minor] Improves Proxy response error status message</a></li> 
<li> 2019-04-29: afabiani <a href="http://github.com/geonode/geonode/commit/04c529f19300e78fa52142640b2f503d7f1a13f7" target="blank"> [Minor fix] allow sld POST request since the user might want to create a new style</a></li> 
<li> 2019-04-29: afabiani <a href="http://github.com/geonode/geonode/commit/460ccfebe9d1a35aaf8da220cb9514cc48d55303" target="blank"> [Closes #4377] Introduce a 'style-check' endpoint for style edit permission checks</a></li> 
<li> 2019-04-29: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/8bdeac9f6b77b162749ec643d6871f7303f79e79" target="blank"> update geosites contrib app to be work with geonode 2.10 (#4287)</a></li> 
<li> 2019-04-28: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/4f85448269764ad2826630db84506bc022d352b9" target="blank"> Fixes: #4374, added missing quote to trans</a></li> 
<li> 2019-04-28: Toni <a href="http://github.com/geonode/geonode/commit/5af9a76987f6256153d999f2ea3e6492fc4aa6b9" target="blank"> Update German translation</a></li> 
<li> 2019-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/83386a0651c037b1161ba79fb6deab1c588625b6" target="blank"> [Closes #4369] List of strings without trans tags and not listed in .po file</a></li> 
<li> 2019-04-25: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/8bbec88810b6aaf74ff7b622cefb21102e0935dc" target="blank"> Fix #4368 Announcement text layout overlaps on index.html</a></li> 
<li> 2019-04-24: afabiani <a href="http://github.com/geonode/geonode/commit/a89adfe1bb4a426b4ce9dbe88244af4471756ed8" target="blank">  - fix test case</a></li> 
<li> 2019-04-23: capooti <a href="http://github.com/geonode/geonode/commit/92e8a511a0bd9172d3c143a7a1abc5cda43accd6" target="blank"> Bump django-geoexplorer-worldmap 4.0.67</a></li> 
<li> 2019-04-23: afabiani <a href="http://github.com/geonode/geonode/commit/ea1a5288a6dcebf7145b3cd57d3b178eb5f3c735" target="blank">  - django-geoexplorer 4.0.42: Fixing GeoServerStyleWriter plugin</a></li> 
<li> 2019-04-23: afabiani <a href="http://github.com/geonode/geonode/commit/73b4c93ad3927845c77d67b3b1ee41ccedf14944" target="blank"> [Fixes #4357] tags do not support unicode text</a></li> 
<li> 2019-04-23: afabiani <a href="http://github.com/geonode/geonode/commit/c59a2a1e9b0d450d444768179c2473091c6b13cb" target="blank">  - Fix adv settings docs titeling</a></li> 
<li> 2019-04-23: afabiani <a href="http://github.com/geonode/geonode/commit/1966ff98d6a46d2f354eea48d70deb214828df35" target="blank">  - minor integrity checks</a></li> 
<li> 2019-04-23: afabiani <a href="http://github.com/geonode/geonode/commit/917fc732c33a73b8b96b97fef4052c73f70ce193" target="blank">  - Fixes/improx as per reviews</a></li> 
<li> 2019-04-23: afabiani <a href="http://github.com/geonode/geonode/commit/34db2f36a7c9b355a09ca48faf8c66e45ae1dee9" target="blank">  - pin urllib3 version conflicting with geonode-oauth-toolkit requirements</a></li> 
<li> 2019-04-18: afabiani <a href="http://github.com/geonode/geonode/commit/87799fddab2302145c43525635f07f701c121fc4" target="blank">  - Bump version to 2.10rc5</a></li> 
<li> 2019-04-15: Angelos Tzotsos <a href="http://github.com/geonode/geonode/commit/72e707c8651a42078718012617d52244b5021a9a" target="blank"> Settings fix for geosites, patch from debian package</a></li> 
<li> 2019-04-15: Angelos Tzotsos <a href="http://github.com/geonode/geonode/commit/888c2bc791d942c2ab2c4fd68c9fa8a57e3edb92" target="blank"> Fixed missing debian changelog records</a></li> 
<li> 2019-04-12: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/3b4e5199b15bdcbd7a62e467b6e7fa5f341b94e0" target="blank"> #4338 fix thumbnail creation with different bbox</a></li> 
<li> 2019-04-10: afabiani <a href="http://github.com/geonode/geonode/commit/2ece112b160e4ee1b6126e5697ca8c5eb105a682" target="blank">  - Geonode logo as favicon</a></li> 
<li> 2019-04-10: afabiani <a href="http://github.com/geonode/geonode/commit/dd195902828ab04aa021bb0562e2f4c4ab1adf17" target="blank">  - Text fixes</a></li> 
<li> 2019-04-10: afabiani <a href="http://github.com/geonode/geonode/commit/7f886744b91b810de57b00d2b6ef1080ead3b842" target="blank"> [Fixes #4321] GeoNode is not able to show errors properly on upload / [Closes #4241] Upload failure: saved_layer is None</a></li> 
<li> 2019-04-09: afabiani <a href="http://github.com/geonode/geonode/commit/834ef7133a948b8bccd7d9ce51b8cdf7736e37d6" target="blank">  - Tentative fix tests</a></li> 
<li> 2019-04-09: afabiani <a href="http://github.com/geonode/geonode/commit/2c154ac312e948dd9701f0253a4b8d81cee8bbcd" target="blank"> [Issue #4325] List of documentation improvements</a></li> 
<li> 2019-04-09: afabiani <a href="http://github.com/geonode/geonode/commit/92bfa6000cb32cbcafe81a056e7425b39cae1a49" target="blank">  - Docs: updates to advanced settgins and docs version</a></li> 
<li> 2019-04-09: afabiani <a href="http://github.com/geonode/geonode/commit/6e7e069dad32bd7f25c2c2e4d6b68475af0ba1b6" target="blank">  - Add 'Syncronize button immediately' to Layers List too</a></li> 
<li> 2019-04-08: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/237baac627138b115033a8508f2fd69c7a5a14bd" target="blank"> add outh test</a></li> 
<li> 2019-04-09: afabiani <a href="http://github.com/geonode/geonode/commit/65fbd8f935a8967bb7bbb21b8bcff05e4f82fb0b" target="blank">  - Added docs for DELAYED SECURITY settings also</a></li> 
<li> 2019-04-09: afabiani <a href="http://github.com/geonode/geonode/commit/3700784d3848e3eb83273c2ac40ad1365b26f5e2" target="blank">  - SESSION_EXPIRED var to False by Default</a></li> 
<li> 2019-04-08: afabiani <a href="http://github.com/geonode/geonode/commit/53a8967bb822a5af36a4dd0ca647bc4ed167e1c5" target="blank">  - Restore session expire messages, but using cookie storeage instead of session</a></li> 
<li> 2019-04-06: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/0772da3938e10d7796c880a9c33f27216bc6ed62" target="blank"> #4348 fix failing read_the_docs</a></li> 
<li> 2019-04-05: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/29606ea2ff0b3cd53fa7e22c2d01a48017e645f5" target="blank"> 8 KB buffer for uwsgi</a></li> 
<li> 2019-04-04: afabiani <a href="http://github.com/geonode/geonode/commit/8bc52a6541fea748a7a1bc527bdb318bb58c54d1" target="blank">  - Fix test cases</a></li> 
<li> 2019-04-04: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/05c70a3171217a6f56664b74598cf34730e01ecb" target="blank"> 8 KB buffer for spc uwsgi</a></li> 
<li> 2019-04-04: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/9c23a37ef35a70dbddcc5d28b332233014fcc665" target="blank"> Set SESSION_EXPIRED_CONTROL_ENABLED for SPC</a></li> 
<li> 2019-04-04: afabiani <a href="http://github.com/geonode/geonode/commit/c1eec2b62b5c419cf681e22bf4ee4b5656423e95" target="blank"> [Fixes #4322] SESSION_EXPIRED_CONTROL_ENABLE=True breaks GeoNode</a></li> 
<li> 2019-04-04: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/fc5d0f7c56d68d11c42777de09a23fcdff12edfb" target="blank"> Polish tests</a></li> 
<li> 2019-04-04: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/4959946c981a1a6671642eef8e72e53a075f5601" target="blank"> Remove failing test</a></li> 
<li> 2019-04-04: afabiani <a href="http://github.com/geonode/geonode/commit/af5c82dc45ef753d1150950d7bf4f1cfff869145" target="blank"> [Fixes #4322] SESSION_EXPIRED_CONTROL_ENABLE=True breaks GeoNode</a></li> 
<li> 2019-04-04: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/d7f1bb87fa43f81e099c5295402674149dc3cd21" target="blank"> GeoServer web UI url default fixed</a></li> 
<li> 2019-04-03: afabiani <a href="http://github.com/geonode/geonode/commit/1cd5b901e02e114b77d546a3eef9260a602682a2" target="blank"> GNIP: Improvements to GeoNode Layers download links - original dataset option in a migration</a></li> 
<li> 2019-04-03: afabiani <a href="http://github.com/geonode/geonode/commit/b9430e8b008fa5fdab08e7b56ff8cede212667f8" target="blank"> [GNIP #3944] Make GeoFence efficient for GeoNode instances with a large number of layers</a></li> 
<li> 2019-04-03: afabiani <a href="http://github.com/geonode/geonode/commit/1405a332f4ebd67ea70b7f642a2149c1246c5025" target="blank"> [GNIP #3944] Make GeoFence efficient for GeoNode instances with a large number of layers</a></li> 
<li> 2019-04-03: afabiani <a href="http://github.com/geonode/geonode/commit/427cb95b94d0076b769f256b9c571959c66ad1c9" target="blank"> [Fixes #4333] Upload from GUI doesn't handle projection properly</a></li> 
<li> 2019-04-03: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/5219096705b98eb48f36a7cf6820deb39964dca9" target="blank"> Change conversion to 5-digits round</a></li> 
<li> 2019-04-03: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/4a2f83927aa99b673ecfb0b7c7ed2e7c37cfa215" target="blank"> Convert for integer comparison</a></li> 
<li> 2019-04-03: afabiani <a href="http://github.com/geonode/geonode/commit/f3c799d9cb2467159273380a8069e5fa05607ae0" target="blank"> [Fixes #4333] Upload from GUI doesn't handle projection properly</a></li> 
<li> 2019-04-01: afabiani <a href="http://github.com/geonode/geonode/commit/c1fb6f58c55366d5a9b8a466059994606977e1d0" target="blank"> [GNIP #3944] Make GeoFence efficient for GeoNode instances with a large number of layers</a></li> 
<li> 2019-03-29: afabiani <a href="http://github.com/geonode/geonode/commit/10cee6f0e78c92e2063180289efbbc5fb71915a5" target="blank">  - Show Original Data Set links also</a></li> 
<li> 2019-03-29: afabiani <a href="http://github.com/geonode/geonode/commit/1e26c5ea4745f8823612bdd0157d1f3382d68369" target="blank"> [Closes #4323] Layers Download Links need some care</a></li> 
<li> 2019-03-28: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/27feb5d433fe7d76b3a8e0b16b5dcf89325c5454" target="blank"> Remove awesome_slugify and all references to it, replace with python-slugify which is a newer and still active replacement</a></li> 
<li> 2019-03-28: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/a803592824abd59e3e08fad2f097131dafce7d83" target="blank"> Revert "add async_thumbnail to improve upload time"</a></li> 
<li> 2019-03-26: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/b5a267b69c8c77aa6ea090231465cbba8e9f8c5c" target="blank"> Allow Travis CI to run on the 2.20.x branch</a></li> 
<li> 2019-03-26: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/b6c8520da247bc79fc7a3e819dc0afae2981b4b8" target="blank"> Remove unused dependency coreschema</a></li> 
<li> 2019-03-26: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/d5593747fc763cf5d8f1043a558c59dcd13fbc2a" target="blank"> Upgrade django-polymorphic from version 1.3.1 to 2.0.3</a></li> 
<li> 2019-03-26: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/f638911563e7d1e9db3fbe9c616c835abb43850d" target="blank"> Upgrade Pillow from version 3.3.2 to version 5.4.1</a></li> 
<li> 2019-03-26: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/8b4c32a81370eb498ee90e635c2086e100606525" target="blank"> Fix GeoServer wait for Postgres</a></li> 
<li> 2019-03-26: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/ce8a05ff65aa59cede4c452bd1315cf21074f696" target="blank"> Update pinax-notifications from 4.1.0 to 5.0.3.</a></li> 
<li> 2019-03-26: afabiani <a href="http://github.com/geonode/geonode/commit/43539d8a46fd5e1c903e7e683fe144d6c4058d1d" target="blank"> [Closes #4312] Remove GeoGig and api_basemaps contrib apps integrated stuff</a></li> 
<li> 2019-03-22: afabiani <a href="http://github.com/geonode/geonode/commit/66bc00c69cf7df3fd8a094f4350f03e8aefe761d" target="blank">  - [Closes #4308] Allow users to refresh layer attributes and statistics through both GeoNode UI and Management Commands</a></li> 
<li> 2019-03-21: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/55268f6481d7fd16694203a424f91366bea7a15c" target="blank"> Upgrade invoke from 0.22.1 to 1.2.0</a></li> 
<li> 2019-03-21: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/8ffc3a4341cbf4757da6dfc16e305e0bac8d0cb3" target="blank"> Upgrade oauthlib from version 2.1.0 to version 3.0.1</a></li> 
<li> 2019-03-21: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/cf3c0c1ea4e42d1680a837dcb24115752cb0ab2d" target="blank"> Add 2.20 to the list of branches that Travis CI runs tests against.</a></li> 
<li> 2019-03-21: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/758076657af9898658aa90e513fd36631851829a" target="blank"> Remove nose as we're not using it for any of the tests anymore.</a></li> 
<li> 2019-03-21: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/6cd379273ac8ef60eea3c704d3da067ac8bc36c2" target="blank"> Update TEST_RUN_INTEGRATION_BDD to install geckodriver and run firefox as headless.</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/4a35c729be05c99ecaa3213cf440b85f22da2715" target="blank"> Flake8 fixes.</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/1065af46ad6182a0c4f792ba0289beeae9ef784a" target="blank"> Ensure selenium with the firefox geckodriver web driver is available for BDD tests.</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/17149830b73f614f95dd737efa60968643ebbecc" target="blank"> Resolve failing BDD tests.</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/4b651dfeb0194e41c21b8df1f232dc65bb46d1eb" target="blank"> The latest version of splinter no longer supports phantomjs, use the default firefox driver instead.</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/a4974affe0cf0cc489df30f765fa4ca19c496843" target="blank"> Don't install specific versions of the testing dependencies for BDD tests, use what we already have in requirements.txt</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/03c1b5a38ae0ff77e541f43fc7ac9d8d5bcedbb3" target="blank"> Resolve remaining flake8 issues.</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/80c5b1b79e47a8d3c57fb141e3f78d0c28d61283" target="blank"> Resolve all W605 invalid escape sequence flake8 errors.  https://lintlyci.github.io/Flake8Rules/rules/W605.html</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/f9d6e403b20bfce33b64783052b4da5552110769" target="blank"> Newer versions of flake8 are stricter and have more findings.  Use autopep8 to resolve some of these.</a></li> 
<li> 2019-03-20: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/56fbc7e0db270b2713cde5067092bebddfdd61a8" target="blank"> Modify flake8 settings to extend the default ignore list, instead of completely overwriting it.</a></li> 
<li> 2019-03-19: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/80bb3d4882b4bac8b1375ada8564a662c901a1e7" target="blank"> Align all settings with GEOSERVER_WEB_UI_LOCATION default value</a></li> 
<li> 2019-03-19: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/da8846001970a40fc3e8ee6ef9b9534940abeecc" target="blank"> Fix #4298</a></li> 
<li> 2019-03-19: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/6edabda4fddf539ec1bdd6d94cde3da21a03962b" target="blank"> Clean up unused testing dependencies and upgrade current testing dependencies</a></li> 
<li> 2019-03-19: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/4aee5bcfc6feba0cad9021cc163e549120d00742" target="blank"> Remove unused jenkins files and pycodestyle dependency.</a></li> 
<li> 2019-03-19: afabiani <a href="http://github.com/geonode/geonode/commit/7c05b9cfb327ee7f56dbba90ac78a6b1ec53d324" target="blank">  - GEOSERVER_WEB_UI_LOCATION default value should point to localhost 8080</a></li> 
<li> 2019-03-19: afabiani <a href="http://github.com/geonode/geonode/commit/4c08e825f935d07d1ec7c0dee17d0faf6ac38cf2" target="blank">  - Typo on request headers key retrieval</a></li> 
<li> 2019-03-19: afabiani <a href="http://github.com/geonode/geonode/commit/21280324c6f0796e02e8c439264b2372c4b87104" target="blank">  - Introducing Proxy Max Retries Option</a></li> 
<li> 2019-03-19: afabiani <a href="http://github.com/geonode/geonode/commit/70edba337d4e4dbfc8827a50c2cf620c971ff645" target="blank">  - Fix Travis</a></li> 
<li> 2019-03-18: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/971c9e6c43bec1cb6bae8ced591488988571b728" target="blank"> Update requirements_docs.txt to reflect the latest dependency changes.</a></li> 
<li> 2019-03-18: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/d59658bd28c3ccb2abd03c48c169c44123743152" target="blank"> Remove unnecessary Ubuntu package comments.</a></li> 
<li> 2019-03-18: afabiani <a href="http://github.com/geonode/geonode/commit/35c235c2f2e94fc4a8e3cdfced4eaf7f1e823eb4" target="blank">  - Restore codecov status check</a></li> 
<li> 2019-03-18: afabiani <a href="http://github.com/geonode/geonode/commit/3e08f2334c9a876890985b13b4c851be19d31846" target="blank"> [Fixes #4293] CSW download link: metadata are empty</a></li> 
<li> 2019-03-18: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/20b24f9db0310f1a2fefa5d1634805efcef9ee72" target="blank"> Upgrade various python dependencies to their latest compatible versions.</a></li> 
<li> 2019-03-18: afabiani <a href="http://github.com/geonode/geonode/commit/bf4826b4bce2decff5205e44f1250c7decbd0554" target="blank">  - 'base.auth' must skip None or Anonymous users</a></li> 
<li> 2019-03-18: afabiani <a href="http://github.com/geonode/geonode/commit/b4686d73191f163eb86698d12c97caecf5371ddc" target="blank">  - Make sure we use "basic.auth" whenever we check for 'access_token'</a></li> 
<li> 2019-03-17: afabiani <a href="http://github.com/geonode/geonode/commit/d54cb85224d0d8dd5e47d1f925dfb3eebfc18d80" target="blank">  - Fix Travis tests</a></li> 
<li> 2019-03-17: afabiani <a href="http://github.com/geonode/geonode/commit/81471d1be262ba71b6c471cd96c61885296121a3" target="blank"> - Trevis tests fix</a></li> 
<li> 2019-03-17: afabiani <a href="http://github.com/geonode/geonode/commit/8dcddb3760c517a6c56b25895e2771acba136b65" target="blank">  - Trevis tests fix</a></li> 
<li> 2019-03-16: afabiani <a href="http://github.com/geonode/geonode/commit/5b4504bd4d8c4c8184c16c8abfdc5dafd7273531" target="blank">  - Revert commit breaking tests</a></li> 
<li> 2019-03-16: afabiani <a href="http://github.com/geonode/geonode/commit/70c31e3d4dcb503ad81145a68838e7d9953cbe60" target="blank">  - Fix test cases</a></li> 
<li> 2019-03-15: afabiani <a href="http://github.com/geonode/geonode/commit/bac420c71aa9d07c1a982891b9019abd74db481e" target="blank">  - Hardening GeoNode and cleanup: http_client uses Bearer Auth whenever it's possible</a></li> 
<li> 2019-03-15: afabiani <a href="http://github.com/geonode/geonode/commit/e55c3ea63ca51695ae79913d51f9873c45c84c1d" target="blank">  - Fix smoke test cases</a></li> 
<li> 2019-03-15: afabiani <a href="http://github.com/geonode/geonode/commit/0796ef4c892b6bcc30b3e71c796b37b9dc4e21fd" target="blank">  - Send warning message whenever the session has expired</a></li> 
<li> 2019-03-15: afabiani <a href="http://github.com/geonode/geonode/commit/683392c85c5b77cb1faa5b959c5272e0cd393d2c" target="blank">  - Hardening GeoNode and cleanup: http_client uses Bearer Auth whenever it's possible</a></li> 
<li> 2019-03-14: afabiani <a href="http://github.com/geonode/geonode/commit/17e061b8a6e800c7bba67de9936a5a62a6d0e810" target="blank"> [Closes #4106] [Remote Services] Add the possibility of filtering the list of resources</a></li> 
<li> 2019-03-14: afabiani <a href="http://github.com/geonode/geonode/commit/f4ce20a2c44ff2fb48c71d4cda32f2c5a449fefd" target="blank"> [Closes #4251] Introduce a SessionExpiredMiddleware in order to checkfor access_token validity</a></li> 
<li> 2019-03-14: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/3777548e49a8e0585a4dd3424d317f72e5d73319" target="blank"> add color picker to theme admin</a></li> 
<li> 2019-03-14: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/35c8b453c5528f7106536e7b693db3ed6bdf53d2" target="blank"> fix geoserver public location</a></li> 
<li> 2019-03-13: afabiani <a href="http://github.com/geonode/geonode/commit/cdf22e5ab48d71c84f0f4762b84210dfdfc698a9" target="blank">  - Proxy: use requests instead of old fashion httplib</a></li> 
<li> 2019-03-13: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/e8788233457fb7a239d6c527ceb9bf7e5f221048" target="blank"> fix geoserver default public location</a></li> 
<li> 2019-03-12: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/ceb0a81f4eb33667ce40147f9ab825bdec101023" target="blank"> Use pycodestyle<2.4.0 until we upgrade the other related dependencies.</a></li> 
<li> 2019-03-08: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/0586d356a670e97a52496eb83094ea4636159746" target="blank"> pep8 dependency is deprecated, remove and replace it with pycodestyle</a></li> 
<li> 2019-03-12: afabiani <a href="http://github.com/geonode/geonode/commit/aa503d94aacb3bc7198b5284c8f036947db039d1" target="blank">  - Minor: double checks action data format str vs. json</a></li> 
<li> 2019-03-11: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/1d8d6a00f76fbfa4ff82fff9d5b5d83d80cff7df" target="blank"> Remove unnecessary dependencies in debian control file to mirror the removals in requirements.txt.</a></li> 
<li> 2019-03-08: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/d050abafd7ddd6c16bbb15327bf14a69f4cff3c3" target="blank"> Update requirements_docs.txt to reflect changes in requirements.txt.</a></li> 
<li> 2019-03-08: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/fec287ce644c09703ae35febc4d42d098418c098" target="blank"> Remove unused Pinax, WeasyPrint and debug dependencies</a></li> 
<li> 2019-03-12: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/1051c9293256ef8ec7f1da9b5a0e0ed707dd47da" target="blank"> fix csw tests</a></li> 
<li> 2019-03-12: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/2a9b9c48d68e97603d6991ad1fb7138b813024a1" target="blank"> remove redundant settings</a></li> 
<li> 2019-03-12: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/1cfd777fa4aacb92d3294159fd7295f80bac9ca7" target="blank"> Update settings.py</a></li> 
<li> 2019-03-11: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/0cc82276b751ff17de4e8913ff89af2e9e305cdf" target="blank"> remove unused and misleading settings</a></li> 
<li> 2019-03-07: capooti <a href="http://github.com/geonode/geonode/commit/1af88d62e9b2d058ff1e5db63c528ff3535cc387" target="blank"> Bump django-geoexplorer-worldmap 4.0.64</a></li> 
<li> 2019-03-07: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/14ff92ebf0ac066c993c96908d3014caf382fcb9" target="blank"> Add frafra to AUTHORS</a></li> 
<li> 2019-03-07: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/b9dace691c10c40788a6c44407d4d8691b808d3b" target="blank"> Run dos2unix on .env files</a></li> 
<li> 2019-03-05: afabiani <a href="http://github.com/geonode/geonode/commit/6eecaf9446a2c2cce0e9e95dc04b535056bf90d0" target="blank">  - Use access_token when parsing layer attributes</a></li> 
<li> 2019-03-05: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/f1fd24873931e23a3d1694cceb3e40f72ab099e8" target="blank"> Updated german translation</a></li> 
<li> 2019-03-05: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/6a154a785fe14e4f401d9431fc8dd1c28600653b" target="blank"> Fix Postgres wait on SPC GeoServer</a></li> 
<li> 2019-02-28: afabiani <a href="http://github.com/geonode/geonode/commit/b9298f0b775db765fa83c20b47a6b26f42df2a4a" target="blank"> [minor] removing redoundant middleware class from settings</a></li> 
<li> 2019-02-27: afabiani <a href="http://github.com/geonode/geonode/commit/b2d6f0e5ede3642c308fcc5df2c33b2e2a5e010c" target="blank"> [Fixes #4254] Pavement YAMLLoadWarning</a></li> 
<li> 2019-02-26: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/c669c188cab4853c30fa1b0f60445f79c89a58c6" target="blank"> Adds back pyopenssl to requirements.txt.</a></li> 
<li> 2019-02-26: Jeremiah Cooper <a href="http://github.com/geonode/geonode/commit/f8b07c55dfcd3e0c6e2a637cf52e760ff71194a1" target="blank"> Removes unnecessary dependencies from the requirements.txt and settings.py files.</a></li> 
<li> 2019-02-22: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/6f1bb7d0f7b86e87c21b4aacb5a766d0160bf9c9" target="blank"> Disable system_site_packages for geonode-selenium</a></li> 
<li> 2019-02-22: capooti <a href="http://github.com/geonode/geonode/commit/83734d8f7566350edf6138f94c51dc9123bf10ee" target="blank"> Bump django-geoexplorer-worldmap==4.0.63</a></li> 
<li> 2019-02-22: afabiani <a href="http://github.com/geonode/geonode/commit/968f9d4a757fe2ee35ec8b410b4252028052f481" target="blank">  - Fix smoke test cases</a></li> 
<li> 2019-02-22: afabiani <a href="http://github.com/geonode/geonode/commit/09e3cb8588ec449e564c25f16c048877af6a6626" target="blank">  - Fix smoke test cases</a></li> 
<li> 2019-02-22: afabiani <a href="http://github.com/geonode/geonode/commit/b60e26b5aa3114b24985c995867643f9be52a692" target="blank"> [Closes #4249] Contribute back upstream menu management from IGAD</a></li> 
<li> 2019-02-21: afabiani <a href="http://github.com/geonode/geonode/commit/9ae8535f39e86982a61e86006c5ec3f8118a6897" target="blank"> Fixes Travis geonode-selenium build</a></li> 
<li> 2019-02-21: afabiani <a href="http://github.com/geonode/geonode/commit/fca593a0d2e2f9774db576a66aad79c71ae9b15d" target="blank"> Fixes Travis geonode-selenium build</a></li> 
<li> 2019-02-21: afabiani <a href="http://github.com/geonode/geonode/commit/09cc694591a96bfc90a038b5e9a5b3ad7cd7b5d3" target="blank"> Fixes Travis geonode-selenium build</a></li> 
<li> 2019-02-21: afabiani <a href="http://github.com/geonode/geonode/commit/04ce54c0b9a0dc751ebc0b0c6e8cfcef6d10a43b" target="blank"> Fixes Travis geonode-selenium build</a></li> 
<li> 2019-02-21: afabiani <a href="http://github.com/geonode/geonode/commit/79a4da9e714e34e4e6c60126da8912228e3f9c94" target="blank"> Fixes Travis geonode-selenium build</a></li> 
<li> 2019-02-21: afabiani <a href="http://github.com/geonode/geonode/commit/d8b05a356d33e5a437b664d7adaa1974ade2b91c" target="blank"> Fixes Travis geonode-selenium build</a></li> 
<li> 2019-02-21: afabiani <a href="http://github.com/geonode/geonode/commit/68c59def24229d5967fee869ecf6e145fadf23d8" target="blank"> [Fixes #4247] 404 error on CSV upload</a></li> 
<li> 2019-02-20: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/44ef8dc8dee0179ee77418ceb86bb05d57747649" target="blank"> Import SSL Certificate for GeoServer</a></li> 
<li> 2019-02-15: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/9c8d1b22038f6c53d9ff0f071e455a26512cae2f" target="blank"> Test with geonode-selenium</a></li> 
<li> 2019-02-19: Denis Rykov <a href="http://github.com/geonode/geonode/commit/b62a8aa77a9569652fb63e2867e0f952346511b2" target="blank"> Typo fix</a></li> 
<li> 2019-02-19: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/536f4959911b762ac487581d5a7f1f1d74b1a5e6" target="blank"> Add support for plugins</a></li> 
<li> 2019-02-19: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/f066d90b23ae9c9a6f9e8837cf3ad26725ec45b9" target="blank"> Update GeoServer to 2.14.2</a></li> 
<li> 2019-02-18: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/00d8e5ef65da6aea029e3c5bec39574307975a50" target="blank"> Improve comment about POSTGRES_PASSWORD</a></li> 
<li> 2019-02-18: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/1cc77259139d0189a3cf92e40b0dd2887d311b8d" target="blank"> Use DATABASE_URL in pgdumper</a></li> 
<li> 2019-02-18: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/b6c75f7e96c1bad31387dfcc62316b3e66f8ec21" target="blank"> Use custom Postgres password</a></li> 
<li> 2019-02-18: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/308b7e503788fb2335957e23341fc18b461b8d22" target="blank"> Add ON_ERROR_STOP=1</a></li> 
<li> 2019-02-18: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/760e5a3917e43d0b090a06b3ffb24db76c337d35" target="blank"> Remove extra Postgres wait</a></li> 
<li> 2019-02-17: Hisham waleed karam <a href="http://github.com/geonode/geonode/commit/aba786993def65951a7fae3a1802d7dc8b7b7180" target="blank"> use 'update' queue instead if using the default</a></li> 
<li> 2019-02-14: capooti <a href="http://github.com/geonode/geonode/commit/aee5fbb8635d5c3f91ffb55323096eac5ea2b086" target="blank"> Fixed a broken link in WorldMap documentation</a></li> 
<li> 2019-02-14: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/42e0bc33daa5b29255218bc4259a2099e155a28f" target="blank"> Add suffix geoserver to BASEURL</a></li> 
<li> 2019-02-14: afabiani <a href="http://github.com/geonode/geonode/commit/9647d53ce7454bda86da7bee86569433e103ef77" target="blank">  - add missing header to Python file</a></li> 
<li> 2019-02-14: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/2675ca374f1691e862328410bdc1700c7002e4da" target="blank"> fix Object of type Map is not JSON serializable</a></li> 
<li> 2019-02-14: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/e8291bf8415d208045bc70ea8167e2bb3290e89e" target="blank"> Use geoserver instead of gs (partial revert)</a></li> 
<li> 2019-02-14: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/ee212deaa7055d56bbecf0e396a03835f3454616" target="blank"> tastypie OAuth Backend</a></li> 
<li> 2019-02-13: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/16168e2a767ca92a0a1a76580e486a3e4467729b" target="blank"> Wait for GeoServer and PostgreSQL instead of failing</a></li> 
<li> 2019-02-14: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/c74f1dd3a5830ce387bc7f1e11ef601f5fa2fa3d" target="blank"> Add rabbitmq volume to main docker-compose.yml</a></li> 
<li> 2019-02-13: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/727d809151b225c1e65c829385402e51b14f291b" target="blank"> use regex to extract schema</a></li> 
<li> 2019-02-13: afabiani <a href="http://github.com/geonode/geonode/commit/44a226a5a4ef6b09d63be9944b6ef23a9d5ea34a" target="blank"> [minor] There was a wrong 'expiring' check on purging old tokens</a></li> 
<li> 2019-02-13: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/372e8ea71f15f1ad0296d4e4c9a285ae5169aed7" target="blank"> Add rabbitmq volume</a></li> 
<li> 2019-02-13: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/f2495b85634a2a1f2a7cdd4a8b1cd026525cf5fc" target="blank"> for haystack also get 'vector_time' layers when 'vector' type is selected as 'vector' is super type of 'vector_time'(same behavior of rest api)</a></li> 
<li> 2019-02-13: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/1e6b2319f19a98b0cdd8d662d31701bbd3b3de1a" target="blank"> filter by vector time layers is not working when haystack is enabled. as for vector_time layer, 'vectorTimeSeries' is indexed instead of 'vector_time'</a></li> 
<li> 2019-02-12: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/80c3bff81bfa33f8c7f89079529d1aacfe59fdc8" target="blank"> Update requirements_docs.txt</a></li> 
<li> 2019-02-12: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/45181708bad206556dfc50a2617a2d2b5d1200b6" target="blank"> Update requirements.txt</a></li> 
<li> 2019-02-12: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/5a6e17c2edf3d37aeb4ade5bb586d74453ae2710" target="blank"> Update requirements_docs.txt</a></li> 
<li> 2019-02-12: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6750ff4726d36c8a385a4bdf6688e186555eec09" target="blank"> Update requirements.txt</a></li> 
<li> 2019-02-12: afabiani <a href="http://github.com/geonode/geonode/commit/c3cf2522759f7820f8179fb77043527dff3d43a3" target="blank"> [Related to #4219] - mitigates the issue: Delayed Security Sync Task seems causing issues with sqlite queries</a></li> 
<li> 2019-02-11: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/c3175fd1761dbe034c3fd42c5761ab20e1145dbb" target="blank"> Remove not used settings sample</a></li> 
<li> 2019-02-11: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/9cf57ef3b12b8513b53c682d90abcb7d9af5e1f6" target="blank"> Revert " Includes additional layer fields in the search index" (#4217)</a></li> 
<li> 2019-02-11: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/a5311bdf18323f7527edf807a70371c5a17e5fcf" target="blank"> Fix missing replacement of geoserver public location (#4215)</a></li> 
<li> 2018-09-12: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/68c2289828e3b821e8d829f9b8314abebed8bfb7" target="blank"> Make sure geogig can be created in a schema other than public</a></li> 
<li> 2019-02-07: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/e554caa7fe0fb937ba31c3fd56178e2a55491593" target="blank"> remove unused import</a></li> 
<li> 2019-02-08: giohappy <a href="http://github.com/geonode/geonode/commit/094a7da08e74423e5e0db9628466600a0f47fa76" target="blank"> moved login/logout callbacks to profile module; renamed oauth utils to auth</a></li> 
<li> 2019-02-07: capooti <a href="http://github.com/geonode/geonode/commit/e463701518cc03be34470d4a1fd412a1e2d4654b" target="blank"> Remove unwanted line of code in worldmap client</a></li> 
<li> 2019-02-07: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/a2cc04ebc165dda7e593c1a3d88965d499a06b2e" target="blank"> use celery task to generate thumbnails</a></li> 
<li> 2019-02-07: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/dd0d1921305daf1cd14e8cd6a21a5321309f9b50" target="blank"> Fix handling of missing layers.</a></li> 
<li> 2019-02-07: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/f018386c31c0399fa8ee47ff5b3f3ac4412a2859" target="blank"> disable threading in test</a></li> 
<li> 2019-02-06: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/a84096b39f8fe1aeb13ae4c6128c99e36ae23ab8" target="blank"> use celery first if enabled</a></li> 
<li> 2019-02-06: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/a18bbd447721a370772ebc030632f4e36a4e4262" target="blank"> add async_thumbnail to improve upload time</a></li> 
<li> 2018-09-12: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/327358a9d1e55fc0883059d249c0f1c6ec405429" target="blank"> Includes additional fields in the search index</a></li> 
<li> 2019-02-06: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/c81fd516725125359b0312737dffa6c18ca78964" target="blank"> Use gs instead of geoserver for URLs in Docker</a></li> 
<li> 2019-02-05: afabiani <a href="http://github.com/geonode/geonode/commit/df468a997ef0218a1c9ac1b939c5ec0f4e4f7ef6" target="blank"> [Security Cleanup] - Remove unuseful and potentially blocking calls from signals and login/out calls</a></li> 
<li> 2019-02-05: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6bd835a7165b896d8a0519ce0f9a0b02cc57a0d5" target="blank"> Cleaning up session if no valid access_token key has been found</a></li> 
<li> 2019-02-05: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/a108360a3126783159ac897b48d601dee5a217ab" target="blank"> Update oauth.py</a></li> 
<li> 2019-02-05: afabiani <a href="http://github.com/geonode/geonode/commit/9cef6600d00c10b41b1706f24238d9efa627ed87" target="blank">  - Backporting GEOSERVER_WEB_UI_LOCATION to sample local settings</a></li> 
<li> 2019-02-04: giohappy <a href="http://github.com/geonode/geonode/commit/01dcc3610575bdb358e4b5dfa2a4dd6eb413ff5f" target="blank"> fixed exception retrieving token object from empty session token</a></li> 
<li> 2019-02-04: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/1560a46758f08a84d67d1bb09c5141eb24761455" target="blank"> Adding all Oauth2 endpoints to lockdown exempt uris</a></li> 
<li> 2019-02-04: giohappy <a href="http://github.com/geonode/geonode/commit/d6d98495b1ef5ae6a771e0bb900ce254ec624ed0" target="blank"> fixed another pep8 issue</a></li> 
<li> 2019-02-04: giohappy <a href="http://github.com/geonode/geonode/commit/d20c9db0106d2bed586b28d7547cf4f47e436f06" target="blank"> fixed pep8 issues</a></li> 
<li> 2019-02-04: giohappy <a href="http://github.com/geonode/geonode/commit/2ccaece5d4e5611ebab0cb78fe423af5f487bb9c" target="blank"> fixed mixing of token object and string in login/logout</a></li> 
<li> 2019-02-01: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/2bb0b9b65ccc2d3e440887245d54a98fa401052a" target="blank"> fix flake8</a></li> 
<li> 2019-02-01: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/6125d2f0afbaf3c565ebbcb338ef04d3429798c6" target="blank"> fix flake8</a></li> 
<li> 2019-01-31: afabiani <a href="http://github.com/geonode/geonode/commit/92ffdc6b1a9bd0b12d7e5dec48cd1dbccd9ed7b0" target="blank">  - fix pavemenet cmdopts options</a></li> 
<li> 2019-01-31: afabiani <a href="http://github.com/geonode/geonode/commit/5553170d5f421906f36a0f542c7407178c4965ca" target="blank"> - Travis Fix & Optimize</a></li> 
<li> 2019-01-30: capooti <a href="http://github.com/geonode/geonode/commit/1aeefe08cfd4fac1c1f884a81828b678aebd8a49" target="blank"> Related to fix for #4178</a></li> 
<li> 2019-01-30: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/4ea657e90f561fd888ce52964f494cbfec5bf6fb" target="blank"> fix force list status code</a></li> 
<li> 2019-01-30: afabiani <a href="http://github.com/geonode/geonode/commit/6f76fd5c7de20be9518d328b89be7484dc6559a6" target="blank">  - Split Travis integration tests into 3 different tasks</a></li> 
<li> 2019-01-30: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/8596bc4e2cf50332eeea6538d196debc6391ecc1" target="blank"> fix import</a></li> 
<li> 2019-01-30: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/7d07b84d3dac0613863050aa3d7b5758efc2cf14" target="blank"> use requests retry to improve geonode/geoserver connection</a></li> 
<li> 2019-01-30: giohappy <a href="http://github.com/geonode/geonode/commit/bdde3b18e48d115578564c1a450aeb9fb440e14e" target="blank"> proxy auth refactoring with extended checks</a></li> 
<li> 2019-01-30: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/05f49e5dc72a4c2fade0b438886bafeb0c0b066a" target="blank"> fix layer_thumbnail returned None instead.</a></li> 
<li> 2019-01-30: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/b3e9359dc001b89b5bb4281b387ff4ccac5fafdd" target="blank"> fix map_thumbnail returned None instead.</a></li> 
<li> 2019-01-30: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/e03d14b24d88ddb5042b98f00fa927e324e466a6" target="blank"> improve map_thumbnail view</a></li> 
<li> 2019-01-30: hisham waleed karam <a href="http://github.com/geonode/geonode/commit/9ca3957f65988950907d76a91621536a1fb899ce" target="blank"> improve layer_thumbnail view</a></li> 
<li> 2019-01-29: capooti <a href="http://github.com/geonode/geonode/commit/76bbbbac7a2c796676d41dff108bec7854509d1a" target="blank"> Added chinese to ALL_LANGUAGES enumeration</a></li> 
<li> 2019-01-29: giohappy <a href="http://github.com/geonode/geonode/commit/8a1c0c6db530ef7b3d93727ffc5ac6142498e5a1" target="blank"> introduce new GEOSERVER_WEB_UI_LOCATION options</a></li> 
<li> 2019-01-29: Florian Hoedt <a href="http://github.com/geonode/geonode/commit/6fb586a3744b1e90d604a82686e71af635b41829" target="blank"> update to PostgreSQL 10</a></li> 
<li> 2019-01-28: afabiani <a href="http://github.com/geonode/geonode/commit/80cbfd25571063ae07862e2e371a8a02eac45fd3" target="blank">  - Added also '/api/layers' as per giohappy review</a></li> 
<li> 2019-01-25: afabiani <a href="http://github.com/geonode/geonode/commit/086f5069d50d4d9ccb605b167301a7413ebb7d96" target="blank"> [Closes #4183] Fix and improve LOCKDOWN_GEONODE mechanism</a></li> 
<li> 2019-01-25: afabiani <a href="http://github.com/geonode/geonode/commit/9717e8299a69e2b541fe81d6f44ee304aaad21b9" target="blank"> [Closes #4183] Fix and improve LOCKDOWN_GEONODE mechanism</a></li> 
<li> 2019-01-25: afabiani <a href="http://github.com/geonode/geonode/commit/4e9ecc0d8cc70215615e92185319b3671ce22a56" target="blank"> [Closes #4183] Fix and improve LOCKDOWN_GEONODE mechanism</a></li> 
<li> 2019-01-25: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/940dd00c0a0ff4a791caefb4c9ee1e4e5216b110" target="blank"> Make flake8 happy</a></li> 
<li> 2019-01-25: afabiani <a href="http://github.com/geonode/geonode/commit/9dc568a5252f5a1658111178571d3fd4a4cb9174" target="blank"> [Fixes #4181] WMS links are not created for Remote services</a></li> 
<li> 2019-01-25: giohappy <a href="http://github.com/geonode/geonode/commit/9266f43feff5f8392bfaaa70c8b1ca074a43a6fa" target="blank"> Geoserver menu link shouldn't be proxied</a></li> 
<li> 2019-01-25: afabiani <a href="http://github.com/geonode/geonode/commit/65177ca6622f3268ce41bcaa3b8676a325f0ffa8" target="blank"> [Fixes #4178] - Unable to create maps with access_token no longer string</a></li> 
<li> 2019-01-24: giohappy <a href="http://github.com/geonode/geonode/commit/3101ce04038a53d14bdf3a9f82abb91f54d5a514" target="blank"> removed test on links in layers list output</a></li> 
<li> 2019-01-24: giohappy <a href="http://github.com/geonode/geonode/commit/094e7a1f0847194ae21132a8c792442f8ec6ba96" target="blank"> make flake happy</a></li> 
<li> 2019-01-24: giohappy <a href="http://github.com/geonode/geonode/commit/f423337704e16814ba0da3763d9183a675846666" target="blank"> show OGC links inside layers list from the API</a></li> 
<li> 2019-01-24: afabiani <a href="http://github.com/geonode/geonode/commit/e6cf56a43e2171a09f968644724298abdd871697" target="blank">  - Fix pep8 issues</a></li> 
<li> 2019-01-24: afabiani <a href="http://github.com/geonode/geonode/commit/393db2c456a94e69a30b977cfd89acd8af9d2d44" target="blank"> [Fixes #4174] - Proxy should pass Bearer authentication to Geoserver transparently</a></li> 
<li> 2019-01-24: afabiani <a href="http://github.com/geonode/geonode/commit/304350363d2810b5ac789067a920c65de2101f3e" target="blank"> [Fixes #4174] - Proxy should pass Bearer authentication to Geoserver transparently</a></li> 
<li> 2019-01-24: afabiani <a href="http://github.com/geonode/geonode/commit/d87d05974a1bfaa24bbe1fcede97890d7e784e21" target="blank"> [Fixes #304] Proxy should pass Bearer authentication to Geoserver transparently</a></li> 
<li> 2019-01-24: afabiani <a href="http://github.com/geonode/geonode/commit/7f82e24c527742d57e2a6d57a77ec30f9d7973de" target="blank">  - Removing duplicate code</a></li> 
<li> 2019-01-23: afabiani <a href="http://github.com/geonode/geonode/commit/b6dc671917a9cc32d8b25daf90063c6f4c6c5ad2" target="blank"> [Fixes #4170] Clean management of OAuth2 Access Tokens</a></li> 
<li> 2019-01-23: afabiani <a href="http://github.com/geonode/geonode/commit/3ca74ca2cc3387e438f75ecc15477c4b0d13974a" target="blank"> [Fixes #4168] GeoNode Proxy should be using OAUTH2 Bearer Header now</a></li> 
<li> 2019-01-23: afabiani <a href="http://github.com/geonode/geonode/commit/9461c1ff73a0c64fc08fed23e0a8eee651529f52" target="blank"> [Fixes #4168] GeoNode Proxy should be using OAUTH2 Bearer Header now</a></li> 
<li> 2019-01-23: afabiani <a href="http://github.com/geonode/geonode/commit/cf1b78c4daaa23fe99b1c9ce869ffa691b2752c1" target="blank"> [Fixes #4168] GeoNode Proxy should be using OAUTH2 Bearer Header now</a></li> 
<li> 2019-01-22: gannebamm <a href="http://github.com/geonode/geonode/commit/16c343dbfba20ffbb04a9f9dcdac3c41d5e9ecf4" target="blank"> missed to revert the celery.env to default</a></li> 
<li> 2019-01-22: admin <a href="http://github.com/geonode/geonode/commit/72f80e59030c6a743eb6fa499fbdf73d312c237d" target="blank"> added ALLOWED_DOCUMENT_TYPES and MAX_DOCUMENT_SIZE as environmental setting to django.env and celery.env. Modified settings.py to read these (doc size was allready implemented)</a></li> 
<li> 2019-01-22: gannebamm <a href="http://github.com/geonode/geonode/commit/d0235269bc94489ddb76eedfe073afba0c772339" target="blank"> changed some environmental vars back to default</a></li> 
<li> 2019-01-22: admin <a href="http://github.com/geonode/geonode/commit/42ab7bef402cb639c29d69e714f8b19b6a992fe5" target="blank"> added ALLOWED_DOCUMENT_TYPES and MAX_DOCUMENT_SIZE as environmental setting to django.env and celery.env. Modified settings.py to read these (doc size was allready implemented)</a></li> 
<li> 2019-01-21: afabiani <a href="http://github.com/geonode/geonode/commit/58884cac860bfb16a5a3363f881720c011bfddb8" target="blank">  - Making OAUTH2 Access Token expiration seconds configurable by settings/env</a></li> 
<li> 2019-01-17: capooti <a href="http://github.com/geonode/geonode/commit/aad2d60faac02743b95fc88373f9ef9579ee25f7" target="blank"> Bump django-geoexplorer-worldmap 4.0.62</a></li> 
<li> 2019-01-17: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/7957cde49766390e6485b9a0d03d10db004a143c" target="blank"> Replace exit with a valid command (#4158)</a></li> 
<li> 2019-01-16: capooti <a href="http://github.com/geonode/geonode/commit/dc877e2ceacbc3958570471be7685e89ac3deaf5" target="blank"> urlsuffix can be numeric. Fixes #4159</a></li> 
<li> 2019-01-16: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/32a886b13658a6fe7803da75cc13c5aa8d018a6e" target="blank"> Typos and extra spaces removed</a></li> 
<li> 2019-01-15: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/287708d101732cb665096d257126594089f384c9" target="blank"> Tentative fix readthedocs build</a></li> 
<li> 2019-01-11: afabiani <a href="http://github.com/geonode/geonode/commit/61c38088cae628aa165b2b1bbb1d73bcff27298e" target="blank"> [Fixes #4153] GeoLite Legacy db discontinued so paver setup fails in Geonode 2.8 dev install</a></li> 
<li> 2019-01-08: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/035a9e2bbf2dabde9c4712941ddfe6e21e461c4f" target="blank"> [Fixes #4150] - Security vulnerabilities on deps (#4151)</a></li> 
<li> 2019-01-02: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/ccaa7f443dede2cc504c6cf08a7f37aa414cbc59" target="blank"> removed windows binary from docs</a></li> 
<li> 2019-01-02: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/09fc2df2f7732d727019d4bd37feba1292b87b50" target="blank"> removed windows and apt from readme</a></li> 
<li> 2018-12-21: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/204a707e8d2ebbb54673fd78e6b5e80d1ddc1f18" target="blank"> Fix geonode.binary arguments escaping</a></li> 
<li> 2018-12-21: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/4d2ada22639c684af997ae39cd7f3d4e0b5034f4" target="blank"> Fix geonode.binary arguments escaping</a></li> 
<li> 2018-12-20: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/faf149121013f7d4fef54ec008957c8704153829" target="blank"> Restored older GeoServer Version #4120</a></li> 
<li> 2018-12-19: afabiani <a href="http://github.com/geonode/geonode/commit/5edc5db7d75a698895dcad9061cb7ba81e7b50f3" target="blank">  - default OGC timeout to 60 secs</a></li> 
<li> 2018-12-19: Paolo Corti <a href="http://github.com/geonode/geonode/commit/1a8f527a63be408abdef65dbdc9efdce46d92db6" target="blank"> Fixes #4132 worldmap client print template (#4133)</a></li> 
<li> 2018-12-19: Paolo Corti <a href="http://github.com/geonode/geonode/commit/68a71377c2f7ae031f0d269a9ad1ac5927582288" target="blank"> Fixes #4134 handles multiple groups for a new map in worldmap client (#4135)</a></li> 
<li> 2018-12-19: Paolo Corti <a href="http://github.com/geonode/geonode/commit/346744ce699d0025f7209e9d7f316b652f4e7f18" target="blank"> Improvements to autocomplete. Fixes #4136 (#4137)</a></li> 
<li> 2018-10-31: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/0e0d1bfdfa9b3f4d68e6a05e2854bff0b0d61f59" target="blank"> [Fixes #4025] Regression with uploading a shapefile with no ascii characters (#4026)</a></li> 
<li> 2018-12-17: afabiani <a href="http://github.com/geonode/geonode/commit/676b023ecad29b8ac443fe9ce8369c0591b3b372" target="blank">  - vulnerability issues: urllib3 bump to version 1.24.1</a></li> 
<li> 2018-12-14: afabiani <a href="http://github.com/geonode/geonode/commit/992daf724e83cdb0c1eb776d147eba841ad02cd9" target="blank">  - proj deps</a></li> 
<li> 2018-12-14: afabiani <a href="http://github.com/geonode/geonode/commit/c1f8d510ea8046c8497dd16f94fa032cf2e1a02a" target="blank">  - re-enable django_filters not included into INSTALLED_APPS</a></li> 
<li> 2018-12-14: afabiani <a href="http://github.com/geonode/geonode/commit/f99adf6f595a95433f72cad0feb189d702a9eff2" target="blank"> - Sentinel2 Backgroung Title refs</a></li> 
<li> 2018-12-12: capooti <a href="http://github.com/geonode/geonode/commit/9a8f0c3ebba2b447665a53633090fa79ded0b21b" target="blank"> Add the sync_geonode_layers command. Fixes #4115</a></li> 
<li> 2018-12-12: capooti <a href="http://github.com/geonode/geonode/commit/d0aefd890fdca2901097853c10fc9e6c61f6866e" target="blank"> Fixes #4117</a></li> 
<li> 2018-12-12: afabiani <a href="http://github.com/geonode/geonode/commit/28792c3acb865ac792d1e7916630319a0a0fd6df" target="blank">  - 'Get Started' inherits the Jumbotron paragraph style</a></li> 
<li> 2018-12-10: afabiani <a href="http://github.com/geonode/geonode/commit/339fdafadb0ea24ea09d44554fa601304ab0529f" target="blank">  - Allow GeoServer Proxy to recognize prefix on non-root paths also</a></li> 
<li> 2018-12-07: afabiani <a href="http://github.com/geonode/geonode/commit/5c979855b83fd18448a0e037c7978ae8eb59dc8f" target="blank">  - Fix small autoescape issue on detail templates</a></li> 
<li> 2018-12-06: Francesco Frassinelli <a href="http://github.com/geonode/geonode/commit/3d92222148e0f9d27c0e29c5eef1e3ccf102a87d" target="blank"> Fix codecov link</a></li> 
<li> 2018-12-05: capooti <a href="http://github.com/geonode/geonode/commit/434d68dab1ea99c2233a56006e5688310a29264e" target="blank"> [worldmap-client] Makes Google StreetView optional. Bump django-geoexplorer-worldmap 4.0.61. Remove some unused code</a></li> 
<li> 2018-12-05: afabiani <a href="http://github.com/geonode/geonode/commit/388fc114d73a1abdb35b0a74df6b447f1c0199c1" target="blank">  - Silencing deprecated warnings</a></li> 
<li> 2018-12-05: afabiani <a href="http://github.com/geonode/geonode/commit/89c97db8695efe0d27defeec055153fdbbd28cd9" target="blank">  - Silencing deprecated warnings</a></li> 
<li> 2018-12-05: afabiani <a href="http://github.com/geonode/geonode/commit/cd874e39c92946a4c70c25fc769e9246fcc4332a" target="blank">  - local_settings.py.geoserver update ms2 backgrounds / catalog takes siteurl / allowed hosts checking for env vars</a></li> 
<li> 2018-12-05: afabiani <a href="http://github.com/geonode/geonode/commit/e5fce5c6677e5038100732a3c5d5e668a52d3d9a" target="blank"> [Fixes #4105] [Remote Services] harvesting resources pagination does not keep memory of the selection if changing page</a></li> 
<li> 2018-12-04: capooti <a href="http://github.com/geonode/geonode/commit/06fae33d3965e449920768f33d4755b341b18a9b" target="blank"> When using worldmap client we need geoserver layers to use gxp_gnsource vs gxp_wmscsource</a></li> 
<li> 2018-12-03: afabiani <a href="http://github.com/geonode/geonode/commit/4c9ba1b8857400902d1bcda44cefb98e0251d96b" target="blank">  - Revert wrong setting</a></li> 
<li> 2018-12-03: afabiani <a href="http://github.com/geonode/geonode/commit/20c1adea7db8576ef127eebfc957d9947d6671b6" target="blank">  - E-mail Tasks Bindings</a></li> 
<li> 2018-12-03: afabiani <a href="http://github.com/geonode/geonode/commit/b534c2de691b4d81be1df3958d68edb2dc37811f" target="blank">  - Remote Services Async Tasks Binding</a></li> 
<li> 2018-11-30: afabiani <a href="http://github.com/geonode/geonode/commit/9dad68eb385fc97f8cee40f951d7e2e90c768c89" target="blank">  - Layed Detail: legend url and title accoringly to the current style selected</a></li> 
<li> 2018-11-29: capooti <a href="http://github.com/geonode/geonode/commit/62474d6150776f47496746c07b15e19e22ab63c9" target="blank"> Port the worldmap map notes application. Fixes #4101</a></li> 
<li> 2018-11-29: afabiani <a href="http://github.com/geonode/geonode/commit/b398ec396abd28d6832de62b89837a59208c1748" target="blank">  - Remove wrong sample layers from local_settings geoserver sample</a></li> 
<li> 2018-11-29: afabiani <a href="http://github.com/geonode/geonode/commit/c17181682c53b59447318d9d4e771e85117ebc58" target="blank">  - View Layer should not behave as Edit Layer</a></li> 
<li> 2018-11-29: afabiani <a href="http://github.com/geonode/geonode/commit/e844f2fefc4da38e289ecc7f8663c4f433276272" target="blank"> - Finalize: Update docker compose files and refresh of JS assets</a></li> 
<li> 2018-11-29: afabiani <a href="http://github.com/geonode/geonode/commit/a2f08785ddb999111e3eee2426317d45dc1d5e42" target="blank">  - Removing unused crontab dependency</a></li> 
<li> 2018-11-28: capooti <a href="http://github.com/geonode/geonode/commit/2e251db923c79693ff372099c64d60849f530ade" target="blank"> Bump django-geoexplorer-worldmap 4.0.60</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/b4d6ccf3664565e073e3ec06eaa97a283affa672" target="blank">  - Finalize: Update docker compose files and refresh of JS assets</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/0f84734ab57c85c61782e6c0e29aa3fb8bfdbaae" target="blank">  - Finalize: Update docker compose files and refresh of JS assets</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/b7544e5a3391ed1106948ea83343316638756f35" target="blank">  - Finalize: Update docker compose files and refresh of JS assets</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/42598ef74761f1500627b9fb478d69abcb5f8036" target="blank">  - pep8 issues</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/5fe6808e30df7b3c697a917e4daa7771e0fb26f3" target="blank">  - Refreshing static assets</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/c414b5545445c82721cad5a8fbe04499f7d86191" target="blank">  - Fix the way how to Style Manage page fetches the styles: read them from GeoNode and align with the GeoServer instance</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/b9e8393642f828d4620e51dad59c982d40311bef" target="blank">  - Fix the way how to Style Manage page fetches the styles: read them from GeoNode and align with the GeoServer instance</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/6d40aff09e7ca9c40bdb6ae2e95885ed5dc1dc70" target="blank">  - Aligning and improving the docker-compose settings</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/16de3143ad17a9ec246679b2ff0c53f08fe78176" target="blank">  - Refreshing static assets</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/ea3ed734e36963eec963e6a760434e870bbfc19b" target="blank">  - Fix the way how to Style Manage page fetches the styles: read them from GeoNode and align with the GeoServer instance</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/66873e968efe5fcd277248537c8bff9153d6dc26" target="blank">  - Update docker compose files</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/9059412997177db2e7b17a6a6e76c01fc80192d7" target="blank">  - Update docker compose files</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/cb209d50ca22d0c39e2f3c5bb1fda0848ae4dafb" target="blank">  - Update docker compose files</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/5d1bded397049205fea16500898a36da3ee3886f" target="blank">  - Update docker compose files</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/15e857de15303e187e80f68b16853703d996d64d" target="blank">  - Update docker compose files</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/8a13d08fcbf45696b3b711e4192eb2adec45809a" target="blank">  - Update docker compose files</a></li> 
<li> 2018-11-28: afabiani <a href="http://github.com/geonode/geonode/commit/8e5453484918def38d74bcec6a1a6625c178295b" target="blank">  - Update docker compose files</a></li> 
<li> 2018-11-26: afabiani <a href="http://github.com/geonode/geonode/commit/d38a9f0ad76810985338a41e8214772cb67b375b" target="blank">  - align Layer Detail page style with the Map Detail one</a></li> 
<li> 2018-11-26: afabiani <a href="http://github.com/geonode/geonode/commit/e13a4f787c6908eda9fcdb5af8ef26997b09d923" target="blank">  - minor updates to local_settings.py.geoserver.sample</a></li> 
<li> 2018-11-22: afabiani <a href="http://github.com/geonode/geonode/commit/6de0c92f9823698ef25160d66b41cf0b2f3935a8" target="blank">  - Minor Refactoring: Edit Map buttons names</a></li> 
<li> 2018-11-22: afabiani <a href="http://github.com/geonode/geonode/commit/4ad081a45c551d1a8d5395c7405e52b644480f0a" target="blank">  - Minor Refactoring: Edit Map buttons names</a></li> 
<li> 2018-11-22: afabiani <a href="http://github.com/geonode/geonode/commit/e28c3f431b4d3edd85665ee093a6bc8efddf1bff" target="blank">  - Minor Refactoring: Edit Map buttons names</a></li> 
<li> 2018-11-22: afabiani <a href="http://github.com/geonode/geonode/commit/b5605692be99535337c5232d0bd3834f86525260" target="blank">  - Minor Refactoring: Edit Map buttons names</a></li> 
<li> 2018-11-16: capooti <a href="http://github.com/geonode/geonode/commit/615693334c8337179bcbf7d6c9fe23bff717160b" target="blank"> Fixes #4089: identify does not work on layers added from the search interface</a></li> 
<li> 2018-11-15: capooti <a href="http://github.com/geonode/geonode/commit/8dfadf5cb4012b9d1cdc1743db3c8d6a22da9fa2" target="blank"> Fixes #4086: worldmap gazetteer fails to be updated when field names are not ascii</a></li> 
<li> 2018-11-15: capooti <a href="http://github.com/geonode/geonode/commit/ebb2b3cd0d1760460ee9b5a10327250d9ca30120" target="blank"> Detect if client is mobile and ask to use wm mobile client</a></li> 
<li> 2018-11-15: afabiani <a href="http://github.com/geonode/geonode/commit/ecfa9d192b0f6f712eaec54696c2049c5a0e948b" target="blank">  - Proxy: include "DELETE" operation also when checking for Auth headers</a></li> 
<li> 2018-11-15: afabiani <a href="http://github.com/geonode/geonode/commit/c5c650513bce40d2d7f97e30940b79a5cdf51926" target="blank">  - Proxy: include "DELETE" operation also when checking for Auth headers</a></li> 
<li> 2018-11-14: capooti <a href="http://github.com/geonode/geonode/commit/5b97afb653a52886557b2ec12368012db45a2023" target="blank"> [worldmap-client] Fixes #4082: remove unneeded tools from map details page</a></li> 
<li> 2018-11-14: afabiani <a href="http://github.com/geonode/geonode/commit/e268a7ea638216a802d3dc544c8d736ce3d5b439" target="blank">  - Display only default style legend at startup</a></li> 
<li> 2018-11-14: afabiani <a href="http://github.com/geonode/geonode/commit/7cdf4d2cd12900fb38f7302b6db5a73dd71f74c8" target="blank">  - Display only default style legend at startup</a></li> 
<li> 2018-11-14: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/c0ea75a1815da138a8925140c53409f1ae5021e4" target="blank">  - geoserver proxy style check fix</a></li> 
<li> 2018-11-14: afabiani <a href="http://github.com/geonode/geonode/commit/f65d69d5fdc77592015ae9fc6bc96a20901ad3bc" target="blank">  - minor log formatting</a></li> 
<li> 2018-11-14: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/b27a1f9bdba3ff2a0aa65bc9f2bb503dbcf29d4c" target="blank">  - geoserver proxy style check fix</a></li> 
<li> 2018-11-14: afabiani <a href="http://github.com/geonode/geonode/commit/d2bf71afa385ede08c6438eb7db55be25db67132" target="blank">  - minor log formatting</a></li> 
<li> 2018-11-14: afabiani <a href="http://github.com/geonode/geonode/commit/69ee087a884eec89a5449af63f10fbfe3fe61295" target="blank">  - minor log formatting</a></li> 
<li> 2018-11-13: capooti <a href="http://github.com/geonode/geonode/commit/385ae621b77d8c61ce1de83be84e5d77f7ab02a9" target="blank"> Fixes #4080 (worldmap client "layers list" failing with new maps)</a></li> 
<li> 2018-11-13: afabiani <a href="http://github.com/geonode/geonode/commit/2c71e9bbe0a15cc48ed9ef87cb3d638b2701c3ae" target="blank">  - Fix GeoServer Signals</a></li> 
<li> 2018-11-13: afabiani <a href="http://github.com/geonode/geonode/commit/167612d09b22657252419866d7e58dccd060fcfe" target="blank">  - Fix GeoServer Signals</a></li> 
<li> 2018-11-13: afabiani <a href="http://github.com/geonode/geonode/commit/07c0979204e6cec639194c417bbafb1d3d4bb0f2" target="blank"> [Closes #4077] Update Celery and Kombu libraries</a></li> 
<li> 2018-11-13: afabiani <a href="http://github.com/geonode/geonode/commit/142d229da2c7c0a97ee1cef28bb20059d43917f2" target="blank"> [Closes #4077] Update Celery and Kombu libraries</a></li> 
<li> 2018-11-13: afabiani <a href="http://github.com/geonode/geonode/commit/c426074b7f6321b9f9a2b4477990a12003f454b3" target="blank">  - Allow multiple Style Legends</a></li> 
<li> 2018-11-13: afabiani <a href="http://github.com/geonode/geonode/commit/0594b52cc729e5bfd7242abdc459ef23f1a47ac8" target="blank">  - Allow multiple Style Legends</a></li> 
<li> 2018-11-13: afabiani <a href="http://github.com/geonode/geonode/commit/2db58b68daf1bba8a6cb1bf402ddd89abfa40285" target="blank"> [Fixes #4075] GeoServer REST Proxy cannot handle SLD DELETE and POST if no SLD body has been provided</a></li> 
<li> 2018-11-13: afabiani <a href="http://github.com/geonode/geonode/commit/d632dda1e0a01ea0f67771041a4b3e2011097970" target="blank"> [Fixes #4075] GeoServer REST Proxy cannot handle SLD DELETE and POST if no SLD body has been provided</a></li> 
<li> 2018-11-13: Hisham waleed karam <a href="http://github.com/geonode/geonode/commit/99799ee03284155ce02cb252640b1c603b8983fd" target="blank"> fix ident_json view</a></li> 
<li> 2018-11-12: capooti <a href="http://github.com/geonode/geonode/commit/7df535c0606c6ac392400ffe8434c8d3ddd2181d" target="blank"> [worldmap-client] Improvements and fixes on the Gazetteer. Fixes #4072.</a></li> 
<li> 2018-11-09: capooti <a href="http://github.com/geonode/geonode/commit/6c3dba0731c5393e405e4fb6decf805488ffcc9f" target="blank"> Localize some strings in the worldmap composer</a></li> 
<li> 2018-11-09: capooti <a href="http://github.com/geonode/geonode/commit/86ed18176c6df6a2277fd183d711368d2d21c40a" target="blank"> Fixes #4068: remove duplicate keywords field in adanced metadata editing</a></li> 
<li> 2018-11-09: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/f274add56308886bf898ff9eff5bdf5801df0bfd" target="blank">  - Allow pluggable GIS client to hook their custom Style Edit Page (#4067)</a></li> 
<li> 2018-11-09: afabiani <a href="http://github.com/geonode/geonode/commit/8f1f4cbbae89ac136a098311dd9e028e77c8d762" target="blank">  - Allow pluggable GIS client to hook their custom Style Edit Page</a></li> 
<li> 2018-11-09: capooti <a href="http://github.com/geonode/geonode/commit/ae7829621ceae7b0b779d003a2ba2e1a5b145dbc" target="blank"> Fixes #4064: resources sort broken on Firefox</a></li> 
<li> 2018-11-09: afabiani <a href="http://github.com/geonode/geonode/commit/442841765fda8c5a7d4f3ce9999cf6f349aeccfd" target="blank">  - Filter Remote Services Links to the REST MAP</a></li> 
<li> 2018-11-09: afabiani <a href="http://github.com/geonode/geonode/commit/62601ddef9fc572763ffb2134268f4e5a797d13c" target="blank">  - Filter Remote Services Links to the REST MAP</a></li> 
<li> 2018-11-09: afabiani <a href="http://github.com/geonode/geonode/commit/e67ec9b265647d378bf4b77a4f77ada3c448144b" target="blank">  - fix localsettings sample</a></li> 
<li> 2018-11-08: capooti <a href="http://github.com/geonode/geonode/commit/d185e6acb548122d5e7deffcda1a6cdda6308ddc" target="blank"> Disable numeric fields from feature search. Fixes #4062</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/1ce497a1e486c81ac90580068d04bc6573e7f9f0" target="blank">  - Fix tests</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/a1bf0ac4bd238de4edbc076631a1dbe4a2d5c830" target="blank">  - Improve Thumbnail method so that it can include a background also [Refers #3982]</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/fcd711fb0731a71067a752db6102a9820c099c87" target="blank">  - set to completed step to check if no _ALLOW_TIME_STEP is false [Refers #3800]</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/d5aa2dfdb198a778e8eb845a6134487f623f2c4b" target="blank">  - Cleanup local_settings.py.geoserver.sample</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/e8f10275a5842e6957f678cfec2ad2c923043ca9" target="blank">  - upload_session.completed_step = 'time' if _ALLOW_TIME_STEP else 'check'</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/53386cc0e4edc8b298eb999a7506818b117b6b39" target="blank">  - upload_session.completed_step = 'time' if _ALLOW_TIME_STEP else 'check'</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/b498dff65115c68c8d8575724dd815c3c4a8cd6b" target="blank">  - upload_session.completed_step = 'time' if _ALLOW_TIME_STEP else 'check'</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/8c000f6c0b530356a5355357b954953ed802c64a" target="blank">  - upload_session.completed_step = 'time' if _ALLOW_TIME_STEP else 'check'</a></li> 
<li> 2018-11-08: afabiani <a href="http://github.com/geonode/geonode/commit/b0edc880c6fa7d0a0c7528585783fbefebb8539c" target="blank">  - Thumbnail Generation call at "finished" messages only</a></li> 
<li> 2018-11-07: capooti <a href="http://github.com/geonode/geonode/commit/b8d37afed7683b4d893f34df9fbdf41016d3b1ea" target="blank"> [worldmap-client] Now attributes order is honored when identifying features. Fixes #4060</a></li> 
<li> 2018-11-07: Paolo Corti <a href="http://github.com/geonode/geonode/commit/3aa488b07c4f835a27c928c8393b1ed0c7409655" target="blank"> [Worldmap client] Uses now WFS for GetFeatureInfo only if user has download permissions. Otherwise uses WMS. Fixes #4058 (#4059)</a></li> 
<li> 2018-11-07: afabiani <a href="http://github.com/geonode/geonode/commit/efbc41c4e767a5240d776952e188bd5fda5ef60a" target="blank">  - Settgins Optimizations</a></li> 
<li> 2018-11-07: afabiani <a href="http://github.com/geonode/geonode/commit/51336d38e9c06acd167716214db86bb05adf52f5" target="blank">  - Fix resource api exception</a></li> 
<li> 2018-11-07: afabiani <a href="http://github.com/geonode/geonode/commit/f9e85b4e0f177472236923b7332e915e897fa9fd" target="blank">  - Fix resource api exception</a></li> 
<li> 2018-11-06: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/61635b5770182ee9f9fca4f8536b48796a18989f" target="blank"> Fixes some broken links as per #4047 (#4055)</a></li> 
<li> 2018-11-06: afabiani <a href="http://github.com/geonode/geonode/commit/dbf42d6c73dfbe45a8b07e4ad20420d7492fddc3" target="blank">  - JS siteUrl trailing slash if not present</a></li> 
<li> 2018-11-06: afabiani <a href="http://github.com/geonode/geonode/commit/d656a6b935e8661763e05e2e48c84b09c274c7b5" target="blank">  - JS siteUrl trailing slash if not present</a></li> 
<li> 2018-11-06: afabiani <a href="http://github.com/geonode/geonode/commit/1ebc390f1e650f3c2237ba36acc75fe9c9234ea3" target="blank">  - Make sure only layers have been added to the cart session</a></li> 
<li> 2018-11-06: afabiani <a href="http://github.com/geonode/geonode/commit/85e66b5a8f677992a1e2cd613a73cbff9746139c" target="blank">  - Make sure only layers have been added to the cart session</a></li> 
<li> 2018-11-06: afabiani <a href="http://github.com/geonode/geonode/commit/045853bc725291e4546f871e42d773f40a2244ce" target="blank">  - Update static libs</a></li> 
<li> 2018-11-06: afabiani <a href="http://github.com/geonode/geonode/commit/c15fd3a384ad232aa9a689c85ca3f2c2915b0f67" target="blank">  - Update static libs</a></li> 
<li> 2018-11-06: afabiani <a href="http://github.com/geonode/geonode/commit/16b4d0b698db409d4e5b979ab75e6adf522566b2" target="blank">  - Fix security test cases</a></li> 
<li> 2018-11-05: capooti <a href="http://github.com/geonode/geonode/commit/d18233b75ba06fa60c578539e2ca1b6a822741e9" target="blank"> Fixes #4056 (uncorrectly set WPS in sync_geofence_with_guardian)</a></li> 
<li> 2018-11-05: afabiani <a href="http://github.com/geonode/geonode/commit/774ffaec3c7cefbf26a53cbee87f75ff3eea5e1f" target="blank"> Fixes some broken links as per #4047</a></li> 
<li> 2018-11-05: afabiani <a href="http://github.com/geonode/geonode/commit/0cc891cf323e8d68c5ce5edd6ccf2f4ac018ffe1" target="blank">  - minor update to local_settings geoserver sample</a></li> 
<li> 2018-11-05: afabiani <a href="http://github.com/geonode/geonode/commit/52cd17a293cf912b9d277ca62bb708765de093f7" target="blank"> [Fixes #4053] save map broken on 2.8 branch?</a></li> 
<li> 2018-11-01: capooti <a href="http://github.com/geonode/geonode/commit/05d2ab2fb9b3d5ee089b758264703a285cc940c3" target="blank"> Avoid duplication of layers when using link (snapshots) in worldmap client. Refs #4046</a></li> 
<li> 2018-10-31: capooti <a href="http://github.com/geonode/geonode/commit/d5ec8c740c3be30b73537a1775f18438c2aa2070" target="blank"> Fixes layers duplication introduced with a snapshot. Refs #4046</a></li> 
<li> 2018-10-31: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/cc94e8211b14a861a7aa564fe144194c017f9630" target="blank"> [Fixes #4025] Regression with uploading a shapefile with no ascii characters (#4026)</a></li> 
<li> 2018-10-31: afabiani <a href="http://github.com/geonode/geonode/commit/163f606ba38d1f7aadcd53e11bca831ebec92e9d" target="blank">  - Fix test cases</a></li> 
<li> 2018-10-31: afabiani <a href="http://github.com/geonode/geonode/commit/89e486350a7f88834201d66013efce1f39f52c17" target="blank">  - Rename columns of non-UTF-8 shapefiles attributes before ingesting</a></li> 
<li> 2018-10-31: afabiani <a href="http://github.com/geonode/geonode/commit/671c250b81ae7d05933825a7f0d6482f65f7c267" target="blank">  - Rename columns of non-UTF-8 shapefiles attributes before ingesting</a></li> 
<li> 2018-10-30: Paolo Corti <a href="http://github.com/geonode/geonode/commit/ff92a009c5ffaa771df7e5e72df69ce8481c9c85" target="blank"> Fixes #4044 (broken comments when using worldmap client) (#4045)</a></li> 
<li> 2018-10-30: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/7ee5ef97258358a48f7262ad4200fd31bb7f9b7e" target="blank"> [Fixes #4040] GeoServer SLD POST may fail if style does not already exist locally. (#4041)</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/5fcdaaad9bd04cb5c1702931bf964fb974c0a4df" target="blank">  - Fix test cases</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/ffad0fc665a8303fb18b427652031bbfc051db7d" target="blank"> [Fixes #4025] Regression with uploading a shapefile with no ascii characters</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/231e535ef6cef51afa3eccc4417775f1ce08b324" target="blank"> [Fixes #4039] GeoNode 'proxy' removes original url netloc from the underlying request</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/34f2ff27cea4c7e12d57aaa2ca150602c436dd94" target="blank"> [Fixes #4038] Remove Django deps known vulnerabilities #4038</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/b8ad39508b39de54ec6ff59ea52b068af7d4d3b3" target="blank">  - Fix test cases</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/feb36591d3ac76f8cd6693382806aeb2de20919c" target="blank">  - Proxy Improvements</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/309a71920f6abc00c17ff199e75cfb0ca77e652a" target="blank">  - Python vulnerabilities</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/52d7c1b384d652c098dc952587dae53f1be313e7" target="blank">  - Fix test cases</a></li> 
<li> 2018-10-30: capooti <a href="http://github.com/geonode/geonode/commit/845c0734c0dde0345f39b60f6c0e34e52c57cec1" target="blank"> Fixes #4036</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/d62e73428c27aef2cca3f971bd7fd3c17bb8e591" target="blank">  - Fix test cases</a></li> 
<li> 2018-10-30: Paolo Corti <a href="http://github.com/geonode/geonode/commit/88c31d2e5a135b2ac2a2b3079272443880104fae" target="blank"> Fixes #4031 (#4032)</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/035c079a72047f237a0bb2c28ac084195e4a39b4" target="blank">  - Fix test cases</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/79006563a5b2b2bbed365a4b8d53877d8d5c9a9c" target="blank">  - Fix test cases</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/9920f07c457567ad95ff0ee2ca2bb80c6dceafdf" target="blank">  - fix test cases</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/2a87e30ccac294a6f180d444f162cbd6a56bbcd8" target="blank"> [Fixes #3775] Hard-coded urls to static-files and media-files - rebuild js boundles</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/ef2fa540459317fad93220fedd4f21eb9e2d3379" target="blank"> [Fixes #3775] Hard-coded urls to static-files and media-files - rebuild js boundles</a></li> 
<li> 2018-10-30: afabiani <a href="http://github.com/geonode/geonode/commit/8eb7bc00164e5a83d217eb73c5572fdafaf13cc7" target="blank"> [Fixes #3775] Hard-coded urls to static-files and media-files</a></li> 
<li> 2018-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/fdfbe95eb5f5497f54dbfe44ec096ce5a23480ed" target="blank"> [Refers #3775] Hard-coded urls to static-files and media-files</a></li> 
<li> 2018-10-29: capooti <a href="http://github.com/geonode/geonode/commit/ce70da9380a91dadf87bf0104163a984b5ead4f5" target="blank"> Fixes #4033</a></li> 
<li> 2018-10-30: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/fd8666b853faca173f4ce094303a4b91f1d08d60" target="blank"> [Closes #4029] Metadata Download Link for RemoteServices should report the Service Type instead of a generic 'http-download' (#4030)</a></li> 
<li> 2018-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/5e9fa80c611ea8d139613c901edfe495105bb929" target="blank"> [Refers #3775] Hard-coded urls to static-files and media-files</a></li> 
<li> 2018-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/3663472e9d5d21bf9bbef71ca2bc95362021d69e" target="blank"> [Refers #3775] Hard-coded urls to static-files and media-files</a></li> 
<li> 2018-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/bd3bba574e54fc6742e62345bbcf63819a541dfd" target="blank"> [Fixes #4025] Regression with uploading a shapefile with no ascii characters</a></li> 
<li> 2018-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/ac64c41f364ae5c5fd33531311ae1dac81fecddb" target="blank"> [Fixes #4025] Regression with uploading a shapefile with no ascii characters</a></li> 
<li> 2018-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/9cdc5287d0932b19b2bea47dbfeed0b48827880c" target="blank">  - Push RemoteService Type on DownloadLinks Metadata</a></li> 
<li> 2018-10-29: afabiani <a href="http://github.com/geonode/geonode/commit/5afb5ad1ee91bf5f85b798d16d2a39d6ddf5c265" target="blank"> [Fixes #4025] Regression with uploading a shapefile with no ascii characters</a></li> 
<li> 2018-10-26: Paolo Corti <a href="http://github.com/geonode/geonode/commit/aba1eb7e857f9f4764381cdcec6d57b770d7e8d9" target="blank"> Manage worldmap client using client hooksets standard approach. Refs #4019 (#4023)</a></li> 
<li> 2018-10-26: afabiani <a href="http://github.com/geonode/geonode/commit/89efc19d6234572605182dfb67d81032242b14f1" target="blank">  - fix test cases</a></li> 
<li> 2018-10-26: afabiani <a href="http://github.com/geonode/geonode/commit/34ac6347e82c54484fe04892536bd2ce435d4a01" target="blank">  - fix test cases</a></li> 
<li> 2018-10-26: afabiani <a href="http://github.com/geonode/geonode/commit/c74bfd1863f5ca0fd7c446c6f2187f733c096691" target="blank">  - general security and encoding updates</a></li> 
<li> 2018-10-26: afabiani <a href="http://github.com/geonode/geonode/commit/a0c16cd0b49b84b3c3d7705de390684a48acb3c7" target="blank"> [Regression] View only perm does not works on GeoServer as espected because guardian always inserts a * * rule on GeoFence</a></li> 
<li> 2018-10-26: afabiani <a href="http://github.com/geonode/geonode/commit/b77962ab7bfdcf903f98035214ee28891ab9d5e1" target="blank"> [Regression] View only perm does not works on GeoServer as espected because guardian always inserts a * * rule on GeoFence</a></li> 
<li> 2018-10-26: olivierdalang <a href="http://github.com/geonode/geonode/commit/7e284a4da30458f094786287e8abfff33be559d8" target="blank"> (readme) More details for migration steps</a></li> 
<li> 2018-10-26: olivierdalang <a href="http://github.com/geonode/geonode/commit/e03f3f6c3494f45d9c4c32ced5cd32abfe09f557" target="blank"> fix migrations instructions for older docker</a></li> 
<li> 2018-10-24: olivierdalang <a href="http://github.com/geonode/geonode/commit/7c9338dc5706ffcbb5e869f12d9af4289b7db99d" target="blank"> [spcgeonode] several modifications</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/b2c238a1e1e1ea65c252f5af9d6d56ee4a11538d" target="blank"> [Fixes #4017] Layer/Map Details Page does not parse the time dimension from the new 1.3.0 GetCapabilities</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/ac4d23d36112d958240193f40d32fc9e30d31d87" target="blank"> [Fixes #4017] Layer/Map Details Page does not parse the time dimension from the new 1.3.0 GetCapabilities</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/25b23d1ce25789d4e3913548682b14a2e5c87acb" target="blank"> [Fixes #4016] New thumbnail is not well centered</a></li> 
<li> 2018-10-23: afabiani <a href="http://github.com/geonode/geonode/commit/809fe4b43ae981d9b507a7fac6a4cb86852d9161" target="blank"> [Fixes #4016] New thumbnail is not well centered</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/0c67495fcdca7abb894986dbb7578e4dfda2759c" target="blank">  - regression: document upload fails since it is wrongly trying to purge GeoFence rules</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/4bc434ce91c45d5a81d6e051d9adf6de17ab5636" target="blank">  - regression: document upload fails since it is wrongly trying to purge GeoFence rules</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/f6462bbd5d97efe4edffcea2f3a6176b535e608a" target="blank">  - regression: document upload fails since it is wrongly trying to purge GeoFence rules</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/cf1627ef29b0b4582d864fa269ff5ff53bacd522" target="blank">  - minor changes</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/be6022e0ef3f26a74ed7b6696e0afc272a6d0589" target="blank"> [Fixes #4016] New thumbnail is not well centered</a></li> 
<li> 2018-10-24: afabiani <a href="http://github.com/geonode/geonode/commit/dbf548c231f0786c03b1e6616390cbf334bec690" target="blank"> [Fixes #4017] Layer/Map Details Page does not parse the time dimension from the new 1.3.0 GetCapabilities</a></li> 
<li> 2018-10-24: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/2ec52c92d2415f178a6c69e1a8a8c4fa700813ad" target="blank"> Update helpers.py</a></li> 
<li> 2018-10-24: kappu <a href="http://github.com/geonode/geonode/commit/95150d56a391bc8396bcae27984559802618c166" target="blank"> Thumb creation last fixes</a></li> 
<li> 2018-10-23: afabiani <a href="http://github.com/geonode/geonode/commit/88b3e14a5a5b562948d1baec8ee87a19d312d731" target="blank"> [Fixes #4016] New thumbnail is not well centered</a></li> 
<li> 2018-10-23: afabiani <a href="http://github.com/geonode/geonode/commit/54e212571ec3510d055bdff587d687157d23ff0b" target="blank">  - Make sure mercanitle does not hit Y -90/90</a></li> 
<li> 2018-10-23: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/de8a4351387385d5edb58c629b9932b0e6fbe070" target="blank"> Update utils.py</a></li> 
<li> 2018-10-23: olivierdalang <a href="http://github.com/geonode/geonode/commit/81dcd2560d7ff65a2325af373ae973f392d608ba" target="blank"> [spcgeonode] improve ci</a></li> 
<li> 2018-10-23: olivierdalang <a href="http://github.com/geonode/geonode/commit/071c24fcbf2038c9c6a6c6b2c525745f456cdf27" target="blank"> [spcgeonode] CI : use docker executor again and run tests</a></li> 
<li> 2018-10-22: olivierdalang <a href="http://github.com/geonode/geonode/commit/9ac5c90881dc5059f1bd35a8bd684b08a8cf312d" target="blank"> [spcgeonode] fix entrypoint perms for django (when mounted)</a></li> 
<li> 2018-10-23: olivierdalang <a href="http://github.com/geonode/geonode/commit/5712486947a348f1c77120285cff28546bf22945" target="blank"> [spcgenonode] remove secrets</a></li> 
<li> 2018-10-22: kappu <a href="http://github.com/geonode/geonode/commit/497fb6d01a9012f4fb907bce8be0bdb4d0bc61ec" target="blank"> Fixing thumb generation</a></li> 
<li> 2018-10-19: olivierdalang <a href="http://github.com/geonode/geonode/commit/0dfa9ccd8eedf9a7240afdb7262fa25a4a9d7bf9" target="blank"> [spcgeonode] integrate in main geonode repo</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/f107142da46ea147b08c6783ea3b0cb8b0fe3ed8" target="blank">  - Fix Upload Session encoding issues</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/f5665e6d3fcb686e47bf6e20d573724b96b7a1ea" target="blank">  - Fix Upload Session encoding issues</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/1a472fca86bff21f442f71e3916e5ac7fbe99804" target="blank">  - Fix Upload Session encoding issues</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/44d7e78b0f704beb5e24843db02b0b2175af4dcd" target="blank"> [Contrib] [Minor] - Update monitoring contrib app / remove vulnerabilities</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/681c2e77c2fbf501c6b7b205895441f4dc6fb319" target="blank"> [Contrib] [Minor] - Update monitoring contrib app / remove vulnerabilities</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/f736b00c1ccb68a285cab7471d2a6121a1f5ed0d" target="blank"> [Contrib] [Minor] - Update monitoring contrib app / remove vulnerabilities</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/ee9f6dacbf3f47be68e790581d67dfc83905d5ed" target="blank">  - thumb improvs</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/2c0674b3b0eb14a6335538b234277510f8c138e8" target="blank">  - thumb improvs</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/b63b0007f87c604fe0ab4a9e450953bb93367f27" target="blank">  - thumb improvs</a></li> 
<li> 2018-10-18: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/67a0bdb4272248a9251245e4b05591806f16bdc1" target="blank">  [Fixes #4011] Encoding Issues with Resource having non-UTF8 characters on title and/or "upload-sessions" (#4012)</a></li> 
<li> 2018-10-18: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/1cc9b7df2fd8bda88c089fe10a784e1100143f8f" target="blank">  [Fixes #4011] Encoding Issues with Resource having non-UTF8 characters on title and/or "upload-sessions" (#4012)</a></li> 
<li> 2018-10-18: afabiani <a href="http://github.com/geonode/geonode/commit/7ca4238f5008b4600839fb0ccb0b3f5ca33a1140" target="blank">  - fix travis</a></li> 
<li> 2018-10-18: Paolo Corti <a href="http://github.com/geonode/geonode/commit/942e286246111ff7b52d9cd2a8d85d05e30e7e2c" target="blank"> PR with Worldmap changes running on master (2.10.x) (#3998)</a></li> 
<li> 2018-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/457f2d5ae549e7873f63a0b68fdf1a84cd935f46" target="blank"> [Fixes #4011] Encoding Issues with Resource having non-UTF8 characters on title and/or 'upload-sessions'</a></li> 
<li> 2018-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/be97e5b561c6fb6a7444f5b7cc9dfa06858b6090" target="blank">  - fix travix build</a></li> 
<li> 2018-10-17: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/cca20abf551e7e21cf1a641313317d123c3d0848" target="blank"> Revert wrong commit</a></li> 
<li> 2018-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/e7e21620b6220dcd9b371ba16960f62f72ec325e" target="blank">  - Mitigate encoding issues for non-UTF-8 Resource names</a></li> 
<li> 2018-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/4b631e5b3dc5e2d3dc2a5e9e9bd957559625cee3" target="blank">  - fix travix build</a></li> 
<li> 2018-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/f2e38871b57314979ed978932717eebac0a0918e" target="blank"> [Backport to 2.8.x] Fix for #3872 - Theme refactoring</a></li> 
<li> 2018-10-17: afabiani <a href="http://github.com/geonode/geonode/commit/0740cb8240d30766ffbdc57a3cd7565e106c9bdf" target="blank"> [Backport to 2.8.x][Closes #4004] Allow to send json body request to {layers,maps}/<id>/thumbnail to regenerate the thumbnail</a></li> 
<li> 2018-10-17: olivierdalang <a href="http://github.com/geonode/geonode/commit/c24958f52f932e9a2e9be61ba5f85f32b84ba41f" target="blank"> Fix for #3872 - simplified implementation for homepage customization</a></li> 
<li> 2018-10-17: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/241847b47d352da7486228b9fb6636f37baef085" target="blank"> [Cumulative patch] - Backport minor fixes from master (#4006)</a></li> 
<li> 2018-10-17: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/069c33d2806b8779076929f10b96c9626046bc81" target="blank"> Fix #3999 (#4000)</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/5e13b79117f78fb9af0942424328026792877978" target="blank"> - fix travis build</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/bd47b5af9ab28ff96cd3cb2b02ba0cd765b60767" target="blank"> - fix travis build</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/638e3e318e1ed668037d21b2ec4c43e2bb0fe889" target="blank">  - fix travis build</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/3e7eea3aba7f7bda807c93cbc606f5d03348b3e5" target="blank"> [Cumulative patch] - Backport minor fixes from master</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/2baa67e516ccd6ba6f200b6808c6a32770654aeb" target="blank">  - fix travis build</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/66b5bf59358a6edd4c6afdc7a3bf8acea85ed679" target="blank">  - fix travis build</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/208352d7e4af8951ff1c49efd17013f1b5c6af94" target="blank">  - fix travis build</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/3c6e35c8ca0856737501a38f590d954cce505025" target="blank"> [Closes #4004] Allow to send json body request to {layers,maps}/<id>/thumbnail to regenerate the thumbnail</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/33293e3bbe8d732f639fd8ac958e63162400d3de" target="blank"> [Closes #4001] Typo on sync_with_guardian</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/b7f0bf15a93f7165c99caf334c3e4b3725b4455b" target="blank"> [Closes #4001] Typo on sync_with_guardian</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/1946d516a9a855931dc64b79748a70a12f363cba" target="blank">  - fix thumbs and gf rules</a></li> 
<li> 2018-10-16: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/ea674c91a32bd4b3c9f3619c022904c71f51a7ec" target="blank"> [Fixes #3993] Adding group access makes layer public (#3995)</a></li> 
<li> 2018-10-16: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/c89823e34969a63e456fa1082c85437e6d89f809" target="blank"> [Closes #3982] Improve Thumbnail method so that it can include a background also (#3997)</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/8419bf0bdb78982672ed96a2254b3c08e207553f" target="blank"> [Backport to 2.8.x][Fixes #3993] Adding group access makes layer public</a></li> 
<li> 2018-10-16: afabiani <a href="http://github.com/geonode/geonode/commit/dfb272f5c81b4e471101af5e60ed3006e0d2d37c" target="blank">  - Themes customization</a></li> 
<li> 2018-10-16: olivierdalang <a href="http://github.com/geonode/geonode/commit/6403291bf54408601fac156c4b184defb238cb9a" target="blank"> fix travis (to be squashed...)</a></li> 
<li> 2018-10-16: olivierdalang <a href="http://github.com/geonode/geonode/commit/ee96b58b82561ad1a1af26fe38b2c148d8f8dec3" target="blank"> fix... (to be squashed)</a></li> 
<li> 2018-10-16: olivierdalang <a href="http://github.com/geonode/geonode/commit/eb8b40631dac266089adb92c3c2df781a634b891" target="blank"> fix tests</a></li> 
<li> 2018-10-16: olivierdalang <a href="http://github.com/geonode/geonode/commit/c56422eea6007aa20fe95719a8aee913683e1bd4" target="blank"> tests</a></li> 
<li> 2018-10-16: olivierdalang <a href="http://github.com/geonode/geonode/commit/1f3d76660623ff607752a36314d45a7befbb92f4" target="blank"> remove unused identifier</a></li> 
<li> 2018-10-16: olivierdalang <a href="http://github.com/geonode/geonode/commit/e648a57b87f82fc7c619d33f5b921a925b74192e" target="blank"> formatting</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/2e73629c55ffa8fa20396b36b2015a18b9e5fa85" target="blank">  - Fix security test cases</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/eb0c913028f08eebf225880e358ac7ff156f969c" target="blank"> [Fixes #3987] GeoFence Management commands are not resilient to duplicated rules</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/8d9c33533398b69b74000dfccb4457f19a82ffde" target="blank"> [Fixes #3987] GeoFence Management commands are not resilient to duplicated rules</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/dec51c1aa7061fa3cd5d991d8452babcc6bf1352" target="blank"> [Fixes #3987] GeoFence Management commands are not resilient to duplicated rules</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/cc115153888dc9b4055d29aee22961a3c38bc686" target="blank"> [Backport to 2.8.x][Fixes #3987] GeoFence Management commands are not resilient to duplicated rules</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/b1564a36ace1ee80c7c14f943e67efa1167230d6" target="blank"> [Fixes #3987] GeoFence Management commands are not resilient to duplicated rules</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/dc2259b75677dda7ee351562a46413eae8d510c2" target="blank">  - Test cases</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/fb66405ee0acf595d39d8b9b03cf09c111d94805" target="blank"> [Fixes #3984] Recurring User 'None' Error Geofence/Geoserver</a></li> 
<li> 2018-10-15: afabiani <a href="http://github.com/geonode/geonode/commit/d821cb69af892a92157990ec48056f10a5bfa0a6" target="blank"> [Fixes #3984] Recurring User 'None' Error Geofence/Geoserver</a></li> 
<li> 2018-10-15: olivierdalang <a href="http://github.com/geonode/geonode/commit/1f6b9f6c7ed308026840addac08b4ac66ae6ee3c" target="blank"> [themes] several improvements</a></li> 
<li> 2018-08-31: olivierdalang <a href="http://github.com/geonode/geonode/commit/6b6b10efd64f5c702e4dfc23c339d89397f57375" target="blank"> simpler implementation for homepage customization</a></li> 
<li> 2018-10-14: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/9f0efbe4f1fbbbba35ce65aa58888b03d87a0f72" target="blank"> Update signals.py</a></li> 
<li> 2018-10-14: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/03c7948ab0d6b09bd75b992b2aaf4c6bcab12dc5" target="blank"> Update signals.py</a></li> 
<li> 2018-10-12: afabiani <a href="http://github.com/geonode/geonode/commit/e28560f0dd6a6dcc0f0a54d49493c89e7925dc9c" target="blank">  - fix naming</a></li> 
<li> 2018-10-12: afabiani <a href="http://github.com/geonode/geonode/commit/f43190c8e3366450f8201cb6251f5b5570dff1a7" target="blank"> [Closes #3982] Improve Thumbnail method so that it can include a background also</a></li> 
<li> 2018-10-12: afabiani <a href="http://github.com/geonode/geonode/commit/0f7cd61c532f290597990df2ba27558f1e2568bd" target="blank"> - improve render thumbnail procedure</a></li> 
<li> 2018-10-12: afabiani <a href="http://github.com/geonode/geonode/commit/787be665aab9602471de6ed781619e2171c497f0" target="blank">  - fix testscases</a></li> 
<li> 2018-10-11: afabiani <a href="http://github.com/geonode/geonode/commit/56984b610b5077f8e07fd1d72cb842bf1b353eaa" target="blank">  - improve render thumbnail procedure</a></li> 
<li> 2018-10-11: Ernest CHIARELLO <a href="http://github.com/geonode/geonode/commit/760cf69493873b51e533c5fb5da132068edb490d" target="blank"> Update setup_docker_compose.txt</a></li> 
<li> 2018-10-10: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/7a1f8ec96e1060e42dd38222cf9f3c1724753a14" target="blank"> pep8 issues</a></li> 
<li> 2018-10-09: mikefedak <a href="http://github.com/geonode/geonode/commit/3e99f9f97152ae3dec4f36f874388e7712327b69" target="blank"> Deny access to layers/documents</a></li> 
<li> 2018-09-25: Erwin Sterrenburg <a href="http://github.com/geonode/geonode/commit/24584f167f1d4d1643332c636fa802b9b6806fcc" target="blank"> set to completed step to check if no _ALLOW_TIME_STEP is false</a></li> 
<li> 2018-10-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/a735d7b9a2743f0435ce16fd32e8d1fcd9f61c43" target="blank"> [Fixes #3947] GeoWebCache Tiled Layer Cache explicit invalidation (#3949)</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/8901e7ef5835483916c9cdf02efd60a0df641631" target="blank"> [Fixes #3953] "bbox_to_projection" flips coords and does not honor the geonode convention [x0, x1, y0, y1]</a></li> 
<li> 2018-10-02: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/f3a8e4f1fb976a0032da65aa000f51d2ea6ff260" target="blank"> Update requirements.txt</a></li> 
<li> 2018-10-01: afabiani <a href="http://github.com/geonode/geonode/commit/4337f0ed4f35f5d6d8829273870d35e84875926f" target="blank"> [Fixes #3951] [Cross-site scripting test - Security related - Issue] Improvements to Tastypie paginator</a></li> 
<li> 2018-10-01: afabiani <a href="http://github.com/geonode/geonode/commit/7d9d9c6d0335070d35fa40ac556764c23f4f7569" target="blank"> [Closes #3948] WPS Endpoint should be exposed to non-protected proxy</a></li> 
<li> 2018-10-09: afabiani <a href="http://github.com/geonode/geonode/commit/4fd8e944dd3d9a46114bf56e8e3b849a867abc1d" target="blank">  - geofence rest endpoint 2.13.x compliant</a></li> 
<li> 2018-10-01: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/2e1dfe76f20d94b1d7f19cc69e29c2e99438b304" target="blank"> [Fixes #3945] GeoFence rules priority computation should be more accurate (#3946)</a></li> 
<li> 2018-09-27: afabiani <a href="http://github.com/geonode/geonode/commit/37601ba8b3264536c13e42e90cd8eddb7a0d5fd4" target="blank"> [Closes #3942] Make 'Edit data' link aware of the storeType</a></li> 
<li> 2018-09-25: afabiani <a href="http://github.com/geonode/geonode/commit/ca6767b00b35f468d889d95cf9cb73724b625b16" target="blank"> [Fixes #3919] fix updatelayers command</a></li> 
<li> 2018-09-25: afabiani <a href="http://github.com/geonode/geonode/commit/4f6e0a54a826367cfbe5fcd253a591c391b99e80" target="blank"> [Closes #3934] Missing OWS endpoints on GeoNode proxy</a></li> 
<li> 2018-10-08: afabiani <a href="http://github.com/geonode/geonode/commit/8796247ab567884aa6314cff8d8194b6fd840f95" target="blank">  - replace build server url</a></li> 
<li> 2018-09-25: afabiani <a href="http://github.com/geonode/geonode/commit/a2e8e74eb542e85620469d00b6d5d074b9b2249a" target="blank"> [Closes #3935] celery.log file based handler causing issues if not correctly configured</a></li> 
<li> 2018-10-09: afabiani <a href="http://github.com/geonode/geonode/commit/b7825ca0025d1a4813e738e09991c8be2a22254d" target="blank">  - Improve test coverage</a></li> 
<li> 2018-10-08: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/671455d9418f094b99715ce7a5cc463e85851748" target="blank"> [Fixes #3962] Remove Django vulnerabilties (#3963)</a></li> 
<li> 2018-10-08: afabiani <a href="http://github.com/geonode/geonode/commit/049b8951d1d9cf931d6b6fe3bf578c021761f613" target="blank">  - replace build server url</a></li> 
<li> 2018-10-04: afabiani <a href="http://github.com/geonode/geonode/commit/d1443e1963e10a4565c90f3ac7c23f20be814755" target="blank">  - disable codecov report on geosolutions branch</a></li> 
<li> 2018-10-04: afabiani <a href="http://github.com/geonode/geonode/commit/88449ce759af8d157889eb37fd7d14ea1b048610" target="blank"> [Closes #3957] Increase "geoserver" tests coverage</a></li> 
<li> 2018-10-04: afabiani <a href="http://github.com/geonode/geonode/commit/fabcd9808be93d11dfb9f46f3c137d2e2ab101b0" target="blank"> [Closes #3957] Increase "geoserver" tests coverage</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/84098e7f319d76cb5791933122484fe4d41c16dc" target="blank"> - codecov reports</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/a1540ab57fc51c0ff92359c7c41edf2f0189710a" target="blank">  - update .travis.yml</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/ee8317db5f6b3a35c3a8092e9420637479815ba8" target="blank">  - update .travis.yml</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/18516801550e60401bfb283f5cc12b7ed1492131" target="blank">  - update .travis.yml</a></li> 
<li> 2018-10-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/395644282aa9b45e62674c8dcc45fbeff9f9ecd1" target="blank"> Update README.rst</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/762ed2bb71059f2acb0f2ee6377e8646be4c985e" target="blank"> - codecov reports</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/f3d59df85a1d0a1569e42192bd422c9dd889cfbb" target="blank">  - codecov reports</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/26fe995893ee4566531ffefd069f20da537aa9f0" target="blank">  - fix test cases</a></li> 
<li> 2018-10-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/effb5f6585d3a1e650a584f7fc1b7253260bf0cc" target="blank"> [Fixes #3947] GeoWebCache Tiled Layer Cache explicit invalidation (#3949)</a></li> 
<li> 2018-10-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/b241b5d1d62a294c4654770f4ffcedb9c26eb1c1" target="blank"> Fix pep8 issues</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/93161371cd1ad40df0c2091caee74d76b8cfa12d" target="blank"> [Fixes #3954] [GeoServer 2.14.x Upgrade] Layer Capabilities 1.3.0</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/cc3829faa965ba11a347369d91ba841b437b4738" target="blank">  - Fix integration test_capabilities test cases</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/df49b5b675b29397a7622c1af6458071143fbc46" target="blank"> [Fixes #3953] "bbox_to_projection" flips coords and does not honor the geonode convention [x0, x1, y0, y1]</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/8274e3309f0e001475ebbd9910d26045377eccaa" target="blank"> - Fix bbox projection</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/5ca88c51841bf1d2863c22881f28f59f12955e0c" target="blank">  - Fix bbox projection</a></li> 
<li> 2018-10-03: afabiani <a href="http://github.com/geonode/geonode/commit/4a3c8d1f0548a0c9b38fcf1d55b7e8b2faed9189" target="blank">  - Fix integration test_capabilities test cases</a></li> 
<li> 2018-10-02: afabiani <a href="http://github.com/geonode/geonode/commit/af5f1cd512e29dab311e344c77b52c4d08f6b143" target="blank">  - Fix integration test_capabilities test cases</a></li> 
<li> 2018-10-02: afabiani <a href="http://github.com/geonode/geonode/commit/3fe7369770c7e4fc5574f00a1691d3eeec943e87" target="blank">  - Fix layer capabilities; WMS 1.3.0</a></li> 
<li> 2018-10-02: afabiani <a href="http://github.com/geonode/geonode/commit/828cd62b959d9e67ee146943c59f2f6febf72e71" target="blank">  - remove restricted dirty_state condition from catalog</a></li> 
<li> 2018-10-02: afabiani <a href="http://github.com/geonode/geonode/commit/1f01d2220fc5d86a9d22536f2f2d497d640cfc73" target="blank">  - Delayed GeoFence Security Rules Invalidation</a></li> 
<li> 2018-10-02: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/7474547860c36c161a9cb4a04461d7147830d8a5" target="blank"> Update requirements.txt</a></li> 
<li> 2018-10-01: afabiani <a href="http://github.com/geonode/geonode/commit/f48ca2438fdf830a87ab338981a526fe41562a7c" target="blank"> [Fixes #3951] [Cross-site scripting test - Security related - Issue] Improvements to Tastypie paginator</a></li> 
<li> 2018-10-01: afabiani <a href="http://github.com/geonode/geonode/commit/179f7bf44dbcd8219885efcbd0e6bed181a95831" target="blank"> [Closes #3948] WPS Endpoint should be exposed to non-protected proxy</a></li> 
<li> 2018-10-01: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/2f6093f63c6e6ba43c98f37e2ec32e44cdf540f8" target="blank"> [Fixes #3945] GeoFence rules priority computation should be more accurate (#3946)</a></li> 
<li> 2018-09-27: afabiani <a href="http://github.com/geonode/geonode/commit/565c139796555466e1e4a78d6603764ef0d1df3b" target="blank"> [Closes #3942] Make 'Edit data' link aware of the storeType</a></li> 
<li> 2018-09-26: afabiani <a href="http://github.com/geonode/geonode/commit/4eff1b6f5f2c411b6311237be5e793559f6c6c9b" target="blank">  - GeoFence rules checks on test cases</a></li> 
<li> 2018-09-26: afabiani <a href="http://github.com/geonode/geonode/commit/9c90d6aa78e3d8e37d1eda9515b3afcab1ccaf58" target="blank">  - GeoFence rules checks on test cases</a></li> 
<li> 2018-09-25: Erwin Sterrenburg <a href="http://github.com/geonode/geonode/commit/a3bcaf011eadc8567e4e78e877eab52d171e6170" target="blank"> set to completed step to check if no _ALLOW_TIME_STEP is false</a></li> 
<li> 2018-09-25: afabiani <a href="http://github.com/geonode/geonode/commit/55f2be399e4bbfd8cae3ef48449e5ce4848e66c7" target="blank"> [Fixes #3919] fix updatelayers command</a></li> 
<li> 2018-09-25: afabiani <a href="http://github.com/geonode/geonode/commit/a094b54334caddaed4fa2aefe045d0c065c9c929" target="blank"> [Closes #3934] Missing OWS endpoints on GeoNode proxy</a></li> 
<li> 2018-09-25: afabiani <a href="http://github.com/geonode/geonode/commit/683c1a3e29a435d2199373b63912c042a9321f17" target="blank"> [Closes #3935] celery.log file based handler causing issues if not correctly configured</a></li> 
<li> 2018-09-24: afabiani <a href="http://github.com/geonode/geonode/commit/9e786c7e59be4a4ea2b32c6e52e64abf98428b31" target="blank">  - Improving groups activity tests</a></li> 
<li> 2018-09-24: afabiani <a href="http://github.com/geonode/geonode/commit/6b3f4b26a7157ca2cd27c7bdc979b54900332c30" target="blank">  - Fixing groups test cases</a></li> 
<li> 2018-09-24: afabiani <a href="http://github.com/geonode/geonode/commit/156df4f5501540264ddbd5af59b2a2e5684f8afd" target="blank"> [Issue #3927] Switching to 2.8.x branch: enabling 2.8.x branch on .travis.yml</a></li> 
<li> 2018-09-24: afabiani <a href="http://github.com/geonode/geonode/commit/33b1ee3f93a04697d7995965e91fe9786b0f08d1" target="blank"> [Fixes #3929] Show documents also on Groups Activity Tabs</a></li> 
<li> 2018-09-24: afabiani <a href="http://github.com/geonode/geonode/commit/31dcab105a831292f8a47fadf5169eac8e769ed7" target="blank">  - Fix migrations</a></li> 
<li> 2018-09-24: afabiani <a href="http://github.com/geonode/geonode/commit/2e5d13e1e39fd094e35718fe9f20f3cf13132943" target="blank">  - Switching to 2.8.x branch</a></li> 
<li> 2018-09-19: Hisham waleed karam <a href="http://github.com/geonode/geonode/commit/d98a72abe4cd492f2dccfc7bbb22db29e0aab500" target="blank"> return layer styles in map json as a list</a></li> 
<li> 2018-09-19: Hisham waleed karam <a href="http://github.com/geonode/geonode/commit/2368a5e461a1a1179b3c1cafd9b5342670f67edb" target="blank">  fix for AttributeError("'str' object has no attribute 'username'",))</a></li> 
<li> 2018-09-19: gannebamm <a href="http://github.com/geonode/geonode/commit/fd7f9ca56897aa4234196d25aa2e78c183e8580a" target="blank"> fix missing '-get' in apt-get (#3918)</a></li> 
<li> 2018-09-13: afabiani <a href="http://github.com/geonode/geonode/commit/b51e38af9ab0fc3540e8324940665c4c84581efb" target="blank"> [Fixes #3914] [Remote Services] Mitigate name clashes for service names</a></li> 
<li> 2018-09-13: afabiani <a href="http://github.com/geonode/geonode/commit/bb6ead8a67449d2bf8e2863e6739b83ec628778d" target="blank"> [Fixes #3914] [Remote Services] Mitigate name clashes for service names</a></li> 
<li> 2018-09-07: afabiani <a href="http://github.com/geonode/geonode/commit/d3e7a08dd7f5309b8744f13ace92147631d5451f" target="blank">  - fix integration test cases  - GeoFence apis cleanup</a></li> 
<li> 2018-09-07: afabiani <a href="http://github.com/geonode/geonode/commit/7430e7e79f530f7af5fd26298882fd9352235bd2" target="blank">  Fix test cases and geofence model</a></li> 
<li> 2018-09-07: amefad <a href="http://github.com/geonode/geonode/commit/b8df0800532e7b284139e1faf68a86668b2c5d84" target="blank"> Remove old configuration for GeoServer security from docs (#3908)</a></li> 
<li> 2018-09-06: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/c96584fd8678816f2e7a18ffb90d4c4472539938" target="blank"> Revert and then apply Fix #3893 again (#3903)</a></li> 
<li> 2018-09-06: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/c9a78a9a7ac8920f311b8c0b26a0e9f464ca20b6" target="blank"> Fix #3893</a></li> 
<li> 2018-09-05: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/7718cb938290c78f9ab62f60561ee0fa8b9ae224" target="blank"> [Closes #3896] Add a sample docker-compose.override.localhost.yml to run docker-compose on localhost (#3897)</a></li> 
<li> 2018-09-05: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/625d0fa929648636f342b3c11ea68a28c72f770d" target="blank"> [Fixes #3890] wsgi.py should either check for local_settings (apt) and settings (docker)</a></li> 
<li> 2018-09-07: amefad <a href="http://github.com/geonode/geonode/commit/76093ef2b834f2d394f94375e290de696c71f974" target="blank"> Remove old configuration for GeoServer security from docs (#3908)</a></li> 
<li> 2018-09-06: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/66e3c7ed05c605805954da7bcc528d9ef1724b64" target="blank"> [2.7.x] Backport issue #3893 (#3904)</a></li> 
<li> 2018-09-06: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/c8182e773f3f7aa6ab537c2a537535d3ab261fcf" target="blank"> Revert and then apply Fix #3893 again (#3903)</a></li> 
<li> 2018-09-06: afabiani <a href="http://github.com/geonode/geonode/commit/45aae43f119f41c44b8ab7da637dbf9382328419" target="blank"> [Fixes #3900] [2.7.x] Fix py.test selenium tests</a></li> 
<li> 2018-09-06: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/eb3081b4269dad417b4ab3c6f5afb2ae7ab4a109" target="blank"> Fix #3893</a></li> 
<li> 2018-09-05: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/391d3ded421cc9b744e3428efdbbdbf1401e75c4" target="blank"> [Closes #3896] Add a sample docker-compose.override.localhost.yml to run docker-compose on localhost (#3897)</a></li> 
<li> 2018-09-05: afabiani <a href="http://github.com/geonode/geonode/commit/e223bb3888958beceee94724f437df9ace86f400" target="blank"> [Fixes #3894] [2.7.x] docker-compose.yml should point to the 2.7.x image and not the latest one</a></li> 
<li> 2018-09-05: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/901ea4a76abe9a1e93615fc1bc28bb68c5191971" target="blank"> [Fixes #3890] wsgi.py should either check for local_settings (apt) and settings (docker)</a></li> 
<li> 2018-09-05: afabiani <a href="http://github.com/geonode/geonode/commit/25b7a190be73152986a0cb7c27fd42c5bd27103c" target="blank">  - fix integration test cases</a></li> 
<li> 2018-09-04: afabiani <a href="http://github.com/geonode/geonode/commit/f864701d61add6d50c95841e3dfd21c002af4f8b" target="blank"> [Fixes #3886] Remove javascript packages vulnerabilities</a></li> 
<li> 2018-09-04: afabiani <a href="http://github.com/geonode/geonode/commit/78f29a16ce3ff64c5196da645e4b603351d393c1" target="blank"> [Fixes #3884] Update GeoServer to 2.14.x on master</a></li> 
<li> 2018-08-31: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/bc2ad9951561231a53b2aebad6fcec12ebdeb9cb" target="blank"> Removing "requirements.txt" known vulnerabilities</a></li> 
<li> 2018-08-31: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/4ff5e5569af25844d77bc097aba95b3999262780" target="blank"> Py.Test BDD - Fix splinter and selenium versions</a></li> 
<li> 2018-08-28: Simone Dalmasso <a href="http://github.com/geonode/geonode/commit/fbef4523cf73196ad8a6b5ecddeb55bb2401ba1d" target="blank"> update geonode-updateip to use the new flags</a></li> 
<li> 2018-08-28: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/995bd661293aa1a0dcd2773ad81bcceedd9cc481" target="blank"> [Fixes #3874] sudo geonode-updateip fails on fresh Ubuntu 16.04 install</a></li> 
<li> 2018-08-28: Simone Dalmasso <a href="http://github.com/geonode/geonode/commit/050b71c7f1017a938dd1d6683a16ebf73296c580" target="blank"> add docs for the new flags of updateip</a></li> 
<li> 2018-08-28: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/209099eb28644af8fa5d8bf5d40e758cba1a5683" target="blank"> 2.10rc4</a></li> 
<li> 2018-08-28: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/274834af27a2db3d02f7696624aa9ecd80ec7916" target="blank"> Updated changelog for version 2.10rc4</a></li> 
<li> 2018-08-23: geo <a href="http://github.com/geonode/geonode/commit/741102211060cf47556d602b311fd84211bd253c" target="blank"> 2.10.0 rc3</a></li> 
<li> 2018-08-23: geo <a href="http://github.com/geonode/geonode/commit/31838d893660630557d06fc03bbe1d7af64179ef" target="blank"> Updated changelog for version 2.10rc2</a></li> 
<li> 2018-08-23: geo <a href="http://github.com/geonode/geonode/commit/3cdc7795c83eef225adc234500512726b31ff34c" target="blank"> 2.10.0 rc2</a></li> 
<li> 2018-08-23: geo <a href="http://github.com/geonode/geonode/commit/699c8e154866354632df3197be6489abf403ef0e" target="blank"> 2.10.0 rc2</a></li> 
<li> 2018-08-23: geo <a href="http://github.com/geonode/geonode/commit/ca8705976c089c3486c0b5a28cd954a3a2737981" target="blank"> Updated changelog for version 2.10rc1</a></li> 
<li> 2018-08-23: geo <a href="http://github.com/geonode/geonode/commit/9b16b98bc2e95a507db6907aa186eae921c1d0cc" target="blank"> 2.10.0 rc1</a></li> 
<li> 2018-08-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/51e6253abcf4a99df4c381b1c3795f922459fb3b" target="blank"> 2.10.0 rc0</a></li> 
<li> 2018-08-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/e1a17e39f7e06a71bad5bffd3cfcf21300355a56" target="blank"> 2.10.0 rc0</a></li> 
<li> 2018-08-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/00471c2bd8d1ed5e174fdc7440a03d25c59dacd6" target="blank"> 2.8.1 release</a></li> 
<li> 2018-08-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/15d9557a02365146267f761db7507aca3266127f" target="blank"> Updated changelog for version 2.8.1rc0</a></li> 
<li> 2018-08-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6896a41be4490df766c4cae69d57498ba54db7f8" target="blank"> 2.8.1 release</a></li> 
<li> 2018-08-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/62bc2f97eb1dbca3220586a0271332efc75f88cf" target="blank"> Backporting PRs fixes from master: https://github.com/GeoNode/geonode/pull/3866 https://github.com/GeoNode/geonode/pull/3865 https://github.com/GeoNode/geonode/pull/3864</a></li> 
<li> 2018-07-31: capooti <a href="http://github.com/geonode/geonode/commit/1e2fdc228623b85a9a619d09396555a3c0ce3a0f" target="blank"> Now there is not a local_settings.py file, so we need to set DATABASES when using worldmap application</a></li> 
<li> 2018-07-31: capooti <a href="http://github.com/geonode/geonode/commit/81f44237f329b40e2adb5f864104525130989da3" target="blank"> Includes commands in Makefile to create and remove databases needed when using the worldmap contrib application</a></li> 
<li> 2018-07-31: afabiani <a href="http://github.com/geonode/geonode/commit/dfa999fdb079fc0df0b758365d9d7b1d07f7d145" target="blank">  - #3180 restoring angular 1.4.0</a></li> 
<li> 2018-07-31: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/c509aa1d73c30ed77e07f90e27731ca0a42c9f7e" target="blank"> allow long item titles to break without whitespace</a></li> 
<li> 2018-07-31: afabiani <a href="http://github.com/geonode/geonode/commit/5d53e71520d5d3dc1afd4b8d19708bf78b30b6f8" target="blank">  - #3180 restoring angular 1.4.0</a></li> 
<li> 2018-07-28: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/9c5035f5bd1276598429f3038dc0bff2d7dc6be9" target="blank"> prevent change of height on cart item hover</a></li> 
<li> 2018-07-27: capooti <a href="http://github.com/geonode/geonode/commit/f9fae7deafd93d8dde6868ceb2e3367ee0c337a7" target="blank"> Ported the mobile client as per #404</a></li> 
<li> 2018-07-27: afabiani <a href="http://github.com/geonode/geonode/commit/5516a184b5bf6b93d45c42d8dc9d9bb26ae32be6" target="blank">  - Fix typo</a></li> 
<li> 2018-07-27: afabiani <a href="http://github.com/geonode/geonode/commit/8734dfe8da1302bdf57c1fccb5f9fb2b2466f389" target="blank">  - Fix typo</a></li> 
<li> 2018-07-27: afabiani <a href="http://github.com/geonode/geonode/commit/19f80f9e42136052c6decafa7cc62ab39bf95fa8" target="blank"> Backport fixes from master</a></li> 
<li> 2018-07-27: afabiani <a href="http://github.com/geonode/geonode/commit/2a17f205d6bbc852649bcd9296eba00737e47eb0" target="blank">  - Minor hardening on Map configuration stuff</a></li> 
<li> 2018-07-27: afabiani <a href="http://github.com/geonode/geonode/commit/6a16176ac57489d78bd0aa1870abb8436b0680d8" target="blank">  - Fix integration tests</a></li> 
<li> 2018-07-26: afabiani <a href="http://github.com/geonode/geonode/commit/a7b49d60fe457b0c672e98967c9017f81eb957d6" target="blank"> Backport fixes from master</a></li> 
<li> 2018-07-26: afabiani <a href="http://github.com/geonode/geonode/commit/ae30503c267e977f294972db6dc2d4a0dda6d16c" target="blank">  - Fix QGis integration tests</a></li> 
<li> 2018-07-26: afabiani <a href="http://github.com/geonode/geonode/commit/b5dac894d6cee47d12ce05da2b9cdfd1cf1f4aa1" target="blank">  - Fix QGis integration tests</a></li> 
<li> 2018-07-25: afabiani <a href="http://github.com/geonode/geonode/commit/bd18aac335e081bf8e7b75113d7de644db2fe48d" target="blank">  - Fix QGis Server Integration Tests</a></li> 
<li> 2018-07-25: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/32edbf5154942a81aed52b91c7ea2dbf935b4144" target="blank"> changed readme to rst with extension and changed setup.py</a></li> 
<li> 2018-07-25: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/8fd79f941e958d2dd4325801637ce64c1a22e9ba" target="blank"> submission of new readme for github</a></li> 
<li> 2018-07-25: afabiani <a href="http://github.com/geonode/geonode/commit/3fec66ff4240a0e7ebea2c973fb90ff2b1096188" target="blank"> Backport fixes from master</a></li> 
<li> 2018-07-25: afabiani <a href="http://github.com/geonode/geonode/commit/fef4dfff241e88dd1cba404eb5cd45ad362fa1fa" target="blank">  - Fix QGis Server Integration Tests</a></li> 
<li> 2018-07-25: afabiani <a href="http://github.com/geonode/geonode/commit/64b2231070ce87ee0a57e23d11117b6d6fbc2cee" target="blank">  - Updating ElasticSearch dependencies</a></li> 
<li> 2018-07-25: Boney Bun <a href="http://github.com/geonode/geonode/commit/1e854d4b674f59298f9a715ae6af34685fee8818" target="blank"> fix a srid bug when uploading vector layers</a></li> 
<li> 2018-07-24: afabiani <a href="http://github.com/geonode/geonode/commit/0f43f323cf315fd2e224cc3bb978a31a8c95a90d" target="blank">  - Updating ElasticSearch dependencies</a></li> 
<li> 2018-07-24: afabiani <a href="http://github.com/geonode/geonode/commit/c1a49147f73fa8cf90ee6137c30153b7d351cfac" target="blank">  - Remove circular local_settings import</a></li> 
<li> 2018-07-24: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/2a1c59b4fa5f7c67663343663886b5b0394685bb" target="blank"> centered magnifier in big search and aligned metadata checkbox</a></li> 
<li> 2018-07-24: afabiani <a href="http://github.com/geonode/geonode/commit/1bc9f4e472885df43f27832a5f44974685a39747" target="blank">  - Tentative fix geoserver docker compose</a></li> 
<li> 2018-07-24: afabiani <a href="http://github.com/geonode/geonode/commit/d1de73b16d495dff7ae4dca814ce6aadb8d9604e" target="blank">  - Tentative fix geoserver docker compose</a></li> 
<li> 2018-07-24: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/89649f623f758175c8f2ae635e105281ba3c5949" target="blank">  - Backporting fixes from master</a></li> 
<li> 2018-07-23: Hisham waleed karam <a href="http://github.com/geonode/geonode/commit/2decdaae4cfda4443856aab9106277dbeebdd13e" target="blank"> Update settings.py</a></li> 
<li> 2018-07-23: afabiani <a href="http://github.com/geonode/geonode/commit/3cfd575d51fc75ddeafde8f26ea2283f378770e2" target="blank">  - Backporting master branch fixes</a></li> 
<li> 2018-07-23: afabiani <a href="http://github.com/geonode/geonode/commit/c974131961d0135b6d0f16bbb39405192ea2f6dc" target="blank">  - Add storeType to Layers Capabilities response</a></li> 
<li> 2018-07-22: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/af3a1e048604ff3fc79c6d3ac64a5e496ab43a07" target="blank"> Backport #3856</a></li> 
<li> 2018-07-22: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/3a4076281b69b989427340dace9dbc0afa54c983" target="blank"> Add variable to set geoserver JAVA_OPTS</a></li> 
<li> 2018-07-21: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/96575c953578d39e153e7426c493849c94469d6e" target="blank"> Backport fix #3853</a></li> 
<li> 2018-07-21: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/9353e37dbc9a5e2439f0953fd7832b7e402d1b57" target="blank"> Fix #3853</a></li> 
<li> 2018-07-21: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/cd5addc4eda8e4e06aa3027dd6969131ea56e746" target="blank">  - MapLoom GIS client hooksets (#3851)</a></li> 
<li> 2018-07-21: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/8cd18100603738065872b375c4a643ecfb843b88" target="blank"> Added explanations regarding pygdal install #3784</a></li> 
<li> 2018-07-20: afabiani <a href="http://github.com/geonode/geonode/commit/ac7a0292e5ecf4ba38229bd62141a261daa6b9a0" target="blank"> - MapLoom GIS client hooksets</a></li> 
<li> 2018-07-20: afabiani <a href="http://github.com/geonode/geonode/commit/821beb2b662cd75f8c0778f241b09fdc6b13a4ac" target="blank"> - MapLoom GIS client hooksets</a></li> 
<li> 2018-07-20: afabiani <a href="http://github.com/geonode/geonode/commit/b745808de29eb9f949b120d9adb290ff08dc9e17" target="blank">  - Fix JS vulnerability</a></li> 
<li> 2018-07-20: afabiani <a href="http://github.com/geonode/geonode/commit/cf6965b367b2ddde2d984328849c9a946666dbb1" target="blank">  - MapLoom GIS client hooksets</a></li> 
<li> 2018-07-20: afabiani <a href="http://github.com/geonode/geonode/commit/7e4454a244efc6452ba34786d8fde28ced708175" target="blank"> Backport fixes from master branch</a></li> 
<li> 2018-07-20: afabiani <a href="http://github.com/geonode/geonode/commit/2af6c077f34df8babc462640effe478dc47312a6" target="blank">  - Fixing test-cases</a></li> 
<li> 2018-07-19: afabiani <a href="http://github.com/geonode/geonode/commit/97d7dd07a5ce6ed5abbc090e413bd45d3d1164c9" target="blank"> Update gsconfig and gsimporter versions</a></li> 
<li> 2018-07-19: afabiani <a href="http://github.com/geonode/geonode/commit/1009131c148992d621828c0c35662c3a39787b34" target="blank">  - Remove ws prefixed URL from links in order to publish a full DescribeLayer on Links</a></li> 
<li> 2018-07-19: afabiani <a href="http://github.com/geonode/geonode/commit/ceda548169db0e9253f61884d92803bfddeee51c" target="blank">  - Update gnimporter version</a></li> 
<li> 2018-07-19: afabiani <a href="http://github.com/geonode/geonode/commit/a5ed83ce41f06a37066b482406f4a2046cce4c6e" target="blank">  - Update gnimporter version</a></li> 
<li> 2018-07-16: giohappy <a href="http://github.com/geonode/geonode/commit/d71cc4ac1afbe22f00c8a4c0d0257db4ee81f408" target="blank"> fix GeoNode DB name in docker env</a></li> 
<li> 2018-07-15: giohappy <a href="http://github.com/geonode/geonode/commit/a7f5b031988e8553c25e8bb201260cb5ab648389" target="blank"> note on docker-compose up for Windows users (see #3709)</a></li> 
<li> 2018-07-14: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/a378b94cc44b382f6b4a8950775cd4052fa6ad39" target="blank">  - Backport fixes and PRs from master (#3846)</a></li> 
<li> 2018-07-13: afabiani <a href="http://github.com/geonode/geonode/commit/688497d1758309d94dab4b4268d8a51b934a39db" target="blank">  - Minor Layout improvements</a></li> 
<li> 2018-07-13: afabiani <a href="http://github.com/geonode/geonode/commit/e80319885122b9a038e92d8cc8b72c858c7015af" target="blank">  - Minor Layout improvements</a></li> 
<li> 2018-07-13: afabiani <a href="http://github.com/geonode/geonode/commit/edbfa648ce6ec94657ec279d0fe7d20926d7b4dc" target="blank">  - Minor Layout improvements</a></li> 
<li> 2018-07-13: afabiani <a href="http://github.com/geonode/geonode/commit/4b635efd12a8fc9294da25e663ee98bbe4e33c60" target="blank">  - Backport fixes and PRs from master</a></li> 
<li> 2018-07-13: afabiani <a href="http://github.com/geonode/geonode/commit/47af0584146bf36a3ebf1ae1384e668988807972" target="blank">  - Exclude public-invite groups from metadata choices</a></li> 
<li> 2018-07-13: afabiani <a href="http://github.com/geonode/geonode/commit/ed4ce3acc72beb0d9d0f35b76be29e18937e2cc8" target="blank"> [Fixes #3834] STATIC_URL vs static template tag</a></li> 
<li> 2018-07-12: afabiani <a href="http://github.com/geonode/geonode/commit/f6bcae545bb31b6a3fc64ac1d8d02798936a2e63" target="blank">  - Fixes issue #3843 - Fix vulnerability with Pillow dependency</a></li> 
<li> 2018-07-11: afabiani <a href="http://github.com/geonode/geonode/commit/7df99f25f124986da74e6a7ce2d869f9b2c5b17e" target="blank">  - backport from master</a></li> 
<li> 2018-07-11: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/be78df272db132260738ed729c09e8a2c891a2bd" target="blank"> Restrict use of Edit Document Button</a></li> 
<li> 2018-07-10: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/9a10a8df36558745e9a757a5461f370bd82596e3" target="blank"> corrected Ubuntu 14.04 to 16.04 in documentation</a></li> 
<li> 2018-07-10: Toni Schönbuchner <a href="http://github.com/geonode/geonode/commit/78f1d477b8b9f91f755c6af77afb1b288ec2a89f" target="blank"> added search input for styles to manage page</a></li> 
<li> 2018-07-07: afabiani <a href="http://github.com/geonode/geonode/commit/5869b40c1b1837df5cba2a8ed52b8ddc89e12910" target="blank">  - Fix max zoom issue</a></li> 
<li> 2018-07-07: afabiani <a href="http://github.com/geonode/geonode/commit/5761b91e3f460c5f7cf4f89a3f00df24c8db3cf2" target="blank">  - Fix max zoom issue</a></li> 
<li> 2018-07-05: geo <a href="http://github.com/geonode/geonode/commit/3b23fca2546a47eef50f5d78292dd153630e02c9" target="blank">  - Packagind scripts updates</a></li> 
<li> 2018-07-05: geo <a href="http://github.com/geonode/geonode/commit/1b4095a2607d31683cb71d594d38c751c0ad0c9d" target="blank">  - Packagin scripts updates</a></li> 
<li> 2018-07-05: geo <a href="http://github.com/geonode/geonode/commit/cc4bbe6719177f689696829ba6ee268acb8a4473" target="blank">  - Packagin scripts updates</a></li> 
<li> 2018-07-05: afabiani <a href="http://github.com/geonode/geonode/commit/4a95271ddefe1120a629ee6450cb33f5730fd0a6" target="blank"> [backport 2.7.x] Minor improvements: allow registered users to invite others / improve French translation</a></li> 
<li> 2018-07-05: afabiani <a href="http://github.com/geonode/geonode/commit/7069710572102f3057da039882113a279c03d6ce" target="blank">  - Improving French translations</a></li> 
<li> 2018-07-04: afabiani <a href="http://github.com/geonode/geonode/commit/d413250efeac17dd4ba4a04eaf3bbf1fada4105f" target="blank">  - Allow portal contributors to invite users</a></li> 
<li> 2018-07-03: Glenn Vorhes <a href="http://github.com/geonode/geonode/commit/4d7d14ae15fcd9904d71bcf28eb596b59048fdb6" target="blank"> add missing ast import</a></li> 
<li> 2018-07-03: Glenn Vorhes <a href="http://github.com/geonode/geonode/commit/fc4008c39ade446a10e68d4e5424e5fd087b1f8d" target="blank"> add missing ast import</a></li> 
<li> 2018-07-03: afabiani <a href="http://github.com/geonode/geonode/commit/a0279938b629631ce1db3b02d93ff800f25b0c31" target="blank">  - Fixes layer replace</a></li> 
<li> 2018-07-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/b98e102c3650bd6d03dd46bba05cd6807ad083d9" target="blank"> Update helpers.py</a></li> 
<li> 2018-07-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/f61bc8553bfc14753005255ef7d20a4692183433" target="blank"> Update helpers.py</a></li> 
<li> 2018-07-03: afabiani <a href="http://github.com/geonode/geonode/commit/515b8392bef322c02cde28dcfad2075eb0cd9dfb" target="blank">  - Fixes layer replace</a></li> 
<li> 2018-07-02: afabiani <a href="http://github.com/geonode/geonode/commit/0dfe7941e4f08f837a4ab5d9bd6ca88e89d8e37b" target="blank">  - Fixes layer replace</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/de7078339e1d6b0a288f53f4f72d955810e4f26f" target="blank">  - Fix kombu/messaging initialization</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/028047d473625174254d861bfdfde39a3ea3f278" target="blank"> - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/85ec5112a91a5219b0cb908609bd716fc7654c13" target="blank"> pep8 fixes</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/c67e5b8ff26303f7ea200a0a7ce9174f5883b3d3" target="blank"> - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/532bfbd3371c182cdef218a852668b4001df8dee" target="blank"> - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/f6d61ff2a42f90e3d23e506e196d3681139c2176" target="blank"> - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/4a4eb8feacf882fb23d707612eddb79b9297f4fd" target="blank"> pep8 fixes</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/8d32e289c1e8675bf6a5ace83872c9d809466a08" target="blank"> - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/2ccb0ed831ad1f71acff7879c670c0850a38e0e1" target="blank"> - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-28: afabiani <a href="http://github.com/geonode/geonode/commit/7c6e5e60bc6e34d6dd490571781bdb495d5c6170" target="blank"> - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/5a4db3d10b233fed83bae44c29a0a2dbe0d68bb8" target="blank"> pep8 issues</a></li> 
<li> 2018-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/cdab39a9fd67d71f675473c094c29924bcc6828b" target="blank"> pep8 issues</a></li> 
<li> 2018-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/a74a0ddc6d8921fac2cfedfeb849c4722e14492b" target="blank">  - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-27: afabiani <a href="http://github.com/geonode/geonode/commit/02b64cf2db5a9e893b346035693d09e20940f3ca" target="blank">  - Fix celery initialization when using GeoNode ad a depenency</a></li> 
<li> 2018-06-27: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/5af25906491406f3671afc0f4b2df6d112e6e01a" target="blank"> Externalize OGC TIMEOUT setting as ENV var</a></li> 
<li> 2018-06-27: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/75128b86ade951bc404cfdc88d7b702d31fdc17d" target="blank"> Externalize OGC TIMEOUT setting as ENV var</a></li> 
<li> 2018-06-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6fff0c0ed671a09c5c6389a18ad4b4f8037328c9" target="blank"> Update Dockerfile</a></li> 
<li> 2018-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/5bbbcaf3ffd3c24a30b3e9d2083f7ed4da49d235" target="blank">  - Backporting Docker Improvs and Fixes from master branch</a></li> 
<li> 2018-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/49ce37c72e8887a96949e95e5abbc673419c246d" target="blank">  - Docker make use of GeoServer Importer Uploader</a></li> 
<li> 2018-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/be9a7a40149b64dc21fe913be3963fe464bf53c1" target="blank">  - minor improvements geoserver helper</a></li> 
<li> 2018-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/dd002d4a7cd4a816ff15c01dc9cbf4926d3d3fb5" target="blank">  - Fix localhost docker compose var</a></li> 
<li> 2018-06-25: afabiani <a href="http://github.com/geonode/geonode/commit/5e289017e03999e809b23323c4d94ee2fa449349" target="blank">  - Tentative fix doscker-compose vars</a></li> 
<li> 2018-06-21: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/4c4e60c4c4d0c93985f7952746f68736c54fa7d3" target="blank">  - Backport stable fixes from master branch</a></li> 
<li> 2018-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/35cec0b544f6f9cd8f845238f4cad6d8afe65404" target="blank">  - Improve Map Embed Template and allow it passing through client hooksets</a></li> 
<li> 2018-06-21: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/edbbd733b8bf016086a4a8e3dd37a28b7a7f1bb2" target="blank">  - Backport stable fixes from master branch</a></li> 
<li> 2018-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/0756f0e9b633002cb234c4a23c421aaa1c9ce9b4" target="blank">  - Improve Map Embed Template and allow it passing through client hooksets</a></li> 
<li> 2018-06-21: afabiani <a href="http://github.com/geonode/geonode/commit/0df60c913edc3eb1a4685f4215730489364a12e9" target="blank">  - Updating the oauth2 toolkit dep version</a></li> 
<li> 2018-06-19: afabiani <a href="http://github.com/geonode/geonode/commit/983d2e648490302ab1dd83b834c5a44e33577fc0" target="blank">  - GeoNode Client Hooksets: allow client configuration tweaking from pluggable client library</a></li> 
<li> 2018-06-17: Francesco Bartoli <a href="http://github.com/geonode/geonode/commit/4da10180a7d616523406963d00d1953a0ebe7c9e" target="blank"> Don't raise an exception if variable is missing</a></li> 
<li> 2018-06-14: afabiani <a href="http://github.com/geonode/geonode/commit/9df16c60b33570373684ec9feb929b3c4cf971f1" target="blank">  - Update requirements: adding openssl deps</a></li> 
<li> 2018-06-14: afabiani <a href="http://github.com/geonode/geonode/commit/f195a0c53d17459df7e48ba535e7a46087936685" target="blank">  - Update requirements: adding openssl deps</a></li> 
<li> 2018-06-13: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/1f3978caa7bb741a03f10ea8f2d0b43aa4ca0ba2" target="blank"> [Fixes #3800] Uploading shapefiles without a datefield and time-enabled is False in importer settings fails in 2.7.x</a></li> 
<li> 2018-06-13: afabiani <a href="http://github.com/geonode/geonode/commit/65ab0d7a801af8a6dce8b9a5a90e360901e5bbd6" target="blank"> [Fixes #3800] Uploading shapefiles without a datefield and time-enabled is False in importer settings fails in 2.7.x</a></li> 
<li> 2018-06-12: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/878ac6efa373eec57fa5ce34255c5fb65bec11ab" target="blank">  - SITEURL rstrip (/) consistently</a></li> 
<li> 2018-06-12: afabiani <a href="http://github.com/geonode/geonode/commit/f4ff4c80ebeb949758fe70091622f243a0ce5f43" target="blank">  - SITEURL rstrip (/) consistently</a></li> 
<li> 2018-06-12: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/75baa8f62391ae98583c61122a2f6b7545aa2105" target="blank"> Backport from master branch</a></li> 
<li> 2018-06-11: afabiani <a href="http://github.com/geonode/geonode/commit/03e972ab59fc71aedb5b6b8904038a95b7322dc2" target="blank"> Improvements to PyCSW Constraints and Local Mappings</a></li> 
<li> 2018-06-11: afabiani <a href="http://github.com/geonode/geonode/commit/ce79021bbc694bb2291e1257f062e4a974e0ffb1" target="blank"> Improvements to PyCSW Constraints and Local Mappings</a></li> 
<li> 2018-06-07: giohappy <a href="http://github.com/geonode/geonode/commit/d4a8759540b1ef5ffa40ecb77ac246037a0140c6" target="blank"> Set default datastore from env for OGC server settings</a></li> 
<li> 2018-06-07: afabiani <a href="http://github.com/geonode/geonode/commit/e2dc1df675a4e84182e825e170312eeaa63c5243" target="blank"> Improvements to PyCSW Constraints and Local Mappings</a></li> 
<li> 2018-06-07: giohappy <a href="http://github.com/geonode/geonode/commit/e1b8386084dc8315b437e1101302b42601e0b804" target="blank"> value should be datastores key name, not value</a></li> 
<li> 2018-06-07: giohappy <a href="http://github.com/geonode/geonode/commit/56943548ddb9755e69e426d6f0775cebbe31e0ee" target="blank"> Set default datastore from env for OGC server settings</a></li> 
<li> 2018-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/304ac29ed3bdb95bbedd36ed5faf2a209a9a6455" target="blank"> [Backport fixes from master]</a></li> 
<li> 2018-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/b2c2789a46fbc74783a57375f0e85f1c34a5d71a" target="blank"> [Fw-port #3817] Implements GNIP #3718 (Worldmap contrib application)</a></li> 
<li> 2018-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/af5371385b8265bc5cf9a4c43641519449001467" target="blank"> [Backport fixes from master]</a></li> 
<li> 2018-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/abd6ac97cf37f2c32745294735de9210b7ba4379" target="blank"> [Fixes #3824] Manage style page show style name instead of title</a></li> 
<li> 2018-06-06: afabiani <a href="http://github.com/geonode/geonode/commit/117bbdccc38929216a4882999f586b3d51b4a0c4" target="blank">  - OIDC 1.0 compliancy / notifications fixes</a></li> 
<li> 2018-06-04: afabiani <a href="http://github.com/geonode/geonode/commit/e7ddf9a561e8738ac8cecdd695e29102fb523848" target="blank">  - OIDC 1.0 compliancy preparation: add api > UserInfo method</a></li> 
<li> 2018-06-02: Tim Sutton <a href="http://github.com/geonode/geonode/commit/096dc10299338cc1b4dd4a0e6730df23cc2d29bb" target="blank"> Fix issues where docker client may be incompatible with docker server API by forcing to APV version 1.24</a></li> 
<li> 2018-05-31: capooti <a href="http://github.com/geonode/geonode/commit/ec76b2dc30b65a82f437795271242ab72b581d42" target="blank"> By default we dont use hypermap</a></li> 
<li> 2018-05-31: capooti <a href="http://github.com/geonode/geonode/commit/2b5e6ca689fe5411f6550f2f76fdad4d41a13ca1" target="blank"> Fixes a problem with createlayer app</a></li> 
<li> 2018-05-30: capooti <a href="http://github.com/geonode/geonode/commit/b590fa7c6f1e4c6a5b3273432faa8d1eeaf74b90" target="blank"> Fixes PEP8 violations and a syntax error</a></li> 
<li> 2018-05-29: capooti <a href="http://github.com/geonode/geonode/commit/8a6ba6ad976e24fd96dd275cb0759c1e007f0a4c" target="blank"> By default USE_WORLDMAP is False</a></li> 
<li> 2018-05-29: capooti <a href="http://github.com/geonode/geonode/commit/afd04ed20244d5814db530f4e85d9643eda46e60" target="blank"> Sync with latest GeoNode 2.7.x</a></li> 
<li> 2018-05-29: capooti <a href="http://github.com/geonode/geonode/commit/b4f590faab443bd4851abbfa331bbe9e160b45c6" target="blank"> Fixes pep8 violations</a></li> 
<li> 2018-05-29: afabiani <a href="http://github.com/geonode/geonode/commit/ed6f97690a2ce41177d369c73d7c9aca16090350" target="blank">  - Add iso8961 time rules (yyyy/yyyy-mm/yyyy-mm-dd) on Templates also</a></li> 
<li> 2018-05-28: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/e54eb9233209196a715a96426b9ed9e76cdd08e4" target="blank">  - Backport from master</a></li> 
<li> 2018-05-28: Giovanni Allegri <a href="http://github.com/geonode/geonode/commit/5541329b0d7b4ea61a08d2da9903b3737637ab2c" target="blank"> DATETIME_INPUT_FORMATS switched to list since Django 1.9</a></li> 
<li> 2018-05-28: afabiani <a href="http://github.com/geonode/geonode/commit/06ef254560b990c2fed91f3408d2de4b7d3b5561" target="blank"> [geoext client] - Zoom To Data and not to nearest Scale</a></li> 
<li> 2018-05-24: capooti <a href="http://github.com/geonode/geonode/commit/7ccf3f02e241aebfc0d6628b7d6af525d95384da" target="blank"> Reset a couple of files</a></li> 
<li> 2018-05-24: capooti <a href="http://github.com/geonode/geonode/commit/651511a9b62967e3ac98ae689e81a2b89a859224" target="blank"> Removed the worldmap.queue application for now</a></li> 
<li> 2018-05-24: capooti <a href="http://github.com/geonode/geonode/commit/fe10f4305847bebba76248b678b0d640029a702d" target="blank"> Updated worldmap installation documentation</a></li> 
<li> 2018-05-24: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/25d620f569316089bcec9e481739297145f1b6fd" target="blank">  - Backport fixes from master branch</a></li> 
<li> 2018-05-24: afabiani <a href="http://github.com/geonode/geonode/commit/be6f92bd8a49b667bb22c0b4bf892966dc98f9f6" target="blank">  - pep8 issues</a></li> 
<li> 2018-05-24: afabiani <a href="http://github.com/geonode/geonode/commit/b21a0b88711c58626f0b63812eba9791e7d30c96" target="blank">  - Update pip install instructions on docs and README</a></li> 
<li> 2018-05-24: afabiani <a href="http://github.com/geonode/geonode/commit/914ccb20082dabdb1c2f2753e4e9e78c1710fbbb" target="blank">  - Include django-celery-mon dep on requirements.txt</a></li> 
<li> 2018-05-24: afabiani <a href="http://github.com/geonode/geonode/commit/5b854c5ff33e9af02a84991ec7ac3f83a65b3d3b" target="blank">  - ASYNC MODE uses ASYNC CELERY TASKS</a></li> 
<li> 2018-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/e4774bf263f135a2058ef155c9224401d253ab1a" target="blank">  - ImageMosaics refactoring: first step - support ZIP archives with granules and .properties files</a></li> 
<li> 2018-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/4a346bd576974fc7b8dee11b149654304d7e0598" target="blank">  - Update dependencies versions</a></li> 
<li> 2018-05-23: afabiani <a href="http://github.com/geonode/geonode/commit/2a16bf00db2c525bf2339624798cf2605d44f812" target="blank">  - Fix Map Detail page structure issue and errors with GetCapabilities</a></li> 
<li> 2018-05-22: capooti <a href="http://github.com/geonode/geonode/commit/7a98b25c2bcac9f7704db3ca865f9d9438faf746" target="blank"> Now using django-geoexplorer-worldmap from the pypi package</a></li> 
<li> 2018-05-21: capooti <a href="http://github.com/geonode/geonode/commit/754e4da56900b1fd5b750d4397f4a53110e2c7bd" target="blank"> Including a local_settings sample file for worldmap</a></li> 
<li> 2018-05-21: capooti <a href="http://github.com/geonode/geonode/commit/e77ea3f850389ed30b58add970eb34ebce4d8ac0" target="blank"> Updated requirements for WorldMap</a></li> 
<li> 2018-05-21: capooti <a href="http://github.com/geonode/geonode/commit/c229e1c03cea973982bc815c1c410182237e3c7b" target="blank"> Fixing a number of things before sending PR to GeoNode 2.7.x</a></li> 
<li> 2018-05-21: capooti <a href="http://github.com/geonode/geonode/commit/5c25cd9eb2454fbe611e61fa1a8ad30c26c4c7df" target="blank"> Removing all static files, which should be added by pip install worldmap-geoexplorer</a></li> 
<li> 2018-05-21: capooti <a href="http://github.com/geonode/geonode/commit/8f33c82957b4cb6800dfe84dcba83fe3e904de7f" target="blank"> Removing worldmap account, which will be part of the cga geonode project</a></li> 
<li> 2018-05-21: capooti <a href="http://github.com/geonode/geonode/commit/8d406ac41aa13c569636adae1ed471e0a6966adc" target="blank"> Removing from git the compiled geoexplorer worldmap client</a></li> 
<li> 2018-05-21: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/4bd34841d99797005dc6f95934f72580cc859ec3" target="blank">  - Backport commit 6c0e8ca from master</a></li> 
<li> 2018-05-21: afabiani <a href="http://github.com/geonode/geonode/commit/6c0e8ca5eb9fdc8be9b2c958f4322e58d605b610" target="blank">  - Restored the possibility of sending multiple uploads</a></li> 
<li> 2018-05-21: capooti <a href="http://github.com/geonode/geonode/commit/6c9cc752d8134944fde03491a1c60609ee518b0d" target="blank"> A couple of fixes and removing geoexplorer source code</a></li> 
<li> 2018-05-21: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/5bd4f3dcfe4cb0cabe198c65a071b6c1749351de" target="blank">  - Backport commit 15123a5 from master</a></li> 
<li> 2018-05-21: afabiani <a href="http://github.com/geonode/geonode/commit/15123a54027c50f5ba2623ac6e942f95f9144273" target="blank">  - Translations and minor refactoring of upload validator</a></li> 
<li> 2018-05-18: capooti <a href="http://github.com/geonode/geonode/commit/2af5e39abf0bc45f5bdf21e5fd216e2b637d76b5" target="blank"> Removed stale worldmap documentation page</a></li> 
<li> 2018-05-18: capooti <a href="http://github.com/geonode/geonode/commit/42513be7b75074d5c65dca3becb7180ed9e6bc3b" target="blank"> Move the worldmap documentation to the correct place</a></li> 
<li> 2018-05-18: capooti <a href="http://github.com/geonode/geonode/commit/52933c9fd0d9481cc41c7b52a327785bc51a2c8a" target="blank"> Synced with GeoNode 2.7.x</a></li> 
<li> 2018-05-16: capooti <a href="http://github.com/geonode/geonode/commit/78530ef070332c69c83441a4a2710d7a34acd133" target="blank"> Updating the client</a></li> 
<li> 2018-05-16: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/ae8dc3238b40f08fe0513ffd47af7e8029506f51" target="blank">  - Allow registered users to edit Remote Services</a></li> 
<li> 2018-05-16: afabiani <a href="http://github.com/geonode/geonode/commit/fc9f14c9197475ba9e5a3cb76a5c5ccaec9acdac" target="blank">  - Reduced size of layer-upload tooltips square</a></li> 
<li> 2018-05-16: afabiani <a href="http://github.com/geonode/geonode/commit/bdf662488925283d4f22ece4400780db235d463e" target="blank">  - Allow registered users to manage Remote Services</a></li> 
<li> 2018-05-16: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/9aa2f2f62eeea80273430c6a63a48e95ece20382" target="blank">  - Backport fixes from master</a></li> 
<li> 2018-05-16: afabiani <a href="http://github.com/geonode/geonode/commit/ddeebf561355413a05bc3b2dac32da61d600ea03" target="blank">  - Correct management of SLDs / Add GWC filterParameter to SLDs</a></li> 
<li> 2018-05-16: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/c6b85ae9148de78f64a2f3953a67846deeee1021" target="blank">  - Backport fixes from master</a></li> 
<li> 2018-05-15: afabiani <a href="http://github.com/geonode/geonode/commit/7b32bb1dc4473c9563034cdb6e066263125bd08b" target="blank">  - Correct management of SLDs / Add GWC filterParameter to SLDs</a></li> 
<li> 2018-05-15: afabiani <a href="http://github.com/geonode/geonode/commit/4c10a85612468a2d0aaae9a08780fe0f6ba6aa57" target="blank">  - Increase Test Coverage</a></li> 
<li> 2018-05-15: afabiani <a href="http://github.com/geonode/geonode/commit/f44471237c8100d675bf3cc5b0735d63155b857c" target="blank">  - Allow unapproved layers to be published on maps</a></li> 
<li> 2018-05-15: afabiani <a href="http://github.com/geonode/geonode/commit/07ebfeee3001e50b0b3c75da7e2c1b3444ee2b07" target="blank">  - Fix for issue Map Composer Menu not show complete #3804</a></li> 
<li> 2018-05-14: afabiani <a href="http://github.com/geonode/geonode/commit/dbde9664d57b9a793b67149b5843a672f735f558" target="blank">  - Test GeoServer Integration Tests running with Docker Compose</a></li> 
<li> 2018-05-14: afabiani <a href="http://github.com/geonode/geonode/commit/cf3247af878391edb9a66d3386cd38353e5597e3" target="blank">  - Test GeoServer Integration Tests running with Docker Compose</a></li> 
<li> 2018-05-14: afabiani <a href="http://github.com/geonode/geonode/commit/325b27246b8bff4bdc247c09de75e026951ceffd" target="blank">  - Fix ResponseNotReady issue</a></li> 
<li> 2018-05-14: afabiani <a href="http://github.com/geonode/geonode/commit/d32f11f18c19d86b5bd258f5068e36b8b77748bc" target="blank">  - Test GeoServer Integration Tests running with Docker Compose</a></li> 
<li> 2018-05-14: afabiani <a href="http://github.com/geonode/geonode/commit/bbaef20b2bf556c12b07d8a447335b5ea714670c" target="blank">  - Test GeoServer Integration Tests running with Docker Compose</a></li> 
<li> 2018-05-14: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/2c3a00c9805ef746d982df20269ad84c0602d224" target="blank"> Update integration.py</a></li> 
<li> 2018-05-14: afabiani <a href="http://github.com/geonode/geonode/commit/a63c39a4f0359a394f99763ff76adbcfd8e01313" target="blank"> Backporting Master PRs</a></li> 
<li> 2018-05-14: afabiani <a href="http://github.com/geonode/geonode/commit/6c3b2b9970f89905277da6a1fbe182177360889e" target="blank">  - Fix celery tasks hanging forever</a></li> 
<li> 2018-05-14: afabiani <a href="http://github.com/geonode/geonode/commit/959219b06845f98e02b42d38740eeabe3fb4eed3" target="blank">  - Minor improvements</a></li> 
<li> 2018-05-11: capooti <a href="http://github.com/geonode/geonode/commit/3eb806e7d8acffe8a8c52555895929d6466731a3" target="blank"> Fixes #375</a></li> 
<li> 2018-05-11: capooti <a href="http://github.com/geonode/geonode/commit/7de6421e80cb219e4b5d1df8a27074d2e4f77968" target="blank"> Fixes #3801</a></li> 
<li> 2018-05-11: erwin <a href="http://github.com/geonode/geonode/commit/d6f784faf7627ed7b7dd4a66aa3290273c5b57b8" target="blank"> Generalize logo-urls in profile-detail template.</a></li> 
<li> 2018-05-11: afabiani <a href="http://github.com/geonode/geonode/commit/87e652980aee4d3bcb6dab6307a1c0cd7296955d" target="blank"> Backporting Master PRs</a></li> 
<li> 2018-05-11: afabiani <a href="http://github.com/geonode/geonode/commit/5ec88bc1c4808bf2e52cf448a732afd166bf80fe" target="blank">  - Docker Compose improvs</a></li> 
<li> 2018-05-10: capooti <a href="http://github.com/geonode/geonode/commit/c5540fb7a407897a42d10409a74bddc42336d369" target="blank"> Now thumbanils are not generate from layers which are created. Fixes #358</a></li> 
<li> 2018-05-10: capooti <a href="http://github.com/geonode/geonode/commit/272017b33d77d4d050674fe3151c746bd063d012" target="blank"> Fixes part of #358 (the layer extent)</a></li> 
<li> 2018-05-10: capooti <a href="http://github.com/geonode/geonode/commit/b29abc581e1486df55a9f007e7955ba1f20197b4" target="blank"> Some improvement to the createlayer application</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/09a9bb868f364d0d6b3300ad6d8a270fd8f66ca7" target="blank"> Fixes https://github.com/camp-zju/geonode/issues/37</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/ed16ac39439877d218ed9fb74f43a0daf1b57baf" target="blank"> Modify the file for translation</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/b9376f0d3202e61d8cc5d602150828ab5c6c8900" target="blank"> Fixes https://github.com/camp-zju/geonode/issues/36</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/cbb1ace8b684bffcd06986495b82723fadd51814" target="blank"> Add Chinese translation file</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/698081e1cc4d2e3ed81cff9fc24704d5679a7941" target="blank"> Add Chinese translation file</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/c96bc5d73654ec15ea0923923564915ed5a881b9" target="blank"> Fixes https://github.com/camp-zju/geonode/issues/34</a></li> 
<li> 2018-05-10: afabiani <a href="http://github.com/geonode/geonode/commit/38177424d0c4025e81253c6c3c47f9de53da7fa7" target="blank">  - minor tweak on settings for Docker</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/ed468785b892cbba04b2721cf67ee7763832c4ee" target="blank"> Fixes https://github.com/camp-zju/geonode/issues/33</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/6ebc540081d3dd7e3a78f3e654f35290eb15c20e" target="blank"> Fixes https://github.com/camp-zju/geonode/issues/32</a></li> 
<li> 2018-05-10: camp-zju <a href="http://github.com/geonode/geonode/commit/d930947bec861225a4abf3ef52d00fd5035427d2" target="blank"> Fixes 31</a></li> 
<li> 2018-05-09: afabiani <a href="http://github.com/geonode/geonode/commit/ac173fcc0702ef55b4c9ed01b5ec47ee1630a666" target="blank">  - Dockerfile: update pip install</a></li> 
<li> 2018-05-09: capooti <a href="http://github.com/geonode/geonode/commit/7a2d4b771bab27e57ce5131f6a82fa6d14fe7019" target="blank"> Fixes #367</a></li> 
<li> 2018-05-09: afabiani <a href="http://github.com/geonode/geonode/commit/0b0c2b79490f6e3c9e3a2c7e4532aebcd7a74d6c" target="blank">  - Travis pip cache</a></li> 
<li> 2018-05-09: afabiani <a href="http://github.com/geonode/geonode/commit/2e548df4c6f7bcdc5f52bcc5cf541a12cab9142f" target="blank">  - Test coverage</a></li> 
<li> 2018-05-09: afabiani <a href="http://github.com/geonode/geonode/commit/a8e67f6ab994bcde3efb409c1a632de087b7310c" target="blank">  - Integration test coverage</a></li> 
<li> 2018-05-09: afabiani <a href="http://github.com/geonode/geonode/commit/7e9c14d8ee0ef5da6fef652e126d7e8aefdf2e61" target="blank">  - Integration test coverage</a></li> 
<li> 2018-05-09: afabiani <a href="http://github.com/geonode/geonode/commit/eb5de195a01d9d4d3705d95f3469e87fd7eb1152" target="blank">  - pep8 issues</a></li> 
<li> 2018-05-09: afabiani <a href="http://github.com/geonode/geonode/commit/8d8cb5453639ca6d991f28e800cbf6e16b3f4d80" target="blank">  - Minor fixes to backup & restore commands</a></li> 
<li> 2018-05-08: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/8e87da4d0e95a8184bd580501ea45734dc9e4aeb" target="blank"> test-specific requirements: twisted</a></li> 
<li> 2018-05-08: afabiani <a href="http://github.com/geonode/geonode/commit/05e2a1b4e883109eb292a826011d5783cce98416" target="blank">  - Legend links for remote services</a></li> 
<li> 2018-05-08: afabiani <a href="http://github.com/geonode/geonode/commit/669b816ec6e17ec08ea0e0898ae99d7ae8f4e093" target="blank">  - Legend links for remote services</a></li> 
<li> 2018-05-08: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/f0366b2e47a9f3a0b8f577ed25398e9fa4fddb38" target="blank"> monitoring: resolve 2-letter codes to 3-letter codes</a></li> 
<li> 2018-05-08: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/0dcca888bfaeab68fd27e840523891dc8e268e98" target="blank"> monitoring support for geoip2</a></li> 
<li> 2018-05-08: afabiani <a href="http://github.com/geonode/geonode/commit/360f7ddfd04ef2bd768d170a7589610f15680404" target="blank">  - Fix updatelayers mgmt command</a></li> 
<li> 2018-05-08: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/4e1563ac6cf03216d7f510ca0e4820c659d72bb0" target="blank"> monitoring support for geoip2</a></li> 
<li> 2018-05-08: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/799f049aa23c078ef48e97134acb8f4acb25099e" target="blank"> monitoring support for geoip2</a></li> 
<li> 2018-05-08: afabiani <a href="http://github.com/geonode/geonode/commit/501edfac60cb8ba8d07cd8cc8feebf86f779fc64" target="blank">  - Monitoring GeoIP error management</a></li> 
<li> 2018-05-08: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/d4ebe63ef856df24350983851772a4498f9c8c9f" target="blank"> Monitoring geoip2 (#286)</a></li> 
<li> 2018-05-08: afabiani <a href="http://github.com/geonode/geonode/commit/f6658e1c6260059bf2b83a08ffa8ed995b16c964" target="blank">  - Disabling synchronous remote services probe from model</a></li> 
<li> 2018-05-08: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/98b752904521b79eee0e651963d189b46468eabf" target="blank"> handle new geoip format properly</a></li> 
<li> 2018-05-08: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/38db65e3adbafbe040739306e686d861c2ed8a6c" target="blank"> use maxmind v2 db format if needed</a></li> 
<li> 2018-05-07: afabiani <a href="http://github.com/geonode/geonode/commit/25d4f3f1ff9f3f0f4322152ffc4687f5d8037316" target="blank">  - Improve Test Coverage</a></li> 
<li> 2018-05-07: afabiani <a href="http://github.com/geonode/geonode/commit/a1601e26a389890df3e0d7b60de78c0117e2d5bf" target="blank"> Backporting Master PRs</a></li> 
<li> 2018-05-07: afabiani <a href="http://github.com/geonode/geonode/commit/151c080674c3ff34bcba5aa38db7fadb56d3cb8f" target="blank"> Backporting Master PRs</a></li> 
<li> 2018-05-07: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/44ec6886997763d1adec1d4a6f7817dbf3d304b7" target="blank"> Update helpers.py</a></li> 
<li> 2018-05-07: afabiani <a href="http://github.com/geonode/geonode/commit/27efde124ddd529fd1085c940a33cb9253fecec6" target="blank">  - Test coverage improvements</a></li> 
<li> 2018-05-07: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/15db8a01f46e7bf1d0d8a6060928dd42efc05f6b" target="blank"> Update helpers.py</a></li> 
<li> 2018-05-04: giohappy <a href="http://github.com/geonode/geonode/commit/d762796e0126920d106b75e711da7da28200eec4" target="blank"> included default settings for social providers</a></li> 
<li> 2018-05-03: capooti <a href="http://github.com/geonode/geonode/commit/4a039537aaab03a3e4df0f26a987279ea8e29b19" target="blank"> Fixes the updatelayers command</a></li> 
<li> 2018-05-02: capooti <a href="http://github.com/geonode/geonode/commit/79409faefe92c1d5b2e47313cd7d6786bdd13443" target="blank"> renaming celery to celery_app</a></li> 
<li> 2018-05-02: capooti <a href="http://github.com/geonode/geonode/commit/419397081b5ee15c91287bf0e9543d941c73a2b4" target="blank"> Fixing a couple of things broke when merging</a></li> 
<li> 2018-05-02: capooti <a href="http://github.com/geonode/geonode/commit/e0a1808dfc9f5a8a68bcdfee10526b87d3f6a297" target="blank"> Fixes a couple of things which were broken by merge with 2.8.0</a></li> 
<li> 2018-05-01: capooti <a href="http://github.com/geonode/geonode/commit/e209771d7a0ee44aca8fcbee20e9f02cc3b3b69b" target="blank"> Synced with GeoNode 2.8.0</a></li> 
<li> 2018-04-30: capooti <a href="http://github.com/geonode/geonode/commit/de6dd0bc4ecb2d896c33f787b068e8bfe0c7f6b6" target="blank"> Updating geoexplorer to last version</a></li> 
<li> 2018-04-30: capooti <a href="http://github.com/geonode/geonode/commit/7b17e8cd047f80656fa22ec8a8e7d442ea2c2d64" target="blank"> Sync with GeoNode 2.8 part 1/2</a></li> 
<li> 2018-04-28: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/8350688254eba19f74101f1d84bdf8c79676aa12" target="blank"> Update helpers.py</a></li> 
<li> 2018-04-27: capooti <a href="http://github.com/geonode/geonode/commit/f42ed7dff42cdbd638d281c5491c9a8e6d5b5411" target="blank"> Now categories order is respected for existing maps. Refs #341</a></li> 
<li> 2018-04-26: capooti <a href="http://github.com/geonode/geonode/commit/5a8c785a678b1d47fa3286b6cf411faec1cea681" target="blank"> Re-enable thumbnails for layers. Fixes #351</a></li> 
<li> 2018-04-26: capooti <a href="http://github.com/geonode/geonode/commit/f4ddf56cd1ac19daec4c745ae90ec8ec1530fa43" target="blank"> Fixes #350</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/de5cbdcac539baa8ff83eb39ff1bbee10818d98c" target="blank"> Backporting Master PRs</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/6af5f51554ad61b9919e9c12380a45c8005f3839" target="blank">  - fixes and improvements to Layer replase functionalities</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/2d8bf65cadf4baf00fbf02881c61fda526d1404b" target="blank"> Forward port 2.8.0 changelogs</a></li> 
<li> 2018-04-26: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/fe14d724a840758d5569ce805f7009be2cb9afac" target="blank"> check geometry type</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/401ad5b13ce966d027e1063196ae27610ad69fab" target="blank">  - Fix layer replase</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/c47b75a94045e01f77d511cc207b8bd1bd1f97e9" target="blank">  - Fix remote services layout</a></li> 
<li> 2018-04-26: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/3b94ba24b41be9129d72dde3d1d5dc641243fad1" target="blank"> catch geoserver error in messaging, to avoid looped delivery</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/c085b83c0bbe4927b46d98942cd90f8bd1e8fd6e" target="blank"> Update utils.py</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/ae62bfd86eb67d347ed3e1766f58149ba7c5ad22" target="blank">  - Fix test cases</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/5753b664c187911789c2d376604c6c79e0c61943" target="blank">  - Fix test cases</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/db24fe3e13014465c39a7e7a4c29bc8b77a2babd" target="blank">  - Fix test cases</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/c01462323134f32c487e1dd3f06fe297e9da9c4d" target="blank">  - Fix test cases</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/6c1d60eab543cff002d5cf9146a59f83f34bcc3b" target="blank"> Updated changelog for version 2.8</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/95e91b7b3e65d2299c0af10097e072c515202f74" target="blank"> Constrain pip to 9.0.3</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/948664881990f8f851e9a52a82a52d441ffbe119" target="blank"> Updated changelog for version 2.8</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/f6dd1582ee893fc5b5d942a5b90bab36ff7e3b67" target="blank"> Constrain pip to 9.0.3</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/419d2e1fa6e5319917ea8c45d383d66a47d18b91" target="blank">  - Restore production/docker requirements</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/65bcf74617328702811efee7b54c3d666f8aa1d1" target="blank">  - DB consistency checks</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/07271fa5b3cbf96c2967979c868387cf0ec590ed" target="blank"> Update utils.py</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/b996b4b63b18987dfd97117d258c3db34c84c1de" target="blank"> Update utils.py</a></li> 
<li> 2018-04-26: afabiani <a href="http://github.com/geonode/geonode/commit/32ddf3c33417deb6fc41e41ce40a2184e85ead6b" target="blank">  - Update avatar version</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/7d8d53c58d164fbf467853bec8a82698c7378e93" target="blank"> Update utils.py</a></li> 
<li> 2018-04-26: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/ba3fb4b544b05b8d9414755acad7fc2e94ba99bb" target="blank"> Update utils.py</a></li> 
<li> 2018-04-25: capooti <a href="http://github.com/geonode/geonode/commit/f9e81c62c48594f1a7b8a48a82fa4ccd1bdb0f23" target="blank"> Use HTML widget in GXP for any field starting with "descriptio". Refs #348</a></li> 
<li> 2018-04-24: afabiani <a href="http://github.com/geonode/geonode/commit/e25f154d38a1e8e7a8330fa0b59ddcfc7028fbd8" target="blank"> Just fix requirements versions for GeoNode modules in order to avoid compatibility issues</a></li> 
<li> 2018-04-24: afabiani <a href="http://github.com/geonode/geonode/commit/2e77def0429ced6f307761b0d24d8fe576d24383" target="blank"> Minor improvement to custom_theme_html template</a></li> 
<li> 2018-04-24: afabiani <a href="http://github.com/geonode/geonode/commit/4e14df5a884112c730dfea46c4f1808856d8e73e" target="blank"> [Closes #3662] GNIP: Improvements to GeoNode Layers download links</a></li> 
<li> 2018-04-24: afabiani <a href="http://github.com/geonode/geonode/commit/9af820274b78ecaa1836e020ba372444718490d1" target="blank"> Just fix requirements versions for GeoNode modules in order to avoid compatibility issues</a></li> 
<li> 2018-04-24: afabiani <a href="http://github.com/geonode/geonode/commit/1dd9e02649e14dfe18902177c2cfc996640f6469" target="blank"> Minor improvement to custom_theme_html template</a></li> 
<li> 2018-04-24: afabiani <a href="http://github.com/geonode/geonode/commit/8d6f5379f3c5b7144515a52472aa21cb716194be" target="blank"> [Closes #3662] GNIP: Improvements to GeoNode Layers download links</a></li> 
<li> 2018-04-24: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/a2c55c265d8a519164c27715fa6d7b92ce51dfe0" target="blank"> use geoip2 for monitoring</a></li> 
<li> 2018-04-24: Cezary Statkiewicz <a href="http://github.com/geonode/geonode/commit/602e1a06b9361852f0a8c94b7875281d468203a8" target="blank"> use geoip2 for monitoring</a></li> 
<li> 2018-04-24: olivierdalang <a href="http://github.com/geonode/geonode/commit/1e02bcc12f2d9c97f5666a91c9ab9f3175ba5094" target="blank"> fix slow login/logout on certain circumstances</a></li> 
<li> 2018-04-24: olivierdalang <a href="http://github.com/geonode/geonode/commit/def7df173423f031335285a40a2943a2bb46387d" target="blank"> fix slow login/logout on certain circumstances</a></li> 
<li> 2018-04-23: afabiani <a href="http://github.com/geonode/geonode/commit/2aa0932181eb9d3e0a45e265b656acd7d794bcd2" target="blank">  - Fix reproj issue on bbox_to_projection</a></li> 
<li> 2018-04-23: afabiani <a href="http://github.com/geonode/geonode/commit/dee03ba92306b82d6105a2a5fe7f983dd367514f" target="blank">  - Fix reproj issue on bbox_to_projection</a></li> 
<li> 2018-04-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/c4c977176f84dd583803ff5c83bb74ead19ca721" target="blank"> Backport master fixes</a></li> 
<li> 2018-04-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/7c7ccdb188d9646b0212f6b2bfaac0d41f79f545" target="blank">  - Fix issue with layer upload</a></li> 
<li> 2018-04-20: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/0d683c94f5e270c4b7b3dc91f801abaf38d230cd" target="blank">  - Fix issue with layer upload</a></li> 
<li> 2018-04-20: afabiani <a href="http://github.com/geonode/geonode/commit/e7a45e61925e8cb819e317e2fea3a6dd1b1e0540" target="blank">  - Restoring Live Server port settings on integration tests in order to avoid address conflicts</a></li> 
<li> 2018-04-19: afabiani <a href="http://github.com/geonode/geonode/commit/8b93fa24b9aff84f1a914c84f1a50aeb57f04b78" target="blank">  - Split test cases on travis</a></li> 
<li> 2018-04-19: afabiani <a href="http://github.com/geonode/geonode/commit/cf61164bddf0a2e1fe0bedfe37118dfcbb31b153" target="blank">  - Split test cases on travis</a></li> 
<li> 2018-04-19: afabiani <a href="http://github.com/geonode/geonode/commit/cab688e77a4259e2c6d7aef8ca4b1da37db0cb80" target="blank">  - Align with master</a></li> 
<li> 2018-04-18: afabiani <a href="http://github.com/geonode/geonode/commit/e92165d2c885a01c8646776ca7652f63d88ca494" target="blank">  - cleanup</a></li> 
<li> 2018-04-18: afabiani <a href="http://github.com/geonode/geonode/commit/c7edb2234a0152150726782f8329e2acf1f19068" target="blank">  - align with master branch</a></li> 
<li> 2018-04-17: afabiani <a href="http://github.com/geonode/geonode/commit/c20fd2166c945af62d5aadba3f9a19547f99bab5" target="blank">  - Fix integration test cases</a></li> 
<li> 2018-04-16: afabiani <a href="http://github.com/geonode/geonode/commit/c0b298f69883d94875a4cc20dc34a447a9f879b5" target="blank"> [Closes #3661] django 1.11 LTS support on master</a></li> 
<li> 2018-04-17: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/ef8fcd21bb9666ee6f617ac42ff7cc96e5f9f069" target="blank"> Better alignment of jumbotron image</a></li> 
<li> 2018-04-16: afabiani <a href="http://github.com/geonode/geonode/commit/5972d18a8f967fc9a5f57e5c5f769d74c16cf087" target="blank"> [Closes #3661] django 1.11 LTS support on master</a></li> 
<li> 2018-04-14: afabiani <a href="http://github.com/geonode/geonode/commit/37969014cf8cbfac7854f4a1800fd38efe2df5b5" target="blank"> Prepare 2.8.1</a></li> 
<li> 2018-04-13: capooti <a href="http://github.com/geonode/geonode/commit/e2278356009db8b19320944099e9e7f6b232194f" target="blank"> Fixes #343</a></li> 
<li> 2018-04-13: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/73c6d372fd1028ddc24286bde34226fd193e9409" target="blank"> Align to master branch</a></li> 
<li> 2018-04-12: capooti <a href="http://github.com/geonode/geonode/commit/98fa182b937093dfa652bc7f508bc17ee23a1b1a" target="blank"> Fixes #340</a></li> 
<li> 2018-04-12: capooti <a href="http://github.com/geonode/geonode/commit/1800ba90bafe5de57617873c438870f9ac2d69f1" target="blank"> Fixes #336</a></li> 
<li> 2018-04-12: capooti <a href="http://github.com/geonode/geonode/commit/c7616a49998264975293eca9cbae775a00f48f46" target="blank"> Fixes #327</a></li> 
<li> 2018-04-11: capooti <a href="http://github.com/geonode/geonode/commit/20881824437106cd917fbbfc07ef7708643045fd" target="blank"> Fixes #330</a></li> 
<li> 2018-04-11: Ahmed Nour Eldeen <a href="http://github.com/geonode/geonode/commit/aad557f92d24755b0746819bac4d2bb4a71407b9" target="blank"> get geometry type for layers</a></li> 
<li> 2018-04-09: capooti <a href="http://github.com/geonode/geonode/commit/19c3f383a94666892cdcea2cc68cdd12554fd356" target="blank"> Fixes #300</a></li> 
<li> 2018-04-09: capooti <a href="http://github.com/geonode/geonode/commit/1dde174f0fc647bd154955f86fcaef9d79020683" target="blank"> Fixes #334</a></li> 
<li> 2018-04-05: capooti <a href="http://github.com/geonode/geonode/commit/2617553cf087ad0ba7270e781ed2d3c2231b7a7b" target="blank"> Adds a status message when updating the gazetteer fields for a layer</a></li> 
<li> 2018-04-05: capooti <a href="http://github.com/geonode/geonode/commit/62919066b22cb7143c24bfcb999e68fe5f225b64" target="blank"> Removed a stale file</a></li> 
<li> 2018-04-04: capooti <a href="http://github.com/geonode/geonode/commit/730c0a337a1b204bee251cfddddabfffe872e9b5" target="blank"> Make layer configuration in json map more robust</a></li> 
<li> 2018-04-04: capooti <a href="http://github.com/geonode/geonode/commit/34cc05d46fd5636b4f789f5cf3eba4e3f446d0c6" target="blank"> Improve map thumbnails</a></li> 
<li> 2018-04-03: capooti <a href="http://github.com/geonode/geonode/commit/dda99c1372c009b927370fe744001eba9c43bd6e" target="blank"> Forgot file in previous commit</a></li> 
<li> 2018-04-03: capooti <a href="http://github.com/geonode/geonode/commit/bb25ec005afcd94b106cbb512e6631b33bd36e59" target="blank"> Add the feature search functionality</a></li> 
<li> 2018-04-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/14482e256bf7e4a98b84b1cdea626f56567d5719" target="blank"> Update README</a></li> 
<li> 2018-04-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/5141963be5ff5477db4a3633508d3665ba170821" target="blank"> Update README</a></li> 
<li> 2018-04-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/53405ce8c15b3784c9b8e3a9f5182b31266720f5" target="blank"> Updated changelog for version 2.8</a></li> 
<li> 2018-04-03: Alessio Fabiani <a href="http://github.com/geonode/geonode/commit/48eea12b9200033181d6abf85f85b27bc5411a59" target="blank"> Release 2.8.0</a></li> 
<li> 2018-03-30: capooti <a href="http://github.com/geonode/geonode/commit/d518ce2b9d9fa85638b975bb8f1462a0c66c58aa" target="blank"> Fixes #301</a></li> 
<li> 2018-03-29: capooti <a href="http://github.com/geonode/geonode/commit/1be90deb4ee2f56c85f8104444ce307f33b172c0" target="blank"> Fixes the regression casuing all the extent issues</a></li> 
<li> 2018-03-28: capooti <a href="http://github.com/geonode/geonode/commit/714e5d2ec7b2ede9c34deb5ed3763d2e2a934df2" target="blank"> Fixes zoom to extent tool</a></li> 
<li> 2018-03-28: capooti <a href="http://github.com/geonode/geonode/commit/5585f5edec66ed5a4adfdc55c3f977e49198181a" target="blank"> Fixes #322</a></li> 
<li> 2018-03-26: capooti <a href="http://github.com/geonode/geonode/commit/09b19f60f2e4b26f242db597e2984b3ddad4e6d2" target="blank"> Correctly identify a local layer when using GeoNodeQueryTool</a></li> 
<li> 2018-03-26: capooti <a href="http://github.com/geonode/geonode/commit/53737f7097de1dda6c6d3b103aeaeb1ddf09665e" target="blank"> Point to the correct warper site in the rectify images dialog</a></li> 
<li> 2018-03-26: capooti <a href="http://github.com/geonode/geonode/commit/0139def9f65a6233b2963f2c90cf517e68f16cbb" target="blank"> Fixes #298</a></li> 
<li> 2018-03-26: capooti <a href="http://github.com/geonode/geonode/commit/994da8f38b15dc1a88950f033d196ea0cfdb48be" target="blank"> Fixes #314</a></li> 
<li> 2018-03-21: capooti <a href="http://github.com/geonode/geonode/commit/8825de9d3a70c47fbc11e8a32d52532dd921646f" target="blank"> Fixes #283</a></li> 
<li> 2018-03-20: capooti <a href="http://github.com/geonode/geonode/commit/d30a9872dc20465192938c50e6b68e80d5aea381" target="blank"> Fixes permission issues with editing and use the correct source for wm layers</a></li> 
<li> 2018-03-16: capooti <a href="http://github.com/geonode/geonode/commit/c9f1a9d60a265f054aa727975f6988c31d82ac30" target="blank"> Fixes #272</a></li> 
<li> 2018-03-16: capooti <a href="http://github.com/geonode/geonode/commit/0a5497ab05633da7b5d40b68d8d01dbb0f0c1b55" target="blank"> Forgot one requirement in previous commit</a></li> 
<li> 2018-03-16: capooti <a href="http://github.com/geonode/geonode/commit/6991c699230112744953152580bf1603f9a0bb5f" target="blank"> Fixes #260 (gazetteer)</a></li> 
<li> 2018-03-08: capooti <a href="http://github.com/geonode/geonode/commit/ae537d3265ec6d343d039eb19af3141f9e5e698e" target="blank"> Fixes #267</a></li> 
<li> 2018-03-06: capooti <a href="http://github.com/geonode/geonode/commit/eabf8f38847121db0add327f60b5ca9b52614ca1" target="blank"> Restore map print tool</a></li> 
<li> 2018-03-06: capooti <a href="http://github.com/geonode/geonode/commit/a027a37ff55f9f7f839af00fd35e4e7e86680098" target="blank"> Migrate worldmap map revisions. Fixes #266</a></li> 
<li> 2018-03-05: capooti <a href="http://github.com/geonode/geonode/commit/16c9d47cd763b4850226ffbc9acc177115d4ce41" target="blank"> Adding a missing import which caused an error when looking at map page as anonymous user</a></li> 
<li> 2018-03-05: capooti <a href="http://github.com/geonode/geonode/commit/968eb2c364fef4d07356afa35186c8b2f97f9cd3" target="blank"> Removed google earth tool. Fixed the gxp_mapshare tool. Fixing google map api key read</a></li> 
<li> 2018-03-05: capooti <a href="http://github.com/geonode/geonode/commit/44cec0c7822f69caac671c09b68364b5c522a6d6" target="blank"> Trying to increase accesstoken expiration to see if this affects #283</a></li> 
<li> 2018-03-02: capooti <a href="http://github.com/geonode/geonode/commit/eb3a887a13fe2f59b4fd8543df858b9cdef483e8" target="blank"> Update instructions adding the configuration of update_last_wm_geonode_layers</a></li> 
<li> 2018-03-02: capooti <a href="http://github.com/geonode/geonode/commit/3ffdc2cce9c84428ee9d1c375406ee596d39cbd1" target="blank"> Fixes #280</a></li> 
<li> 2018-03-02: capooti <a href="http://github.com/geonode/geonode/commit/d97cf35932620e2261c265ecf6570bb49ced8663" target="blank"> Fixes #264</a></li> 
<li> 2018-02-27: capooti <a href="http://github.com/geonode/geonode/commit/84db0f6af154b1d7353ecd12902a3f407a12c5a8" target="blank"> Updating instructions for geonode-worldmap</a></li> 
<li> 2018-02-26: capooti <a href="http://github.com/geonode/geonode/commit/75291f2040adf669e8e18318ecd60891565df487" target="blank"> Ported the action model and its api, which is needed by hypermap</a></li> 
<li> 2018-02-26: capooti <a href="http://github.com/geonode/geonode/commit/f9ffe2bbc2fec92112e60f76ccb6e5d29ef610a3" target="blank"> Fixed javascript build.xml and a few things in GeoExplorer.js</a></li> 
<li> 2018-02-23: capooti <a href="http://github.com/geonode/geonode/commit/20a6f171e35fdc4a6d1beb03da3914f9c3332abe" target="blank"> Added worldmap geoexplorer client source code. Fixes #265</a></li> 
<li> 2018-02-21: capooti <a href="http://github.com/geonode/geonode/commit/ef2ce5a2515fe3b7e010a1e7a4d2145680403161" target="blank"> WorldMap api version is now 2.8</a></li> 
<li> 2018-02-21: capooti <a href="http://github.com/geonode/geonode/commit/dd0642a9d26918f2b6e025ad18557edc7219accf" target="blank"> Add url dispatcher for worldmap api</a></li> 
<li> 2018-02-21: capooti <a href="http://github.com/geonode/geonode/commit/19655c2e5ab459d5db3c46765b01afdf46d21ddd" target="blank"> Fixes a problem with layers upload</a></li> 
<li> 2018-02-16: capooti <a href="http://github.com/geonode/geonode/commit/9456161f91ee5cb0af7ec6f41b304a309767689a" target="blank"> Synced with geonode master</a></li> 
<li> 2018-02-15: capooti <a href="http://github.com/geonode/geonode/commit/a521cfcb7c6727e9e9f3c67243e1a84c11642cdf" target="blank"> Fixes #273</a></li> 
<li> 2018-02-15: capooti <a href="http://github.com/geonode/geonode/commit/7683603d1ecee8773bf507cd8efe7e20bb35c936" target="blank"> Fixes #263</a></li> 
<li> 2018-02-15: capooti <a href="http://github.com/geonode/geonode/commit/0706039e0945b873c464a908b901f58e2248f83b" target="blank"> Now it is possible to edit and style also from local dev</a></li> 
<li> 2018-02-14: capooti <a href="http://github.com/geonode/geonode/commit/dbe2b88993a2b3ad0a48be099c4ce77a9e7df590" target="blank"> Enable DB_DATASTORE when using WorldMap</a></li> 
<li> 2018-02-14: capooti <a href="http://github.com/geonode/geonode/commit/cdb366d54ea5a423b42c1b280349b34e26184559" target="blank"> Remove an ipdb line</a></li> 
<li> 2018-02-12: capooti <a href="http://github.com/geonode/geonode/commit/aa066cc919a8e713772d351f4bac99024e9c342b" target="blank"> Align to GeoNode master. Fixes #276</a></li> 
<li> 2018-02-08: capooti <a href="http://github.com/geonode/geonode/commit/d9363214cd98d23d93b2d6ba1c1085cfbac6bd98" target="blank"> Updated installation instructions</a></li> 
<li> 2018-02-06: Ben Lewis <a href="http://github.com/geonode/geonode/commit/12b3ce00a8c82cea7e5fa7d56e2470f4ca6192db" target="blank"> Update README.md</a></li> 
<li> 2018-02-06: capooti <a href="http://github.com/geonode/geonode/commit/adfa449f4c06fc10f0e439d331be79ea85267037" target="blank"> Hard fixing wms endpoint for now for having style edit working</a></li> 
<li> 2018-02-01: capooti <a href="http://github.com/geonode/geonode/commit/be1999c2c1c57865b3e351a5e8f63a597c8acda7" target="blank"> Now layer is correctly displayed in map</a></li> 
<li> 2018-01-31: capooti <a href="http://github.com/geonode/geonode/commit/0bf993724854fd910baf99e6523b16cf38f3b958" target="blank"> Added instructions for geonode/worldmap contrib app configuration</a></li> 
<li> 2018-01-31: capooti <a href="http://github.com/geonode/geonode/commit/0933fab68977538b8b42f2c67dd1bcb163a7f99b" target="blank"> Removing worldmap settings from general settings file</a></li> 
<li> 2018-01-31: capooti <a href="http://github.com/geonode/geonode/commit/817e47c452a87eb37c94ca38b864e04016c6e0c7" target="blank"> Fixes a problem with upload - not sure if this is a general GeoNode problem, will need to look into it</a></li> 
<li> 2018-01-31: capooti <a href="http://github.com/geonode/geonode/commit/55a29e1aa683bd37c7c95be7f3de5fb1b3f183bf" target="blank"> Redefining some urls when using worldmap contrib application</a></li> 
<li> 2018-01-31: capooti <a href="http://github.com/geonode/geonode/commit/f16196485df1d0d52450ccd9ff900d538ef39c78" target="blank"> Added context processors worldmap variables</a></li> 
<li> 2018-01-30: capooti <a href="http://github.com/geonode/geonode/commit/9d6e211dfb251736cfa07bb554f0fc356223ec01" target="blank"> Fixes migration for apps still using South. Move the content_map field to the appropriate model</a></li> 
<li> 2018-01-30: capooti <a href="http://github.com/geonode/geonode/commit/da6fde22a09d5b18f76fc9c77ed56375fc97e962" target="blank"> Fixing a migration</a></li> 
<li> 2018-01-30: capooti <a href="http://github.com/geonode/geonode/commit/e971dad05eb12231661ff3ef3bf77a42c8cbd747" target="blank"> Fixes a syntax error</a></li> 
<li> 2018-01-18: capooti <a href="http://github.com/geonode/geonode/commit/9983f26fbf371bae601d7141b28d3c0edd0a01d9" target="blank"> Basic version of WorldMap GeoNode unforked version with working maps</a></li> 
<li> 2018-01-11: capooti <a href="http://github.com/geonode/geonode/commit/f934f35873516987ccb15d2b245327a6acd771f0" target="blank"> Start removing forked code in GeoNode/WorldMap</a></li> 
<li> 2018-01-10: Ubuntu <a href="http://github.com/geonode/geonode/commit/6e3d1af666bde90940acab5bd9cf7520e2ccffd6" target="blank"> Fixed conflicts with master</a></li> 
<li> 2017-11-21: capooti <a href="http://github.com/geonode/geonode/commit/4e5f82f0fd9ee5b0c3639b464b2d2d6c71cb7ae8" target="blank"> Sync with geonode master</a></li> 
<li> 2017-11-21: Way Barrios <a href="http://github.com/geonode/geonode/commit/3ef8e837eaf2cef1654c161f78288d476fefbb36" target="blank"> Fixing settings import, we should use django.conf in stead of geonode</a></li> 
<li> 2017-11-14: Way Barrios <a href="http://github.com/geonode/geonode/commit/4a7595a45461c804ab88981133f17187416e8193" target="blank"> removing pdb</a></li> 
<li> 2017-11-14: Way Barrios <a href="http://github.com/geonode/geonode/commit/69fa4f35b7807243a0e1e4eeaf76d031f1cb223f" target="blank"> removing pdb dependency</a></li> 
<li> 2017-11-07: Way Barrios <a href="http://github.com/geonode/geonode/commit/b21a8758437226f356e17c3a597ee1b598c3d20d" target="blank"> Adding missing migrations</a></li> 
<li> 2017-11-03: capooti <a href="http://github.com/geonode/geonode/commit/c194052640e25eb918b618d29b3598b209788147" target="blank"> Sync with GeoNode master</a></li> 
<li> 2017-11-03: capooti <a href="http://github.com/geonode/geonode/commit/6d4b4f70712ec826ef1d3bb3e7ecb2393be202e6" target="blank"> Sync pavement with the one from master</a></li> 
<li> 2017-10-31: capooti <a href="http://github.com/geonode/geonode/commit/6169bc7498c447b17c4d7c22f4c95c729056727b" target="blank"> Added missing migration</a></li> 
<li> 2017-10-27: capooti <a href="http://github.com/geonode/geonode/commit/ace70930519b6313e38e56a435b86c3f0d119565" target="blank"> Updating config to download GeoServer 2.12</a></li> 
<li> 2017-10-24: Way Barrios <a href="http://github.com/geonode/geonode/commit/27f1a73d880c2ffc4d2020652a33a14702b3b181" target="blank"> removing is_certifier from people profile</a></li> 
<li> 2017-10-19: Way Barrios <a href="http://github.com/geonode/geonode/commit/a5769e0878e6a4b739db24872d6c311e91403a81" target="blank"> Dataverse and Datatables migration</a></li> 
<li> 2017-10-17: capooti <a href="http://github.com/geonode/geonode/commit/fa2d460acf20d756e6e58a3ce4f111997a93e5e5" target="blank"> Enable layer-brose again</a></li> 
<li> 2017-10-13: Lenninlasd <a href="http://github.com/geonode/geonode/commit/4af2be4e48210b065340d040d7c97c1582185937" target="blank"> Add missing translations</a></li> 
<li> 2017-10-10: Lenninlasd <a href="http://github.com/geonode/geonode/commit/fe93dbcf125c23e344b01846fffbeadc5708887d" target="blank"> Add extra metadata attributes</a></li> 
<li> 2017-10-04: capooti <a href="http://github.com/geonode/geonode/commit/b870cafc61b5fada2a3f0a6c0c0c1ee8947cbdc2" target="blank"> erge branch 'master' into wm-develop</a></li> 
<li> 2017-09-26: Way Barrios <a href="http://github.com/geonode/geonode/commit/5e2b128bfca7a5448b01ce4a086c990fe2179cb1" target="blank"> removing certification app from GeoNode</a></li> 
<li> 2017-09-20: capooti <a href="http://github.com/geonode/geonode/commit/3e9bc3e196bfee35b8e9d649ec7c1e0b8a3c52d9" target="blank"> Added a missing migrations for map</a></li> 
<li> 2017-09-19: capooti <a href="http://github.com/geonode/geonode/commit/65aa0259aa908e32a9b3533f139ad43c1f7992ba" target="blank"> Adding migrations for the gazetteer fields</a></li> 
<li> 2017-09-19: capooti <a href="http://github.com/geonode/geonode/commit/9942a899144baaae6b86acfbc464c1412da2cf87" target="blank"> Fixes some migrations problem and make sure that "paver sync" correctly build worldmap database</a></li> 
