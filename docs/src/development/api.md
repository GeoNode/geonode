In this section, we are going to demostrate how GeoNode API can be utilized/integrated with other applications using Python.

## Resource Listing and Details
As mentioned in previous chapters, GeoNode resources are categorized in different types e.g. datasets, maps, documents. Etc.
All available resources can be listed with API ``GET /api/v2/resources``.

To obtain a single resource, a primary key is provided in the url. Eg ``GET /api/v2/resources/{resource.pk}``.

Example Requests:

1. Listing:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources"
response = requests.request("GET", url)
```
2. Detail:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources/1797"
response = requests.request("GET", url)
```

!!! note
    The above requests work for publicly visible resources. If a resource is private either the Basic Auth or the Bearer token must be included inside the headers.

1. Listing with basic auth:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("GET", url, headers=headers)
```

A token can be used in place of Basic Auth by setting ``'Authorization': 'Bearer <token>'``.

## Resource Download


The download URL for a resource can be obtained from ``resource.download_url``. This URL executes the synchronous download of a resource in its default download format (ESRI Shapefile for vector, Geotiff for rasters and the original format for documents). 
Additional export formats for datasets are available through the UI. At the moment the API doesn’t expose them.

## Resource Links
From the resource detail response, URls and links to services can be obtained from the ``resource.links[]`` array value.
The purpose of each link is defined by its ``link_type``. The “name” also can specify additional information about the linked resource. 

### Metadata
Links to each metadata format can be obtained from links with ``link_type = "metadata"``

### OGC services
OGC requests can be built by taking:
the OGC base url from  links from ``resource.links[]`` with ``"link_type"= ("OGC:WMS | OGC:WFS | OGC:WCS)``
the OGC service layername obtained from the ``resource.alternate`` property 

### Embedding
A resource can be embedded inside a third party website. The “embed view” of a resource is suitable to be placed inside an iframe.
The URL for the embedded view can be obtained from the ``resource.embed_url`` property.

## Resource Searching and Filtering
GeoNode resources can be filtered with the following query parameters:


Parameter | URL
---------|----------
title and abstract ``(paginated free text search)`` | /api/v2/resources?page=1&search=text-to-search&search_fields=title&search_fields=abstract
resource_type ``(dataset, map, document, service, geostory, dashboard)`` | /api/v2/resources?filter{resource_type}=map
subtype ``(raster,vector, vector_time, remote)`` | /api/v2/resources?filter{resource_type}=vector
favorite ``(Boolean True)`` | /api/v2/resources?favorite=true
featured ``(Boolean True or False)``| /api/v2/resources?filter{resource_type}=vector
published ``(Boolean True or False)`` | /api/v2/resources?filter{is_published}=true
aprroved ``(Boolean True or False)``| /api/v2/resources?filter{is_approved}=true
category | api/v2/resources?filter{category.identifier}=example
keywords |  /api/v2/resources?filter{keywords.name}=example
regions |  /api/v2/resources?filter{regions.name}=global
owner |  /api/v2/resources?filter{owner.username}=test_user
extent ``(Four comer separated coordinates)`` |  /api/v2/resources?extent=-180,-90,180,90


1. Filter with a single value
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources/?filter{resource_type}=map"
response = requests.request("GET", url, headers=headers, data=payload
```
2. Filter with multiple values
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources/?filter{resource_type.in}=map&filter{resource_type.in}=dataset"
response = requests.request("GET", url, headers=headers, data=payload)
```

!!! note
    With filter APIs of format ``/api/v2/resources?filter{filter_key}=value``, additional methods(in and icontains) can be used on them to provide extensively filtered results.
    Eg
    ``/api/v2/resources?filter{regions.name.icontains}=global``
    ``/api/v2/resources?filter{regions.name.in}=global``.

    It's important to note that other methods are case sensitive except the icontains.


## Dataset specific resources
Get the metadata of uploaded datasets with:

- API: ``GET /api/v2/datasets/{id}``
- Status Code: ``200``
!!! note
       This is very similar to `GET /api/v2/resources` but provides additional metadata specifically for datasets like `featureinfo_custom_template` or `attribute_set`
    
Example:

```python
import requests

