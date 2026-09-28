# Resource Information

From the *resources catalog* (e.g. `Datasets`, `Maps`, etc.) you can select the `Open properties` icon for the resource you are interested in to see an overview of it. In the images below, we use a `dataset` as an example, but a similar `properties table` is used for all resources.

![](img/resource_overview.png){ align=center }

## General `properties table` tabs

This section presents the `properties table` tabs that are available for all resources (e.g. `Documents`, `GeoStories`, etc.).

- The *Info* tab is active by default. This tab section shows resource metadata such as its title, abstract, date of publication, and more. The metadata also indicates the resource owner, the topic categories the resource belongs to, and the affected regions.
  It is worth noting that for all resources, the user can view the full metadata by clicking `View full metadata`, which is presented at the end of the `Info` tab section.

![](img/resource_info.png){ align=center }
/// caption
*Resource Info tab*
///

- The *Location* tab shows the spatial extent of the resource.

![](img/resource_location.png){ align=center }
/// caption
*Resource Location tab*
///

By clicking the copy icons, you can copy the current *Bounding Box* or the *Center* to the clipboard. Once pasted, it will be a WKT text.

![](img/copy_locations_resource.png){ align=center }
/// caption
*Bounding Box and Center*
///

- The *Relations* tab lets you see which other resources are linked to this one.

![](img/map_relations.png){ align=center }
/// caption
*Relations tab of a map, listing the datasets it uses as layers*
///

!!! Note
    The *Relations* tab is only displayed when the resource actually has something to list. When a resource has no relations at all, the tab is hidden rather than shown empty.

The tab lists the related resources you have permission to view. Relations themselves come from two different sources.

**Automatic relations** are derived by GeoNode from the way resources are actually used. They are kept up to date on their own:

- a *Map* lists the *Datasets* it uses as layers;
- a *Dataset* lists the *Maps* that use it as a layer.

**Manual relations** are links you create yourself, through the *Related resources* field of the metadata editor. Any resource can be linked to any other resource. These links appear in the *Relations* tab alongside the automatic ones. See [Metadata](metadata.md) for how to create them.

Because *GeoStories* and *Dashboards* have no automatic relations, their *Relations* tab appears only once manual links have been added.

- The *Assets* tab presents the current resource download link. Moreover, the user can add additional assets related to this resource.

![](img/resource_assets.png){ align=center }
/// caption
*Resource Assets tab*
///

- The *Share* tab allows the owner of the resource to edit its permissions.

![](img/resource_share.png){ align=center }
/// caption
*Resource Share tab*
///

For detailed information about the `Share` options, please take a look at [Share options](sharing.md).

- The *Settings* tab allows the owner of the resource to define a group, the publishing status, and more options (e.g. Approved).

![](img/resource_settings.png){ align=center }
/// caption
*Resource Settings tab*
///

From the upper left toolbar on the thumbnail part of the properties panel, it is possible to:

![](img/resource_info_toolbar.png){ align=center }
/// caption
*Resource Info toolbar*
///

- Upload a new thumbnail for the resource
- Set a thumbnail by using the full extent of the resource (in the case of a `Dataset` or a `Map`)
- Remove the thumbnail

From the lower right toolbar on the thumbnail part of the properties panel, it is possible to:

- Save the current changes of the resource (this is not included for `Maps`)
- Download the resource (this is not included for `Maps`)
- Copy the resource URL
- Copy the OGC resource web services URL (in the case of a `Dataset`)

## Cloning a resource

Cloning creates a new, fully independent resource. It gets its own UUID, its own permissions record, and, for a `Dataset`, its own copy of the data on the GIS backend. Ownership of the clone is transferred to whoever triggers it, regardless of who owned the source.

What is carried over from the source:

- Metadata: title, abstract, category, license, and every other descriptive field
- Keywords, regions, and thesaurus keywords
- Contacts and their roles (point of contact, metadata author, and so on)
- Geographic access limits (per-user and per-group)
- Permissions: the clone starts with the same permission spec as the source, not the default permissions a newly created resource would get
- Linked resources (e.g. a `Map`'s linked `Datasets`)
- Type-specific data: a `Dataset`'s attribute table, a `Map`'s layers, and the underlying files/assets

What does not carry over:

- The owner, which becomes the user who triggered the clone
- The `featured` flag, always reset to off on the clone

Because the clone owns its own copy of everything above rather than sharing rows with the source, deleting the source resource afterward does not affect the clone.

You can access the resource details page by clicking the button on the right (`View dataset` in the case of a `dataset`) in the overview panel.
That page looks like the one shown in the picture below.

![](img/resource_detail.png){ align=center }
/// caption
*Resource page*
///

## Specific `properties table` tabs

Beyond the general tabs, there are a few tabs for specific resources:

### Dataset resource

- The *Data* tab shows the data structure behind the dataset. All attributes are listed and, for each of them, some statistics (e.g. the range of values) are estimated when possible.

![](img/dataset_attributes_tab.png){ align=center }
/// caption
*Dataset Attributes tab*
///
