# GeoNode harvesting concepts

When a **harvester** is configured, GeoNode is able to use its corresponding **harvester worker** to contact the remote service and generate a list of **harvestable resources**.
The user is then able to select which of those resources are of interest. Depending on its configured update frequency, sometime later, the **[harvesting scheduler](#harvesting-scheduler)** will create new **harvesting sessions** in order to create local GeoNode resources from the remote harvestable resources that had been marked as relevant by the user.

The above description uses the following key concepts:

## harvester

This is the configuration object that is used to parametrize harvesting of a remote service. It is configurable at runtime and is preserved in the GeoNode database.

Harvesters and their properties can be managed by visiting the `Harvesting -> Harvesters` section of the GeoNode admin area, or by visiting the `api/v2/harvesters/` API endpoint with an admin user.

Among other parameters, a harvester holds:

`remote_url`
: Base URL of the remote service being harvested, for example `https://stable.demo.geonode.org`

`harvester_type`
: Type of harvester worker that is used to perform harvesting. See the [harvester worker](#harvester-worker) concept and the [standard harvester workers](harvester_workers.md) page for more detail. Example: `geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker`

`scheduling_enabled`
: Whether harvesting shall be performed periodically by the [harvesting scheduler](#harvesting-scheduler) or not.

`harvesting_session_update_frequency`
: How often, in minutes, new harvesting sessions should be automatically scheduled.

`refresh_harvestable_resources_update_frequency`
: How often, in minutes, new refresh sessions should be automatically scheduled.

`default_owner`
: Which GeoNode user shall be made the owner of harvested resources.

`harvest_new_resources_by_default`
: Should new remote resources be harvested automatically? When this option is selected, the user does not need to specify which harvestable resources should be harvested, as all of them will be automatically marked for harvesting by GeoNode.

`delete_orphan_resources_automatically`
: Orphan resources are those that have previously been created by means of a harvesting operation but that GeoNode can no longer find on the remote service being harvested. Should these resources be deleted from GeoNode automatically? This also applies when a harvester configuration is deleted, in which case all of the resources that originated from that harvester are now considered orphan.

## harvester worker

Harvester workers implement retrieval for concrete remote service types. Each harvester uses a specific worker, depending on the type of remote service that it gets data from. Harvester workers may accept their own additional configuration parameters.

Harvester workers are set as the `harvester_type` attribute on a harvester. Their configuration is set as a JSON object on the `harvester_type_specific_configuration` attribute of the harvester.

GeoNode ships with the following harvester workers:

1. GeoNode, which enables harvesting from other GeoNode deployments
2. WMS, which enables harvesting from OGC WMS servers
3. ArcGIS REST services, which enables harvesting from ArcGIS REST services

Adding [new harvester workers](harvester_workers.md#creating-new-harvesting-workers) is also possible. This allows custom GeoNode deployments to add support for harvesting from other remote sources.

## harvestable resource

A resource that is available on the remote server. Harvestable resources are persisted in the GeoNode DB. They are created during [refresh operations](harvesting_operations.md#update-the-list-of-harvestable-resources-operation), when the harvester worker interacts with the remote service in order to discover which remote resources can be harvested.

Harvestable resources can be managed by visiting the `Harvesting -> Harvestable resources` section of the GeoNode admin area, or by visiting the `api/v2/harvesters/{harvester-id}/harvestable-resources` API endpoint with an admin user.

In order to be harvested by the [harvesting scheduler](#harvesting-scheduler), a harvestable resource must have its `should_be_harvested` attribute set to `True`. This attribute can be set manually by the user or it can be set automatically by the harvester worker, in case the corresponding harvester is configured with `harvest_new_resources_by_default = True`.

## harvesting session

In GeoNode, discovering remote resources and harvesting them is always done under the scope of a harvesting session. These sessions are stored in the GeoNode DB and can be inspected by visiting the `Harvesting -> Asynchronous harvesting sessions` section of the GeoNode admin area.

Harvesting sessions are used to keep track of the progress of execution of the relevant harvesting operations. They are updated while each operation is running. There are two types of sessions:

### refresh session

This session is created during the [update of harvestable resources operation](harvesting_operations.md#update-the-list-of-harvestable-resources-operation).
It has `type=discover-harvestable-resources`. During a refresh session, the harvester worker discovers remote resources and creates their respective harvestable resources in the GeoNode DB. After such session is finished, the user can inspect the found harvestable resources and mark those that are relevant with `should_be_harvester=True`.

### harvesting session

This session is created during the [perform harvesting operation](harvesting_operations.md#perform-harvesting-operation). It has `type=harvesting`. During a harvesting session, the harvester worker creates or updates new GeoNode resources based on the harvestable resources that have been configured with `should_be_harvested=True`.

In addition to the aforementioned `type`, harvesting sessions also carry the `status` attribute, which provides context on the current status of the session, and consequently of the underlying harvesting operation.

## harvesting scheduler

The scheduler is responsible for initiating new harvesting operations in an automated fashion. Periodically, the scheduler goes through the list of existing harvesters, checking if it is time to dispatch one of the harvesting operations mentioned in the next section.

The scheduler operation frequency is configurable by defining a `HARVESTER_SCHEDULER_FREQUENCY_MINUTES` setting, the default is to trigger the scheduler every 30 seconds.

!!! Note
    Since the harvesting scheduler only checks if there is work to do once every `x` seconds, defaulting to 30 seconds, there is usually a delay between the time a harvesting operation is supposed to be scheduled and the actual time when it is scheduled. Moreover, the harvesting scheduler is implemented as a Celery task. This means that, if the Celery worker is busy, that may also cause a delay in scheduling harvesting operations, as the scheduler Celery task may not be triggered immediately.
