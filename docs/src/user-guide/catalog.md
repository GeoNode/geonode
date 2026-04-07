## Managing Data

Data management tools built into GeoNode allow integrated creation of resources eg datasets, documents, link to external documents, map visualizations and other configured geonode apps. Each resource in the system can be shared publicly or restricted to allow access to only specific users. Social features like user profiles and commenting and rating systems allow for the development of communities around each platform to facilitate the use, management, and quality control of the data the GeoNode instance contains.

GeoNode lets you publish different kinds of resources, but they fall into two big families:

Source resources are created directly from data: you can upload a file (e.g., a vector/raster dataset, a PDF, an image) or connect a remote source (when supported). In GeoNode, these are:

 - **Datasets**: geospatial data that can be styled, visualized, queried, and reused across the platform.
 - **Documents**: supporting files such as reports, manuals, images, and other attachments that provide context and additional information.

Derived resources are built from existing content already in GeoNode. Instead of uploading new data, you combine and present what you’ve already published as Datasets and Documents. These include **Maps**, **Dashboards**, and **GeoStories**, which are curated outputs that reference previously uploaded resources as their inputs.

No matter which type you create, all resources share the same foundation: consistent metadata management (title, abstract, keywords, contacts, licensing, and more) and a common set of configuration options (permissions, visibility/sharing, and other resource settings). This keeps your workflow uniform—upload once, describe it well, and reuse it everywhere.

#### Datasets
Datasets are a primary component of GeoNode.
Datasets are publishable resources representing a raster or vector spatial data source. Datasets also can be associated with metadata, ratings, and comments.
By clicking the Datasets link you will get a list of all published datasets. If logged in as an administrator, you will also see the unpublished datasets in the same list.
GeoNode allows the user to upload vector and raster data in their original projections using a web form.
Vector data can be uploaded in many different formats (ESRI Shapefile, KML and so on…). Satellite imagery and other kinds of raster data can be uploaded as GeoTIFFs.

#### Maps
Maps are a primary component of GeoNode.
Maps are comprised of various datasets and their styles. Datasets can be both local datasets in GeoNode as well as remote datasets either served from other WMS servers or by web service datasets such as Google or MapQuest.
GeoNode maps also contain other information such as map zoom and extent, dataset ordering, and style.

You can create a map based on uploaded datasets, combine them with some existing datasets and a remote web service dataset, share the resulting map for public viewing. Once the data has been uploaded, GeoNode lets the user search for it geographically or via keywords and create maps. All the datasets are automatically reprojected to web mercator for maps display, making it possible to use popular base maps such as OpenStreetMap.

#### Documents
GeoNode allows to publish tabular and text data and to manage metadata and associated documents.
Documents can be uploaded directly from your disk (see Upload/Add Documents for further information).
The following documents types are allowed: txt, .log, .doc, .docx, .ods, .odt, .sld, .qml, .xls, .xlsx, .xml, .bm, .bmp, .dwg, .dxf, .fif, .gif, .jpg, .jpe, .jpeg, .png, .tif, .tiff, .pbm, .odp, .ppt, .pptx, .pdf, .tar, .tgz, .rar, .gz, .7z, .zip, .aif, .aifc, .aiff, .au, .mp3, .mpga, .wav, .afl, .avi, .avs, .fli, .mp2, .mp4, .mpg, .ogg, .webm, .3gp, .flv, .vdo, .glb, .pcd, .gltf.
Through the document detailed page is possible to view, download and manage a document.

#### GeoStories
GeoStory is a MapStore tool integrated in GeoNode that provides the user a way to create inspiring and immersive stories by combining text, interactive maps, and other multimedia content like images and video or other third party contents. Through this tool you can simply tell your stories on the web and then publish and share them with different groups of GeoNode users or make them public to everyone around the world.

#### Dashboard
Dashboard is a MapStore tool integrated in GeoNode that provides the user with a space to add many Widgets, such as charts, maps, tables, texts and counters, and can create connections between them in order to:
- Provide an overview to better visualize a specific data context
- Interact spatially and analytically with the data by creating connections between widgets
- Perform analysis on involved data/layers

### Finding Data
This section will guide you to navigate GeoNode to find datasets, maps and documents and other resource types by using different routes, filters and search functions.
On every page you can find some quick search tool.

The _Search box_ in the navigation bar let you type a text and find all the resource which have to deal with that text.

Clicking the **Filter** button a panel is shown containing a wealth of options for customizing a search.
It is possible to search and filter data by Text, Types, Categories, Keywords, Owners, Regions, Group, Limitations on public access, Date and Spatial Extent.
Try to set some filter and see how the resulting data list changes accordingly. An interesting type of filter is the spatial extent: you can apply a spatial filter by moving or zooming a map within a geographical area.

![FilterPanel](img/search_filter_by_extent.png)