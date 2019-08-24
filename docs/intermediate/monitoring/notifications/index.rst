Monitoring: Notifications
=========================

Notifications are part of monitoring that is run after each data collection cycle.
It's configurable mechanism to check if metrics values are within allowed value range, and if not, send notification to designated receivers (registered users or external emails).

Data model
----------

Notification mechanism is composed of several classes, responsible for different aspects:

* High-level configuration: `NotificationCheck`:

    keeps general description, list of metric check definition, send grace period configuration and last send marker, list of users to which notification should be delivered (in helper table, `NotificationReceiver` class).

* Per-metric definition: `MetricNotificationDefinition`:

    keeps per-metric-per-check configuration: name of metric, min, max values allowed for user, check type (if value should be below or above given threshold, or should last read be not older than specific period from metric check), additional scope for check (resource, label, ows service - this part is partially implemented). Definition object is created from `NotificationCheck.user_tresholds` data, and is used to generate validation form.
    Note, that one `NotificationCheck` can have several definition items, for set of different metrics. Definition rows are created when `NotificationCheck` is created, or updated.

* Per-metric check configuration: `MetricNotificationCheck`

    Keeps per-metric-per-check configuration: metric and threshold values. It is created after user submits configuration form for specific notification.

Workflow
--------

Notifications are checked after each collection/processing period in collection script, by calling `CollectorAPI.emit_notifications(for_timestamp)`. This will do following:

* get all notifications,
* for each notification, will get all notification checks
* for each notification check, it will get metric valid for given timestamp and check if value matches given criteria
* each check can raise exception, which will be captured in caller, and for each notification, list of errors will be returned
* based on list of notifications and errors, alerts will be generated and send to users, unless last delivery was before grace period is finished.

Additionally, notifications expose ``/monitoring/api/status/`` :ref:`status-api`, which will show errors detected at the moment of request.

Web API
=======

.. _status-api:

Status API
----------

Status endpoint presents current state of error checking performed by notifications.
Frontend can make requests periodically to this endpoint.
There is no history view for status at the moment.
Status response is wrapped with standard response envelope.
Non-error response will have `status` key set to `ok` and `success` to `true`, otherwise `errors` will be not empty.

No errors response:

``GET /monitoring/api/status/``

.. code-block:: json

    {
        "status": "ok",
        "data": [],
        "success": true
    }

Response with errors reported:

.. code-block:: json

    {
      "status": "ok",
      "data": [
        {
          "problems": [
            {
              "threshold_value": "2017-08-29T10:45:26.142",
              "message": "Value collected too far in the past",
              "name": "request.count",
              "severity": "warning",
              "offending_value": "2017-08-25T16:41:00"
            }
          ],
          "check": {
            "grace_period": {
              "seconds": 600,
              "class": "datetime.timedelta"
            },
            "last_send": null,
            "description": "detects when requests are not handled",
            "severity": "warning",
            "user_threshold": {
              "3": {
                "max": 10,
                "metric": "request.count",
                "steps": null,
                "description": "Number of handled requests is lower than",
                "min": 0
              },
              "4": {
                "max": null,
                "metric": "request.count",
                "steps": null,
                "description": "No response for at least",
                "min": 60
              },
              "5": {
                "max": null,
                "metric": "response.time",
                "steps": null,
                "description": "Response time is higher than",
                "min": 500
              }
            },
            "id": 2,
            "name": "geonode is not working"
          }
        }
      ],
      "success": true
    }

Response with reported errors contains list of check elements in `data` element. Each check element contains:

* `check` - serialized `NotificationCheck` object, which was used
* `problems` - list of metric checks that failed. Each element contains name of metric, severity, error message, measured and threshold value.

Severity
~~~~~~~~

Severity is a textual description of potential impact of error. There are three values: `warning`, `error` and `fatal`.

Notification list
-----------------

This call will return list of available notifications:

``GET /monitoring/api/notifications/``

