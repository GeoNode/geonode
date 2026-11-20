# Importer hooks

The importer fires an event at each lifecycle transition of an `ExecutionRequest`. Code outside the handlers (e.g. an external Django app) can subscribe to these events to send notifications, update external systems or collect statistics, without subclassing any handler.

## Events

An event is named `<action>.<phase>`:

- `action` is the `ExecutionRequest.action` value: `upload`, `copy`, `replace`, `upsert`, `resource_metadata_upload`, `resource_style_upload`, `document_upload`, ... Custom actions defined by out-of-tree handlers work too.
- `phase` is one of:

| Phase | When it fires |
|---|---|
| `started` | The first step of the execution starts and the status becomes `running`. |
| `completed` | The status becomes `finished`. `output_params["resources"]` is already filled. |
| `partially_failed` | Some layers are imported and some failed. The status becomes `failed`, `output_params["resources"]` lists the imported layers. |
| `failed` | The status becomes `failed`. |

`*` matches any action or any phase: `upload.*`, `*.failed`, `*.*`. An unknown phase raises `ValueError` when the callback is added.

## Callbacks

A callback receives the execution, the handler class and the event kwargs:

```python
def my_callback(execution, handler, **kwargs):
    ...
```

- `execution` is the `ExecutionRequest`, read after the status change.
- `handler` is the handler class from `execution.input_params["handler_module_path"]`, or `None` if it is missing or cannot be imported.
- `failed` and `partially_failed` pass `reason`. For `partially_failed` it is the list of the layers not imported. For `failed` it is the error, as received by `set_as_failed`: a string, an exception or `None`.

Callbacks are called by priority (lower first, default `10`), then in registration order.

## The execution object

The `execution` passed to a callback is a snapshot, read right after the status change: other workers keep updating the row (other layers, rollback, a late failure), and its owner can delete it. Treat it as read-only context of the event, not as the current state:

- never call `execution.save()`: it overwrites what the other workers wrote;
- in a custom async task, pass `str(execution.exec_id)` and the values you need, then read the execution again and handle a missing row or a changed status;
- `user` can be `None`, and the files in `input_params` may already be deleted.

## Registering a subscriber

Define a subclass of `BaseImporterSubscriber`:

```python
from geonode.upload.hooks import BaseImporterSubscriber


class MyNotifier(BaseImporterSubscriber):
    def register(self, hooks):
        hooks.add_action("upload.completed", self.notify)
        hooks.add_action("*.failed", self.alert, priority=5)

    def notify(self, execution, handler, **kwargs):
        resources = execution.output_params.get("resources", [])
        ...

    def alert(self, execution, handler, reason=None, **kwargs):
        ...
```

and list it in the settings:

```
IMPORTER_HOOK_SUBSCRIBERS="['my_app.hooks.MyNotifier']"
```

The subscribers are registered at startup, after the handlers. A class that is not a `BaseImporterSubscriber` raises `TypeError`.

An external Django app can also add its callbacks directly in its own `AppConfig.ready()`, without the setting:

```python
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "my_app"

    def ready(self):
        # here to avoid AppRegistryNotReady: hooks imports the resource models
        from geonode.upload.hooks import importer_hooks
        from my_app.hooks import notify

        importer_hooks.add_action("upload.completed", notify)
```

`importer_hooks.remove_action(event, callback)` removes a callback added with the same event.

## Example: email the uploader when an upload completes

The subscriber below listens only to `upload.completed`: replace, upsert, copy and the failures are ignored. It sends the uploader an email with the links of the imported resources.

```python
# my_app/hooks.py
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail

from geonode.upload.hooks import BaseImporterSubscriber


class UploadCompletedNotifier(BaseImporterSubscriber):
    def register(self, hooks):
        hooks.add_action("upload.completed", self.notify_uploader)

    def notify_uploader(self, execution, handler, **kwargs):
        if not execution.user or not execution.user.email:
            return
        # resources is filled before completed fires: no need to read the execution again
        links = [urljoin(settings.SITEURL, r["detail_url"]) for r in execution.output_params.get("resources", [])]
        send_mail(
            subject=f"Upload {execution.name} completed",
            message="Your upload is completed, the imported resources are:\n" + "\n".join(links),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[execution.user.email],
        )
```

```
IMPORTER_HOOK_SUBSCRIBERS="['my_app.hooks.UploadCompletedNotifier']"
```

The callback runs in the importer worker: if the mail server is slow, send the email from a Celery task of your own instead.

## Behaviour to know

- Callbacks run synchronously, in the process that changes the status: usually the Celery worker of the importer, but the web process when the API view fails before dispatching the import. Keep them fast and move slow work to a Celery task of your own.
- A failing callback is logged and does not stop the other callbacks. It never changes the execution status.
- Callbacks must not call `orchestrator.set_as_*`.
- `completed`, `partially_failed` and `failed` fire once per execution, also when several workers end it at the same time (e.g. a multi-layer upload). A second failure appends its reason to `execution.log` without firing `failed` again.
- `started` does not fire again for the rollback of a failed execution.
- `failed` and `partially_failed` can fire after `completed`: an error raised after the execution finished moves it to `failed`.
- In a multi-layer upload, the rollback of a failed layer fails the execution while the other layers are still importing: `failed` fires and `partially_failed` does not. The layers not imported are appended to `execution.log`.
- `failed` can fire without `started`, when the API view fails after creating the execution.
- `failed` fires after the cleanup of the uploaded asset: the callback may not find the uploaded files.
- The handler `perform_last_step` runs before `completed` and `partially_failed`, on every path that ends the execution. If it raises, the execution fails: `failed` fires instead.
- `add_action` does not check for duplicates: a callback added twice is called twice.