DATASET_ID = "the dataset id"
url = f"https://master.demo.geonode.org/api/v2/datasets/{DATASET_ID}"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("GET", url, headers=headers)
```

## Resource Upload
The API supports the upload of datasets and documents.

### Datasets
The dataset upload form accepts file formats of ESRI Shapefile, GeoTIFF, Comma Separated Value (CSV), Zip Archive, XML Metadata File, and Styled Layer Descriptor (SLD).
For a successful upload, the form requires base_file, dbf_file, shx_file, and prj_file. The xml_file, and Sld_file are optional.

- API: ``POST /api/v2/uploads/upload``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/uploads/upload"
files= [
('sld_file',('BoulderCityLimits.sld',open('/home/myuser/BoulderCityLimits.sld','rb'),'application/octet-stream')),   ('base_file',('BoulderCityLimits.shp',open('/home/BoulderCityLimits.shp','rb'),'application/octet-stream')),  ('dbf_file',('BoulderCityLimits.dbf',open('/home/BoulderCityLimits.dbf','rb'),'application/octet-stream')),  ('shx_file',('BoulderCityLimits.shx',open('/home/BoulderCityLimits.shx','rb'),'application/octet-stream')),
('prj_file',('BoulderCityLimits.prj',open('/home/myuser/BoulderCityLimits.prj','rb'),'application/octet-stream))
]
headers = {
'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("POST", url, headers=headers, files=files)
```

### Documents

Documents can be uploaded as form data.

- API: ``POST /api/v2/documents``
- Status Code: ``200``

Example:
```python
import requests

url = "http://localhost:8000/api/v2/documents"
payload={
    'title': 'An example image'
}
files=[
    ('doc_file',('image.jpg',open('/home/myuser/image.jpg','rb'),'image/jpeg'))
]
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("POST", url, headers=headers, data=payload, files=files)
```

Documents can also be created to reference remote resources. In this case the ``doc_url`` parameter must be used to set the URL of the remote document.

- API: ``POST /api/v2/documents``
- Status Code: ``200``

Example:
```python
import requests

url = "http://localhost:8000/api/v2/documents"
payload={
    'title': 'An example image',
    'doc_url' : 'http://examples.com/image.jpg'
}
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("POST", url, headers=headers, data=payload, files=files)
```

Notice that if the URL doesn't end with a valid doc extension, the ``extension`` parameter must be used (e.g. ``extension: 'jpeg'``).

### Tracking dataset upload progress

When an upload request is executed, GeoNode creates an "Execution request" and keeps updating its state and progress (it’s a property attribute, calculated on getting the response) attributes as the resource is being created and configured in Geoserver.
An execution can be in one of the following status:
    - ``ready``
    - ``running``
    - ``failed``
    - ``finished``

When the dataset is successfully uploaded, the final state of the upload is set to ``finished``.

In order to view status of the execution, the API method ``GET /api/v2/executionrequest/{execution_id}`` where ``{execution_id}`` is the value returned by the initial call to the upload API. 

The returned object contains, beyond all the information related to the execution, the inputs that were passed to the execution request, and output params specific to the type of execution.
In the case of a dataset upload, the output params contain the URL of the catalog page for the new datast.


```json
"output_params": {
    "detail_url": [
        "/catalogue/#/dataset/9881"
    ]
}
```

You can also filter executions by status.
Eg ``GET /api/v2/executionrequest?filter{action}=import&filter{source}=upload&filter{status}=finished``


Example:
```python
import requests

url = "https://stable.demo.geonode.org/api/v2/executionrequest/5f640b6b-8c51-4514-a054-995133fee107"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("GET", url, headers=headers)
```

### Overwriting a dataset

Uploading a resource will create by default a new dataset. This behaviour can be changed by setting the ``overwrite_existing_layer`` parameter to ``True``. 
In this case the upload procedure will overwrite a resource whose name matches with the new one.

### Skip existing dataset

If the parameter ``skip_existing_layers`` is set to true ``True`` the uplad procedure will ignore files whose name matched with already existing resources.

### Upload of a metadata file

A complete metadata file conforming to ISO-19115 can be uploaded for a dataset.

- API: ``PUT /api/v2/datasets/{dataset_id}/metadata``
- Status Code: ``200``

Example:
```python
import requests

url = "http://localhost:8000/api/v2/datasets/1/metadata"
files=[
        ('metadata_file',('metadata.xml',open('/home/user/metadata.xml','rb'),'text/xml'))
    ]
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("PUT", url, headers=headers, data={}, files=files)
```

## Resource Delete
- API: ``DELETE /api/v2/resources/{pk}/delete``
- Status Code: ``204``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources/1778"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("DELETE", url, headers=headers)
```

## Resource Download
GeoNode offers a download option to resources of resource_type dataset and document.
For datasets, the download option is available for only datasets with uploaded files.

### Datasets
- API: ``GET /datasets/{resource.alternate}/dataset_download``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/datasets/geonode:BoulderCityLimits3/dataset_download"
response = requests.request("GET", url)
```