.. code-block:: json

    {
      "status": "ok",
      "data": {
        "problems": [
          {
            "threshold_value": "10.0000",
            "check_url": "/monitoring/api/notifications/config/2/",
            "name": "request.count",
            "check_id": 2,
            "description": "Metric value for request.count should be at least 10, got 4 instead",
            "offending_value": "4.0000",
            "message": "Number of handled requests is lower than 4",
            "severity": "error"
          }
        ],
        "health_level": "error"
      },
      "success": true
    }

Response will contain list of notifications summary in `data` key. Each element will have:

* `name` of metric checked
* `message` is error message generated by notification. This describes what the problem is.
* `description` more detailed information what which check failed.
* `offending_value` and `threshold_value` are values that were compared (`offending_value` is acutal value from metric data)
* `check_url` to notification details
* `severity` of error

Also, `data` will have highest `severity` value available in `health_level`.

Notification details
--------------------

This will return details for notification, including form and list of allowed fields:

``GET /monitoring/api/notifications/config/{{notification_id}}/``

.. code-block:: json

    {
      "status": "ok",
      "errors": {},
      "data": {
        "fields": [
          {
            "is_enabled": true,
            "use_resource": false,
            "description": "Number of handled requests is lower than",
            "max_value": "10.0000",
            "metric": {
              "class": "geonode.contrib.monitoring.models.Metric",
              "name": "request.count",
              "id": 2
            },
            "min_value": "0.0000",
            "use_label": false,
            "use_ows_service": false,
            "field_option": "min_value",
            "use_service": false,
            "steps_calculated": [
              "0.0000",
              "3.33",
              "6.67",
              "10.0"
            ],
            "current_value": "30.0000",
            "steps": 3,
            "notification_check": {
              "class": "geonode.contrib.monitoring.models.NotificationCheck",
              "name": "geonode is not working",
              "id": 2
            },
            "field_name": "request.count.min_value",
            "id": 3,
            "unit": ""
          },
          {
            "is_enabled": true,
            "use_resource": false,
            "description": "No response for at least",
            "max_value": null,
            "metric": {
              "class": "geonode.contrib.monitoring.models.Metric",
              "name": "request.count",
              "id": 2
            },
            "min_value": "60.0000",
            "use_label": false,
            "use_ows_service": false,
            "field_option": "max_timeout",
            "use_service": false,
            "steps_calculated": null,
            "current_value": {
              "seconds": 120,
              "class": "datetime.timedelta"
            },
            "steps": null,
            "notification_check": {
              "class": "geonode.contrib.monitoring.models.NotificationCheck",
              "name": "geonode is not working",
              "id": 2
            },
            "field_name": "request.count.max_timeout",
            "id": 4,
            "unit": ""
          },
          {
            "is_enabled": false,
            "use_resource": false,
            "description": "Response time is higher than",
            "max_value": null,
            "metric": {
              "class": "geonode.contrib.monitoring.models.Metric",
              "name": "response.time",
              "id": 11
            },
            "min_value": "500.0000",
            "use_label": false,
            "use_ows_service": false,
            "field_option": "max_value",
            "use_service": false,
            "steps_calculated": null,
            "current_value": null,
            "steps": null,
            "notification_check": {
              "class": "geonode.contrib.monitoring.models.NotificationCheck",
              "name": "geonode is not working",
              "id": 2
            },
            "field_name": "response.time.max_value",
            "id": 5,
            "unit": "s"
          },
          {
            "is_enabled": false,
            "use_resource": false,
            "description": "dsfdsf",
            "max_value": null,
            "metric": {
              "class": "geonode.contrib.monitoring.models.Metric",
              "name": "response.time",
              "id": 11
            },
            "min_value": null,
            "use_label": false,
            "use_ows_service": false,
            "field_option": "min_value",
            "use_service": false,
            "steps_calculated": null,
            "current_value": null,
            "steps": null,
            "notification_check": {
              "class": "geonode.contrib.monitoring.models.NotificationCheck",
              "name": "geonode is not working",
              "id": 2
            },
            "field_name": "response.time.min_value",
            "id": 6,
            "unit": "s"
          },
          {
            "is_enabled": true,
            "use_resource": false,
            "description": "Incoming traffic should be higher than",
            "max_value": null,
            "metric": {
              "class": "geonode.contrib.monitoring.models.Metric",
              "name": "network.in.rate",
              "id": 34
            },
            "min_value": null,
            "use_label": false,
            "use_ows_service": false,
            "field_option": "min_value",
            "use_service": false,
            "steps_calculated": null,
            "current_value": "10000000.0000",
            "steps": null,
            "notification_check": {
              "class": "geonode.contrib.monitoring.models.NotificationCheck",
              "name": "geonode is not working",
              "id": 2
            },
            "field_name": "network.in.rate.min_value",
            "id": 7,
            "unit": "B/s"
          }
        ],
        "form": "<tr><th><label for=\"id_emails\">Emails:</label></th><td><textarea cols=\"40\" id=\"id_emails\" name=\"emails\" rows=\"10\">\r\n\nad@m.in</textarea></td></tr>\n<tr><th><label for=\"id_severity\">Severity:</label></th><td><select id=\"id_severity\" name=\"severity\">\n<option value=\"warning\">Warning</option>\n<option value=\"error\" selected=\"selected\">Error</option>\n<option value=\"fatal\">Fatal</option>\n</select></td></tr>\n<tr><th><label for=\"id_active\">Active:</label></th><td><input checked=\"checked\" id=\"id_active\" name=\"active\" type=\"checkbox\" /></td></tr>\n<tr><th><label for=\"id_grace_period\">Grace period:</label></th><td><input id=\"id_grace_period\" name=\"grace_period\" type=\"text\" value=\"00:01:00\" /></td></tr>\n<tr><th><label for=\"id_request.count.min_value\">Request.count.min value:</label></th><td><select id=\"id_request.count.min_value\" name=\"request.count.min_value\">\n<option value=\"0.0000\">0.0000</option>\n<option value=\"3.33\">3.33</option>\n<option value=\"6.67\">6.67</option>\n<option value=\"10.0\">10.0</option>\n</select></td></tr>\n<tr><th><label for=\"id_request.count.max_timeout\">Request.count.max timeout:</label></th><td><input id=\"id_request.count.max_timeout\" min=\"60.0000\" name=\"request.count.max_timeout\" step=\"0.01\" type=\"number\" /></td></tr>\n<tr><th><label for=\"id_response.time.max_value\">Response.time.max value:</label></th><td><input id=\"id_response.time.max_value\" min=\"500.0000\" name=\"response.time.max_value\" step=\"0.01\" type=\"number\" /></td></tr>\n<tr><th><label for=\"id_response.time.min_value\">Response.time.min value:</label></th><td><input id=\"id_response.time.min_value\" name=\"response.time.min_value\" step=\"0.01\" type=\"number\" /></td></tr>\n<tr><th><label for=\"id_network.in.rate.min_value\">Network.in.rate.min value:</label></th><td><input id=\"id_network.in.rate.min_value\" name=\"network.in.rate.min_value\" step=\"0.01\" type=\"number\" /></td></tr>",
        "notification": {
          "grace_period": {
            "seconds": 60,
            "class": "datetime.timedelta"
          },
          "last_send": "2017-09-04T13:13:15.203",
          "description": "detects when requests are not handled",
          "severity": "error",
          "user_threshold": {
            "request.count.max_timeout": {
              "max": null,
              "metric": "request.count",
              "steps": null,
              "description": "No response for at least",
              "min": 60
            },
            "response.time.max_value": {
              "max": null,
              "metric": "response.time",
              "steps": null,
              "description": "Response time is higher than",
              "min": 500
            },
            "request.count.min_value": {
              "max": 10,
              "metric": "request.count",
              "steps": 3,
              "description": "Number of handled requests is lower than",
              "min": 0
            }
          },
          "active": true,
          "id": 2,
          "name": "geonode is not working"
        }
      },
      "success": true
    }

