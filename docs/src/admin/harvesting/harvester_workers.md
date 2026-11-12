# Standard harvester workers

!!! Note
    Remember that, as stated above, a harvester worker is configured by means of setting the `harvester_type` and `harvester_type_specific_configuration` attributes on the harvester.

    Moreover, the format of the `harvester_type_specific_configuration` attribute must be a JSON object.

## GeoNode harvester worker

This worker is able to harvest remote GeoNode deployments. In addition to creating local resources by retrieving the remote metadata, this harvester is also able to copy remote datasets over to the local GeoNode. This means that this harvester can even be used in order to generate replicated GeoNode instances.

This harvester can be used by setting `harvester_type=geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker` in the harvester configuration.

It recognizes the following `harvester_type_specific_configuration` parameters:

`harvest_datasets`
: Whether to harvest remote resources of type `dataset` or not. Acceptable values: `true`, the default, or `false`

`copy_datasets`
: Whether to copy remote resources of type `dataset` over to the local GeoNode. Acceptable values: `true` or `false`, the default

`harvest_documents`
: Whether to harvest remote resources of type `document` or not. Acceptable values: `true`, the default, or `false`

`copy_documents`
: Whether to copy remote resources of type `document` over to the local GeoNode. Acceptable values: `true` or `false`, the default

`resource_title_filter`
: A string that must be present in the remote resources `title` in order for them to be acknowledged as harvestable resources. This allows filtering out resources that are not relevant. Acceptable values: any alphanumeric value

Example: setting this to a value of `"water"` would mean that the harvester generates harvestable resources for remote resources that are titled *water basins*, *Water territories*, etc. The harvester would not generate harvestable resources for remote resources whose title does not contain the word *water*.

`start_date_filter`
: A string specifying a datetime that is used to filter out resources by their `start_date`. This is parsed with [dateutil.parser.parse()](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse), which means that it accepts many different formats, for example `2021-06-31T13:04:05Z`

`end_date_filter`
: Similar to `start_date_filter` but uses resources `end_date` as a filter parameter

`keywords_filter`
: A list of keywords that are used to filter remote resources

`categories_filter`
: A list of categories that are used to filter remote resources

## WMS harvester worker

This worker is able to harvest from remote OGC WMS servers.

This harvester can be used by setting `harvester_type=geonode.harvesting.harvesters.wms.OgcWmsHarvester` in the harvester configuration.

It recognizes the following `harvester_type_specific_configuration` parameters:

`dataset_title_filter`
: A string that is used to filter remote WMS layers by their `title` property. If a remote layer title contains the string defined by this parameter, then the layer is recognized by the harvester worker

## ArcGIS REST Services harvester worker

This worker is able to harvest from remote ArcGIS REST Services catalogs.

This worker is able to recognize two types of `remote_url`:

1. URL of the ArcGIS REST services catalog. This URL usually ends in `rest/services`. A catalog may expose several different services. This harvester worker is able to descend into the available ArcGIS Rest services and retrieve their respective resources. Example:

    ```text
    https://sampleserver6.arcgisonline.com/arcgis/rest/services
    ```

2. URL of the ArcGIS REST services Service. This URL usually takes the form `{base-url}/rest/services/{service-name}/{service-type}`. Example:

    ```text
    https://sampleserver6.arcgisonline.com/arcgis/rest/services/CharlotteLAS/ImageServer
    ```

This harvester worker can be used by setting `harvester_type=geonode.harvesting.harvesters.arcgis.ArcgisHarvesterWorker` in the harvester configuration.

It recognizes the following `harvester_type_specific_configuration` parameters:

`harvest_map_services`
: Whether services of type `MapServer` ought to be harvested. Defaults to `True`

`harvest_image_services`
: Whether services of type `ImageServer` ought to be harvested. Defaults to `True`

`resource_name_filter`
: A string that is used to filter remote WMS layers by their `title` property. If a remote layer name contains the string defined by this parameter, then the layer is recognized by the harvester worker

`service_names_filter`
: A list of names that are used to filter the remote ArcGIS catalog

## Creating new harvesting workers

New harvesting workers can be created by writing classes derived from [geonode.harvesting.harvesters.base.BaseGeonodeHarvesterWorker](https://github.com/GeoNode/geonode/blob/master/geonode/harvesting/harvesters/base.py#L66).
This class defines an abstract interface that must be implemented. All methods decorated with `abc.abstractmethod` must be implemented in the custom harvester worker class. Study the implementation of the standard GeoNode harvester worker classes in order to gain insight on how to implement custom ones.

After writing a custom harvester worker class, it can be added to the list of known harvester workers by defining the `HARVESTER_CLASSES` GeoNode setting. This setting is a list of strings, containing the Python class path to each harvester worker class. It has a default value of:

```python
HARVESTER_CLASSES = [
    "geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker",
    "geonode.harvesting.harvesters.wms.OgcWmsHarvester",
    "geonode.harvesting.harvesters.arcgis.ArcgisHarvesterWorker",
]
```

These are the standard harvester worker classes shipped by GeoNode. If this setting is defined, its value simply extends the default list. This means that it is not possible to disable the standard worker classes, only to add new ones.