### Documents

- API: ``GET /documents/{resource.pk}/download``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/documents/1781/download"
response = requests.request("GET", url)
```

## Dataset Update Metadata 

- API: ``PATCH /api/v2/datasets/{id}``
- Status Code: ``200``

The following example changes the title and the license of a dataset.
```python
import requests

url = ROOT + "api/v2/datasets/" + DATASET_ID
auth = (LOGIN_NAME, LOGIN_PASSWORD)

data = {
    "title": "a new title",
    "license": 4, 
}
response = requests.patch(url, auth=auth, json=data)
```

!!! note
    `bbox_polygon` and `ll_bbox_polygon` are derived values which cannot be changed.

## Users, Groups and Permissions

### Users


Listing
- API: ``POST /api/v2/users``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/users"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("GET", url, headers=headers)
```
 
### User detail

- API: ``POST /api/v2/users/{pk}``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/users/1000"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("GET", url, headers=headers)
```

### Create a new user
- API: ``POST /api/v2/users``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/users"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
payload={"username": "username",
        "password": "password",
        "email": "email@email.com",
        "first_name":"first_name",
        "last_name":"last_name",
        "avatar": "https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240"}
response = requests.request("POST", url, headers=headers, data=payload)
```

### Edit a User
- API: ``PATCH /api/v2/users/{pk}``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/users/1000"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
payload={"password": "new_password"}
response = requests.request("PATCH", url, headers=headers, data=payload)
```

### Delete a User
- API: ``DELETE /api/v2/users/{pk}``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/users/1000"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
payload={"password": "new_password"}
response = requests.request("DELETE", url, headers=headers, data=payload)
```
In this case the list of validation rules configured in :ref:`user-deletion-rules` are checked before the deletion is executed.

### List user groups
- API: ``POST /api/v2/users/{pk}/groups``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/users/1000/groups"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("GET", url, headers=headers)
```
### Transfer resources owned by a user to another
- API: ``POST /api/v2/users/{pk}/transfer_resources``
- Status Code: ``200``

Example:
```python
import requests
payload={"owner": 1001}
url = "https://master.demo.geonode.org/api/v2/users/1000/transfer_resources"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("POST", url, headers=headers, data=payload)
```

In this case the resources will be transfered to the user with id 1001,
instead using the payload={"owner": "DEFAULT"} the resources will be transfered to the principal user

### Remove user as a group manager

- API: ``POST /api/v2/users/{pk}/remove_from_group_manager``
- Status Code: ``200``

Example:
```python
import requests
payload={"groups": [1,2,3]}
url = "https://master.demo.geonode.org/api/v2/users/1000/remove_from_group_manager"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("POST", url, headers=headers, data=payload)
```

In this case the user shall be removed as a group manager from the following group ids, 
if the payload would be payload={"groups": "ALL"} the user will be removed as a group manager from all the groups its part of

### Groups
In GeoNode, On listing groups, the api returns groups which have group profiles. Therefore for django groups which are not related to a group profile are not included in the response. However these can be accessed in the Django Administration panel.

- API: ``POST /api/v2/groups``
- Status Code: ``200``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/groups"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("GET", url, headers=headers)
```

## Permissions
Permissions in GeoNode are set per resource and per user or group. The following are general permissions that can be assigned:

- *View:* allows to view the resource. ``[view_resourcebase]``
- *Download:* allows to download the resource specifically datasets and documents. ``[ view_resourcebase, download_resourcebase]``
- *Edit:* allows to change attributes, properties of the datasets features, styles and metadata for the specified resource. ``[view_resourcebase, download_resourcebase, change_resourcebase, change_dataset_style, change_dataset_data, change_resourcebase_metadata]``
- *Manage:* allows to update, delete, change permissions, publish and unpublish the resource. ``[view_resourcebase, download_resourcebase, change_resourcebase, change_dataset_style, change_dataset_data, publish_resourcebase, delete_resourcebase, change_resourcebase_metadata, change_resourcebase_permissions]``

### Obtaining permissions on a resource

On listing the resources or on resource detail API, GeoNode includes perms attribute to each resource with a list of permissions a user making the request has on the respective resource.

GeoNode also provides an API to get an overview of permissions set on a resource. The response contains users and groups with permissions set on them. However this API returns ``200`` if a requesting user has ``manage`` permissions on the resource otherwise it will return ``403 (Forbidden)``.