Returned keys in `data` element:

* `fields` - list of form fields, including detailed per-resource configuration flags
* `form` - rendered user form, which can be displayed
* `notification` - serialized notification object with `user_thresholds` list (this is a base to create `fields` objects)

Frontend should use `fields` list to create whole form in client-side:

* field name is stored in `field_name`.
* field label can be constructed from `description`
* unit can be extracted from `unit` field
* if field definition provides list in `steps_calculated`, this should be used to construct selection/dropdown, otherwise text input should be displayed. If possible, validation should take into account `min_value` and `max_value`.
* currently set value is available in `current_value` field.
* each field has `is_enabled` property, which tells if field is enabled. Currently this value is calculated in following way: field is enabled if `current_value` is not `None`. This may change in the future.

Additionally, each notification configuration accepts list of emails in `emails` field. This field should be send as a list of emails joined with new line char (`\n`).

Form should be submitted to the same url as configuration source (``/monitoring/api/notifications/config/{id}/``), see below.

Notification edition (by user)
------------------------------

Following API call allows user to configure notification by setting receivers and adjust threshold values for checks:

``POST /monitoring/api/notifications/config/{{notification_check_id}}/``

.. code-block:: python

    request.count.max_value=val
    request.count.min_value=1
    emails=list of emails

Response contains serialized `NotificationCheck` in `data` element, if no errors were captured during form processing:

