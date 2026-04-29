# Harvesting workflows

There are two main possible harvesting workflows:

1. Continuous harvesting
2. One-time harvesting

## Continuous harvesting

This workflow relies on the [harvesting scheduler](gnode_harvesting_concepts.md#harvesting-scheduler) in order to ensure harvested resources are continuously kept up to date with their remote counterparts.

1. The user creates a harvester and sets its `scheduling_enabled` attribute to `True`
2. When the time comes, the harvesting scheduler calls the [update list of harvestable resources operation](harvesting_operations.md#update-the-list-of-harvestable-resources-operation). Alternatively, the user may call this operation manually the first time
3. When the previous operation is done, the user goes through the list of generated [harvestable resources](gnode_harvesting_concepts.md#harvestable-resource) and, for each relevant harvestable resource, sets its `should_be_harvested` attribute to `True`. Alternatively, if the harvester has its `harvest_new_resources_automatically` attribute set to `True`, the harvestable resources are already marked as to be harvested, without requiring manual user intervention
4. When the time comes, the harvesting scheduler calls the [perform harvesting operation](harvesting_operations.md#perform-harvesting-operation). This causes the remote resources to be harvested. These now show up as resources on the local GeoNode

## One-time harvesting

This workflow is mostly executed manually by the user.

1. The user creates a harvester and sets its `scheduling_enabled` attribute to `False`
2. The user calls the [update list of harvestable resources operation](harvesting_operations.md#update-the-list-of-harvestable-resources-operation)
3. When the previous operation is done, the user goes through the list of generated [harvestable resources](gnode_harvesting_concepts.md#harvestable-resource) and, for each relevant harvestable resource, sets its `should_be_harvested` attribute to `True`
4. The user then proceeds to call the [perform harvesting operation](harvesting_operations.md#perform-harvesting-operation). This causes the remote resources to be harvested. These now show up as resources on the local GeoNode