- API: ``GET /api/v2/resources/1791/permissions``

Example:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources/1791/permissions"
headers = {
    'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("GET", url, headers=headers)
```

### Changing permissions on a resource

Permissions are configured with a so called ``perms spec``, which is a JSON structured where permissions for single users and groups can be specified.

The example below shows a perm specification for following rules:

- user1 can ``edit``
- user2 can ``manage``
- group1 can ``edit``
- anonymous users (public) can ``view``
- registered members can ``download``

!!! note 
    The id of the “anonymous” and “registered members” groups can be obtained from the permissions of the resource. They are not listed inside the groups API, since these are spceial internal groups

```json
{ 
    "users": [
        {
            "id": <id_of_user1>,
            "permissions": "edit"
        },
        {
            "id": <id_of_user2>,
            "permissions": "manage"
        }
    ],
    "organizations": [
        {
            "id": <id_of_group1>,
            "permissions": "edit"
        },
    ],
    "groups": [
        {
            "id": <id_of_anonymous_group>,
            "permissions": "view"
        },
        {
            "id": <id_of_regisdtered-members_group>,
            "permissions": "download"
        }
    ]
}
```
The perm spec is sent as JSON, with ``application/json Content-Type``, inside a ``PUT`` request.

```python
import requests
import json

url = "https://master.demo.geonode.org/api/v2/resources/1791/permissions"
payload = json.dumps({
"users": [
    {
    "id": 1001,
    "permissions": "edit"
    },
    {
    "id": 1002,
    "permissions": "manage"
    }
],
"organizations": [
    {
    "id": 1,
    "permissions": "edit"
    }
],
"groups": [
    {
    "id": 2,
    "permissions": "view"
    },
    {
    "id": 3,
    "permissions": "download"
    }
]
})
headers = {
'Authorization': 'Basic dXNlcjpwYXNzd29yZA==',
'Content-Type': 'application/json',
}

response = requests.request("PUT", url, headers=headers, data=payload)
```

This is an asynchrnous operation which returns a response similar to the following:

```json
{
    "status": "ready",
    "execution_id": "7ed578c2-7db8-47fe-a3f5-6ed3ca545b67",
    "status_url": "https://master.demo.geonode.org/api/v2/resource-service/execution-status/7ed578c2-7db8-47fe-a3f5-6ed3ca545b67"
}
```


The ``status_url`` property returns the URL to track kthe progress of the request. Querying the URL a result similar to the following will be returned:

```json
{
    "user": "admin",
    "status": "running",
    "func_name": "set_permissions",
    "created": "2022-07-08T11:16:32.240453Z",
    "finished": null,
    "last_updated": "2022-07-08T11:16:32.240485Z",
    "input_params": {
    …
    }
}
```

The operation will be completed once the ``status`` property is updated with the value ``finished``.

## Linked Resources Listing and Details

All available linked_resources  can be listed with API ``GET /api/v2/resources/{pk}/linked_resources``.
where pk Resource base id

Example Requests:
^^^^^^^^^^^^^^^^^

1. List all resource links:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources/{pk}/linked_resources"
response = requests.request("GET", url)
```

## Assets

### Assets Upload

Assets can be attached to a resource as a file.


**Endpoint**:

- **API**: ``POST /api/v2/resources/{pk}/assets/``
- **Status Code**: ``201``

where ``{pk}`` is the resource base id to which the asset is to be attached.

**Parameters**:

Parameter | Type | Description
---------|----------|----------
``files`` | Files | The files to upload, can be multiple files
``title`` | String | Title for the asset which is optional
``description`` | String | Description of the asset which is optional

Example Request:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources/{pk}/assets/"

payload = {
'title': 'My Asset Title',
'description': 'Description of my asset'
}

files=[
('file',('assets.png',open('/location/of/file','rb'),'image/png'))
]

headers = {
'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}

response = requests.request("POST", url, headers=headers, data=payload, files=files)
```

### Asset Remove

Atatched assets can be removed from a resource.

**Endpoint**:

- **API**: ``DELETE /api/v2/resources/{resource_pk}/assets/{asset_pk}``
- **Status Code**: ``204``

where ``{resource_pk}`` is the resource base id from which the asset is to be removed and ``{asset_pk}`` is the asset id to be removed.

Example Request:
```python
import requests

url = "https://master.demo.geonode.org/api/v2/resources/{resource_pk}/assets/{asset_pk}"

headers = {
'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
}
response = requests.request("DELETE", url, headers=headers)
```