.. code-block:: json

    {
      "status": "ok",
      "errors": {},
      "data": {
        "grace_period": {
          "seconds": 600,
          "class": "datetime.timedelta"
        },
        "last_send": null,
        "description": "more test",
        "severity": "error",
        "user_threshold": {
          "request.count.max_value": {
            "max": null,
            "metric": "request.count",
            "steps": null,
            "description": "Max number of request",
            "min": 1000
          },
          "request.count.min_value": {
            "max": 100,
            "metric": "request.count",
            "steps": null,
            "description": "Min number of request",
            "min": 0
          }
        },
        "id": 293,
        "name": "test"
      },
      "success": true
    }

Error (non-200) response will have `errors` key populated:

.. code-block:: json

    {
      "status": "error",
      "errors": {
        "user_threshold": [
          "This field is required."
        ],
        "name": [
          "This field is required."
        ],
        "description": [
          "This field is required."
        ]
      },
      "data": [],
      "success": false
    }

Notification creation
---------------------

This API call allows to create new notification, it's different in form layout from edition:

``POST /monitoring/api/notifications/``

.. code-block:: python

    name=Name of notification (geonode doesn't work)
    description=This will check if geonode is serving any data
    emails=
    user_thresholds=
    severity=

Payload elements:

* `name`, `description` are values visible for user
* `severity` severity value
* `emails` is a list of emails, however, it is encoded to a string, where each email is in new line:

  .. code-block:: python

      email1@test.com
      email2@test.com

* `user_thresholds` is a json encoded list of per-metric-per-check configurations. Each element of list should be a 10-elemnt list, containing:

  * name of metric
  * field check option (one of three values: `min_value`, `max_value` or `max_timeout`)
  * flag, if metric check can use service
  * flag, if metric check can use resource
  * flag, if metric check can use label
  * flag, if metric check can use ows service
  * minimum value for user input (no minimum check if None)
  * maximum value for user input (no maximum check if None)
  * steps count is a number of steps to generate for user input, so user can select value from select list instead of typing. This will have effect only if both min and max values are also provided
    Sample payload for `user_thresholds`:

    .. code-block:: python

        [
            ('request.count', 'min_value', False, False, False, False, 0, 100, None, "Min number of request"),
            ('request.count', 'max_value', False, False, False, False, 1000, None, None, "Max number of request"),
        ]

Response is a serialized `NotificationCheck` wrapped with standard response envelope (status, errors etc).
Actual data is in `data` key. If processing failed, for example because of form validation errors, response will be non-200 OK, and `errors` key will be populated.

.. code-block:: json

    {
      "status": "ok",
      "errors": {},
      "data": {
        "grace_period": {
          "seconds": 600,
          "class": "datetime.timedelta"
        },
        "last_send": null,
        "description": "more test",
        "user_threshold": {
          "request.count.max_value": {
            "max": 100,
            "metric": "request.count",
            "steps": null,
            "description": "Min number of request",
            "min": 0
          },
          "request.count.min_value": {
            "max": null,
            "metric": "request.count",
            "steps": null,
            "description": "Max number of request",
            "min": 1000
          }
        },
        "id": 257,
        "name": "test"
      },
      "success": true
    }
