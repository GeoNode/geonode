# Supervisord and Systemd

## Celery

## Rabbitmq and Redis

## How to: Async Upload via API

In GeoNode it is possible to upload resources via API in async or sync way.

Here is available a full example of upload via API:
[GeoNode upload API test example](https://github.com/GeoNode/geonode/blob/582d6efda74adb8042d1d897004bbf764e6e0285/geonode/upload/api/tests.py#L416)

### Step 1

Create a common client session, this is fundamental due to the fact that GeoNode will check the request session.
For example with `requests` we will do something like:

```python
import requests
client = requests.session()
```

Note: in Django this part is already managed.

### Step 2

Call the `api/v2/uploads/upload` endpoint with `PUT`, it is a `form-data` endpoint, by specifying in `files` a dictionary with the names and the files that we want to upload, and a `data` payload with the required information.

For example:

```python
params = {
    "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',  # layer permissions
    "time": "false",
    "layer_title": "layer_title",
    "time": "false",
    "charset": "UTF-8",
}

files = {
    "filename": <_io.BufferedReader name="filename">
}

client.put(
    "http://localhost:8000/api/v2/uploads/upload/",
    auth=HTTPBasicAuth(username, password),
    data=params,
    files=files,
)

Returns:
- dict with import id of the resource
```

### Step 3

Call the final upload page in order to trigger the actual import.
If correctly set, GeoServer will manage the upload asynchronously.

```python
client.get("http://localhost:8000/upload/final?id={import_id}")

The `import_id` is returned from the previous step
```

### Step 4

The upload has been completed on GeoNode, we should check until GeoServer has completed its part.
To do so, it is enough to call the detailed information about the upload that we are performing:

```python
client.get(f"http://localhost:8000/api/v2/uploads/{upload_id}")
```

When the status is `PROCESSED` and the completion is `100%` we are able to see the resource in GeoNode and GeoServer.
