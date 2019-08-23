Monitoring: API
===============

Overview
--------

Geonode monitoring is an optional infrastructure for monitoring resource usage in GeoNode, accompanying GeoServer(s) and hosts on which each service is running. This is not full-fledge monitoring, like zabbix or nagios, rather a moderate size tool to diagnose deployment health.
It will be used by users that mostly are not full-time sysops, so usage is simplified.

API
---

Monitoring API exposes various data to monitoring client.

API root URL is ``/monitoring/``, each path in this documentation is relative to that root.

Valid from/valid to
~~~~~~~~~~~~~~~~~~~

Monitoring collects data periodically, in fixed periods (usually 1 minute).
Each metric data is a value (or values if they are split by additional indicators, like resource, label etc) accumulated within that period.

.. _host:

Host
~~~~

Host is a physical or virtualized instance, on which specific service (GeoNode or GeoServer) is running.
This entity is not monitored, but it's used to group services by their deployment location.
Hosts list is available in API in ``/api/hosts/`` endpoint:

``GET /monitoring/api/hosts/``

.. code-block:: json

    {
      "hosts": [
        {
          "ip": "127.0.0.1",
          "name": "localhost"
        }
      ]
    }

While host is not monitored directly, some service types (and services of those types) are responsible for monitoring underlying host,hardware resources are monitored indirectly (no dedicated system-level agent is needed).

Service
~~~~~~~

Service is a name of monitored service.
Services are configurable from admin interface, and exposed in API in ``/api/services/``:

``GET /monitoring/api/services/``

.. code-block:: json

    {
      "services": [
        {
          "name": "local-system",
          "last_check": "2017-08-03T13:33:26.674",
          "host": "localhost",
          "check_interval": 60,
          "type": "hostgeonode",
          "id": 3
        },
        {
          "name": "local-geoserver",
          "last_check": "2017-08-03T13:33:26.455",
          "host": "localhost",
          "check_interval": 60,
          "type": "geoserver",
          "id": 2
        },
        {
          "name": "local-geonode",
          "last_check": "2017-08-03T13:33:27.741",
          "host": "localhost",
          "check_interval": 60,
          "type": "geonode",
          "id": 1
        }
      ]
    }

Each service is described by properties:

* `name` - unique name of service
* `type` - service type name
* `host` - host on which service is running
* `id` - object id
* `last_check` - timestamp with last check (data collection) on that service
* `check_interval` - interval in seconds, how often data should be collected from this service.

Service type
~~~~~~~~~~~~

Service type describes kind of services to which it's assigned. There are several service types available:

* `geonode` - service is a GeoNode instance
* `geoserver` - service is a GeoServer instance
* `hostgeonode` - service is not an application, service is underlying host measured with GeoNode (see :ref:`host`)
* `hostserver` - service is not an application, service is underlying host measured with GeoServer (see :ref:`host`)

Resource
~~~~~~~~

Resource is an object that can be served by GeoNode or GeoServer. There are several resource types monitored:

* layer
* document
* map
* url

Resource can be served from either GeoNode or GeoServer.
We don't check if specific resource actually exists, just keep list of items used and recorded for monitoring.
Also, it won't show renames/copies/moves of the same resource.

Resources list is available in ``/api/resources/`` endpoint:

``GET /monitoring/api/resources/``

.. code-block:: json

    {
      "resources": [
        {
          "type": "layer",
          "id": 13,
          "name": "unesco:Unesco_point"
        },
        {
          "type": "layer",
          "id": 7,
          "name": "geonode:test"
        },
        {
          "type": "layer",
          "id": 14,
          "name": "http://www.opengis.net/gml:GridCoverage"
        },
        {
          "type": "map",
          "id": 17,
          "name": "some map"
        },
        ]
    }

Resource is described with following attributes:

* `id` - numeric id of resource record in monitoring
* `type` - type of resource
* `name` - name of resource.

Resources list can be filtered with following query sting arguments:

* `metric_name` - name of metric for which resources should be returned
* `resource_type` - name of type of resource (`layer`, `map`, `document`, `style`, `url`)
* `valid_from` - list resources that are available since that timestamp
* `valid_to` - list resources that are available until that timestamp

Example:

``GET /monitoring/api/resources/?resource_type=layer&metric_name=request.count&valid_from=2017-08-01``

.. code-block:: json

    {
      "resources": [
        {
          "type": "layer",
          "id": 24,
          "name": "atlantis:landmarks"
        },
        {
          "type": "layer",
          "id": 2,
          "name": "topp:states"
        },
        {
          "type": "layer",
          "id": 22,
          "name": "atlantis:island"
        },
        {
          "type": "layer",
          "id": 23,
          "name": "atlantis:poi"
        },
        {
          "type": "layer",
          "id": 16,
          "name": "dissolveroad2"
        },
        {
          "type": "layer",
          "id": 21,
          "name": "atlantis:roads"
        }
      ]
    }

Resource type
~~~~~~~~~~~~~

Resource Types describe which types of resource the GeoNode monitoring consider.
To retrieve the full list of Resource Types the ``/api/resource_types/`` is available:

``GET /monitoring/api/resource_types/``

.. code-block:: json

    {
      "status": "ok",
      "data": {
        "key": "resource_types"
      },
      "errors": {},
      "resource_types": [
        {
          "type": "No resource",
          "name": ""
        },
        {
          "type": "Layer",
          "name": "layer"
        },
        {
          "type": "Map",
          "name": "map"
        },
        {
          "type": "Resource base",
          "name": "resource_base"
        },
        {
          "type": "Document",
          "name": "document"
        },
        {
          "type": "Style",
          "name": "style"
        },
        {
          "type": "Admin",
          "name": "admin"
        },
        {
          "type": "URL",
          "name": "url"
        },
        {
          "type": "Other",
          "name": "other"
        }
      ],
      "success": true
    }

Event Types
~~~~~~~~~~~

Event Types describe the way resources were used in GeoNode.
Resource can be accessed as a regular view (throuhg GeoNode, like `/layers/X` url), or through OWS request.
Full list of Event Types handled is available in ``/api/event_types/`` endpoint:

``GET /monitoring/api/event_types/``

.. code-block:: json

    {
        "status": "ok",
        "errors": { },
        "data": {
            "key": "event_types"
            },
        "event_types": [
            {
                "name": "all"
                },
            {
                "name": "other"
                },
            {
                "name": "download"
                },
            {
                "name": "view"
                },
            {
                "name": "OWS:TMS"
                },
            {
                "name": "OWS:WMS-C"
                },
            {
                "name": "OWS:WMTS"
                },
            {
                "name": "OWS:WCS"
                },
            {
                "name": "OWS:WFS"
                },
            {
                "name": "OWS:WMS"
                },
            {
                "name": "OWS:WPS"
                },
            {
                "name": "OWS:ALL"
                },
            {
                "name": "create"
                },
            {
                "name": "upload"
                },
            {
                "name": "change"
                },
            {
                "name": "change_metadata"
                },
            {
                "name": "view_metadata"
                },
            {
                "name": "publish"
                },
            {
                "name": "remove"
                }
            ],
        "success": true
    }

Event types starting with `OWS:` prefix mean they're related to OWS service.
`OWS:ALL` is a cumulative event type, which keeps requests for any OWS.

Event type `other` means request not related to OWS.
This is also cumulative event type, and should be used as a baseline of all non-ows requests.

Event type `all` means any request.

Label
~~~~~

Label is a description of subset of metric data that is not described by resources (it's not served as logical data set).
Things that can be described with label:

* user tracking id
* volume mount point
* network interface name
* request path
* request method
* response status code
* etc ...

 List of all labels recorded is available in ``/api/labels/`` endpoint:

``GET /monitoring/api/labels/``

.. code-block:: json

    {
      "labels": [
        {
          "id": 306,
          "name": "Other / Other / Python Requests 2.13"
        },
        {
          "id": 315,
          "name": "Kent"
        },
        {
          "id": 298,
          "name": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
        },
        {
          "id": 261,
          "name": "lo"
        },
        {
          "id": 331,
          "name": "PUT"
        },
        {
          "id": 334,
          "name": "Other / Other / Python Requests 2.18"
        }
        ]
    }

Each metric data set will have at least one label attached. List of labels can be filtered with following query sting arguments:

* `metric_name` - name of metric for which labels should be returned
* `valid_from` - list labels that are available since that timestamp
* `valid_to` - list labels that are available until that timestamp

Example:

``GET /monitoring/api/labels/?metric_name=request.ua&valid_from=2017-08-05``

.. code-block:: json

    {
      "labels": [
        {
          "id": 298,
          "name": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
        },
        {
          "id": 312,
          "name": "Java/1.8.0_131"
        },
        {
          "id": 293,
          "name": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36"
        },
        {
          "id": 345,
          "name": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/538.1 (KHTML, like Gecko) PhantomJS/2.1.1 Safari/538.1"
        },
        ...
       ]
    }

Metric name
~~~~~~~~~~~

Metric name is a semi-namespace description of what kind of data metric stores.
Typical metric names:
- `request.count`
- `request.ip`
- `response.size`
- `response.status`

Each service type has a set of metrics available.
Application-level services will have different metric set than host-level services.

Full list of metrics is available in ``/api/metrics/`` endpoint. Returned list is not filterable.
Sample response:

``GET /monitoring/api/metrics/``

.. code-block:: json

    {
      "metrics": [
        {
          "metrics": [
            {
              "type": "count",
              "name": "request.count",
              "unit": "Count"
            },
            {
              "type": "count",
              "name": "request.ip",
              "unit": "Count"
            },
            ...
          ],
          "service": "geonode"
        },
        { "service": "geoserver",
          "metrics": [..]
        }
        ]
    }

Metrics are grouped by service. Each metric has following structure:

.. code-block:: json

    {
        "type": "count",
        "name": "request.ip",
        "unit": "Count"
    }

where:

* `type` is a metric data type (it can be count, value or rate). This is internal description of how to deal with aggregation of data for metric.
* `name` name of metric
* `unit` suggested Y-axis label, describing data units

Metric Data
~~~~~~~~~~~

Core feature of monitoring API is ability to get data for given metric for specified period.
Metric value is a data set for fixed period of time, from which data were collected and processed for one specific metric name.
Additionally, each metric can have data calculated for specific services, resources, labels and event_types.
Metric data API has several features:

* it can show metric data within specific time frame, down to 1 minute granularity (may be less if collection intervals are lower).
* it can show metric data aggregated with custom granularity (for example from last 48 hours with 15 minutes granularity).
* it can show metric data for whole monitored setup or for specific resource, label (like user agent type), monitored service (just for geonode or just for geoserver), Event type. Params can be joined in one query.

API endpoint is: ``/api/metric_data/METRIC_NAME/``:

Sample request for `request.ua` metric in specific time window (between 10am and 2pm of 2017-08-03) and data granularity (1h)

| ``GET /monitoring/api/metric_data/request.ua/?``
| ``valid_from=2017-08-03%2010:00:00&valid_to=2017-08-03%2014:00:00&interval=3600``

.. code-block:: json

    {
      "data": {
        "input_valid_from": "2017-08-03T10:00:00",
        "input_valid_to": "2017-08-03T14:00:00",
        "data": [
          {
            "valid_from": "2017-08-03T10:00:00",
            "data": [],
            "valid_to": "2017-08-03T11:00:00"
          },
          {
            "valid_from": "2017-08-03T11:00:00",
            "data": [
              {
                "samples_count": 10,
                "val": "10.0000",
                "min": "1.0000",
                "max": "1.0000",
                "sum": "10.0000",
                "label": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0",
                "metric_count": 10
              },
              {
                "samples_count": 790,
                "val": "790.0000",
                "min": "19.0000",
                "max": "79.0000",
                "sum": "790.0000",
                "label": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
                "metric_count": 22
              },
              {
                "samples_count": 150,
                "val": "150.0000",
                "min": "15.0000",
                "max": "15.0000",
                "sum": "150.0000",
                "label": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/538.1 (KHTML, like Gecko) PhantomJS/2.1.1 Safari/538.1",
                "metric_count": 10
              }
            ],
            "valid_to": "2017-08-03T12:00:00"
          },
          {
            "valid_from": "2017-08-03T12:00:00",
            "data": [],
            "valid_to": "2017-08-03T13:00:00"
          },
          {
            "valid_from": "2017-08-03T13:00:00",
            "data": [
              {
                "samples_count": 37,
                "val": "37.0000",
                "min": "4.0000",
                "max": "12.0000",
                "sum": "37.0000",
                "label": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.40 Safari/537.36",
                "metric_count": 4
              }
            ],
            "valid_to": "2017-08-03T14:00:00"
          }
        ],
        "metric": "request.ua",
        "interval": 3600,
        "type": "count",
        "axis_label": "Count",
        "label": null
      }
    }

Metric data response is wrapped with following envelope:

.. code-block:: json

        "data": {
            "input_valid_from": "2017-08-03T10:00:00",
            "input_valid_to": "2017-08-03T14:00:00",
            "metric": "request.ua",
            "interval": 3600,
            "type": "count",
            "axis_label": "Count",
            "label": null,
            "data": [
            ... # actual data
            ],
        }
    }

where:

* `input_valid_from` and `input_valid_to` are parsed and aligned timestamps for which data are returned,
* `metric` is metric name for which response is returned,
* `interval` data aggregation interval used, in seconds (if none is provided, 60 seconds are used, unless time window is larger than 24 hours),
* `type` is metric data type, which describes internally how data are aggregated (sum, average or min/max function).
* `axis_label` is suggested value-axis label to be used in chart
* `label` is metric data label used (no label by default).

Metric data item is build as following structure:

.. code-block:: json

    {
        "valid_from": "2017-08-03T13:00:00",
        "valid_to": "2017-08-03T14:00:00",
        "data": [
        {
            "samples_count": 37,
            "val": "37.0000",
            "min": "4.0000",
            "max": "12.0000",
            "sum": "37.0000",
            "label": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.40 Safari/537.36",
            "metric_count": 4
        },
        {
            "samples_count": 20,
            "val": "20.0000",
            "min": "4.0000",
            "max": "10.0000",
            "sum": "20.0000",
            "label": "Internet Explorer 4.0",
            "metric_count": 3
        },
        ],

    }

where:

* `valid_from` and `valid_to` are timestamps of data aggregation period
* `data` is a list of value rows. When `data` is empty, that means no data were collected for input params.
* each `data` element contains:

    - `label` label value associated with metric data value. This can describe user-provided differentiation value (user agent string, request method etc), or, if such value is not in use, default, "count" or "value" label.
    - `val` is metrid data aggregated value, which should be used by frontend application. For `request.ua` this means count of requests for given user agent string, for `response.time` that will return average response time.
    - `min`, `max`, `sum` are helper statistical values to give insight on data used,
    - `samples_count` is a sum of all samples counts (actual requests) used for this calculation
    - `metric_count` is a number of metric data used to calculate the value.
    - `resource` (optional) key with resource structure (`id`, `name`, `type`). This element will be visible when grouping by resource is used.
    - `event_type` (optional) key with name of event type related to rest of row. This element will be visible when grouping by event type is used

Metric data can be filtered with following params:

* `valid_from` timestamp (date or date + time) meaning that data should be newer than this timestamp
* `valid_to` timestamp (date or date + time) meaning that data should be older than this timestamp
* `interval` data aggregation interval, in seconds. See below notes about intervals and timestamps alignment
* `label` label value only for which data should be returned (see [Labels](#labels))
* `resource` id of resource (see [Resources](#resources)) for which data should be returned
* `service` name of service (see [Services](#services)) for which data should be returned
* `event_type` name of service (see [Event Types](#ows_service)) for which data should be returned
* `resource_type` name of resource type to filter by, for example `layer` to show only data for layer objects (exclude urls, documents, maps).

grouping metric data
~~~~~~~~~~~~~~~~~~~~

Additionally, in some cases client application may want to receive list of data points in one period for several resources (typical usage scenario: list top-most requested layers).
In such case, metric data should be queried also with following params:

* `group_by` - name of object which should be used for grouping. At the moment two grouping modes are available:

    - `resource` - group by resource affected. This will produce metrics for the same label but each resource affected will be listed separately. Returned metric data items will have additional `resource` key, which will hold dictionary with keys `name` and `type`. Sample response:

      ``GET /monitoring/api/metric_data/request.count/?last=86400&interval=86400&group_by=resource``

      .. code-block:: json

          {
            "data": {
              "input_valid_from": "2017-09-01T00:00:00",
              "input_valid_to": "2017-09-08T13:50:34.024",
              "data": [
                ..
                {
                  "valid_from": "2017-09-04T00:00:00",
                  "data": [
                    {
                      "resource": {
                        "type": "layer",
                        "name": "nurc:Arc_Sample"
                      },
                      "samples_count": 300,
                      "val": "300.0000",
                      "min": "100.0000",
                      "max": "100.0000",
                      "sum": "300.0000",
                      "label": "count",
                      "metric_count": 3,
                      "id": 10
                    },
                    {
                      "resource": {
                        "type": "layer",
                        "name": "sde:HYP_HR_SR_OB_DR"
                      },
                      "samples_count": 72,
                      "val": "72.0000",
                      "min": "24.0000",
                      "max": "24.0000",
                      "sum": "72.0000",
                      "label": "count",
                      "metric_count": 3,
                      "id": 25
                    }
                  ],
                  "valid_to": "2017-09-05T00:00:00"
                }
                  ],
                  "valid_to": "2017-09-09T00:00:00"
                }
              ],
              "metric": "request.count",
              "interval": 86400,
              "type": "count",
              "axis_label": "Count",
              "label": null
            }
          }

    - `resource_no_labels` - group by resource affected, but do not distinct by label. This will produce similar result as the other grouping, but it will not contain 'label' key.

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=86400&interval=86400&group_by=resource_no_label&event_type=view&resource_type=url``

      .. code-block:: json

          {
              "data": {
                  "input_valid_from": "2018-07-10T15:13:50.784Z",
                  "input_valid_to": "2018-07-11T15:13:50.784Z",
                  "data": [
                      {
                          "val"id_from: "2018-07-10T15:13:50.784Z",
                          "data": [
                      {
                          "resource": {
                              "type": "url",
                              "name": "/layers/",
                              "id": 15
                          },
                          "metric_count": 4,
                          "val": 2,
                          "min": "1.0000",
                          "max": "1.0000",
                          "sum": "4.0000",
                          "samples_count": 4
                      },
                      {
                          "resource": {
                              "type": "url",
                              "name": "/",
                              "id": 16
                          },
                          "metric_count": 4,
                          "val": 2,
                          "min": "1.0000",
                          "max": "4.0000",
                          "sum": "7.0000",
                          "samples_count": 7
                      },
                      {
                          "resource": {
                              "type": "url",
                              "name": "/maps/",
                              "id": 17
                          },
                          "metric_count": 4,
                          "val": 2,
                          "min": "1.0000",
                          "max": "2.0000",
                          "sum": "5.0000",
                          "samples_count": 5
                      },
                      {
                          "resource": {
                              "type": "url",
                              "name": "/maps/3",
                              "id": 18
                          },
                          "metric_count": 1,
                          "val": 1,
                          "min": "1.0000",
                          "max": "1.0000",
                          "sum": "1.0000",
                          "samples_count": 1
                      },
                      {
                          "resource": {
                              "type": "url",
                              "name": "/maps/7",
                              "id": 20
                          },
                          "metric_count": 1,
                          "val": 1,
                          "min": "1.0000",
                          "max": "1.0000",
                          "sum": "1.0000",
                          "samples_count": 1
                      }
                      ],
                      "valid_to": "2018-07-11T15:13:50.784Z"
                  }
                  ],
                  "metric": "request.users",
                  "interval": 86400,
                  "type": "value",
                  "axis_label": "Count",
                  "label": null
              }
          }

    - `label` - group by label. This will return number of unique label occurrences within selected period.

      ``GET /monitoring/api/metric_data/request.users/?last=86400&interval=86400&group_by=label``

      .. code-block:: json

          {
            "data": {
              "input_valid_from": "2018-07-10T16:29:08.982Z",
              "input_valid_to": "2018-07-11T16:29:08.982Z",
              "data": [
                {
                  "valid_from": "2018-07-10T16:29:08.982Z",
                  "data": [
                    {
                      "samples_count": 243,
                      "val": 13,
                      "min": "0.0000",
                      "max": "25.0000",
                      "sum": "243.0000",
                      "metric_count": 124
                    }
                  ],
                  "valid_to": "2018-07-11T16:29:08.982Z"
                }
              ],
              "metric": "request.users",
              "interval": 86400.0,
              "type": "value",
              "axis_label": "Count",
              "label": null
            }
          }

    - `event_type` - group by event type. This will expose `event_type` field in data items. Grouping will return number of requests per each event type.
    - `event_type_on_label` - group by event type but use label to do grouping (instead of metric data value). This will expose `event_type` field in data items. Grouping will return number of requests per label (especially for `request.users`, which uses label field as tracking id value, see [User Analytics](https://github.com/geosolutions-it/geonode/wiki/Monitoring:-User-Analytics)).

Timestamps alignment
~~~~~~~~~~~~~~~~~~~~

Data collected by monitoring are aggregated into fixed period values. This have several consequences:

* you cannot query for time window smaller than aggregation period
* when querying for time window, input valid_from and valid_to will be aligned to possible actual valid_from and valid_to values. Alignment is calculated from 0:00h each day. For best results, you should use intervals that can be aligned without reminders.
* timestamps alignment may produce more rows than you expect in some cases. For example, let's say client application want to have data aggregated with 5 minutes interval. Search for data between 12:04 and 12:06, even if interval between those two (2 minutes) is smaller than data interval (5 minutes), this will be aligned to data intervals, which will be:

    * from 12:00 to 12:05
    * from 12:05 to 12:10

 If data aggregation period ends in the future, there's good chance it will not contain any data.

Exceptions
~~~~~~~~~~

Exceptions are served with separate API endpoints. Those endpoints will return:

* list of exceptions captured
* exception details

List of exceptions is available in ``/api/exceptions/`` endpoint:

``GET /monitoring/api/exceptions/``

.. code-block:: json

    {
      "exceptions": [
        {
          "url": "/monitoring/api/exceptions/8/",
          "error_type": "exceptions.ValueError",
          "id": 8,
          "service": {
            "type": "geonode",
            "name": "local-geonode"
          },
          "created": "2017-06-20T17:50:24.922"
        },
        {
          "url": "/monitoring/api/exceptions/9/",
          "error_type": "org.geoserver.platform.ServiceException",
          "id": 9,
          "service": {
            "type": "geoserver",
            "name": "local-geoserver"
          },
          "created": "2017-06-26T15:33:20.152"
        },
        {
          "url": "/monitoring/api/exceptions/10/",
          "error_type": "django.db.utils.ProgrammingError",
          "id": 10,
          "service": {
            "type": "geonode",
            "name": "local-geonode"
          },
          "created": "2017-06-27T12:32:37.032"
        },
      ]
    }

Each exception in list contains:

* `error_type` which is a class of exception
* `id` object id for given exception recorded
* ` service` service object, on which exception was recorded
* `created` exception recorded timestamp
* `url` url with exception details

Exception details:

``GET /monitoring/api/exceptions/30/``

.. code-block:: json

    {
      "error_data": "Traceback (most recent call last):\n  File \"/home/cezio/.virtualenvs/geonode/lib/python2.7/site-packages/django/core/handlers/base.py\", line 132, in get_response\n    response = wrapped_callback(request, *callback_args, **callback_kwargs)\n  File \"/home/cezio/.virtualenvs/geonode/lib/python2.7/site-packages/django/views/generic/base.py\", line 71, in view\n    return self.dispatch(request, *args, **kwargs)\n  File \"/home/cezio/.virtualenvs/geonode/lib/python2.7/site-packages/django/views/generic/base.py\", line 89, in dispatch\n    return handler(request, *args, **kwargs)\n  File \"/mnt/work/cezio/geosolutions/repos/geonode/geonode/contrib/monitoring/views.py\", line 176, in get\n    return json_response({self.output_name: out})\n  File \"/mnt/work/cezio/geosolutions/repos/geonode/geonode/utils.py\", line 619, in json_response\n    body = json.dumps(body, cls=DjangoJSONEncoder)\n  File \"/usr/lib64/python2.7/json/__init__.py\", line 251, in dumps\n    sort_keys=sort_keys, **kw).encode(obj)\n  File \"/usr/lib64/python2.7/json/encoder.py\", line 207, in encode\n    chunks = self.iterencode(o, _one_shot=True)\n  File \"/usr/lib64/python2.7/json/encoder.py\", line 270, in iterencode\n    return _iterencode(o, 0)\n  File \"/home/cezio/.virtualenvs/geonode/lib/python2.7/site-packages/django/core/serializers/json.py\", line 115, in default\n    return super(DjangoJSONEncoder, self).default(o)\n  File \"/usr/lib64/python2.7/json/encoder.py\", line 184, in default\n    raise TypeError(repr(o) + \" is not JSON serializable\")\nTypeError: <Service: Service: local-geoserver@localhost> is not JSON serializable\n",
      "service": {
        "type": "geonode",
        "name": "local-geonode"
      },
      "created": "2017-07-24T13:29:28.321",
      "error_type": "exceptions.TypeError",
      "request": {
        "event_type": null,
        "client": {
          "ip": "127.0.0.1",
          "position": {
            "lat": null,
            "country": null,
            "lon": null,
            "city": null
          },
          "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.40 Safari/537.36",
          "user_agent_family": "PC / Linux / Chrome 60.0.3112"
        },
        "request": {
          "path": "/monitoring/api/exceptions/",
          "host": "localhost:8000",
          "method": "GET",
          "created": "2017-07-24T13:29:28.280"
        },
        "response": {
          "status": 200,
          "time": 30,
          "type": "text/html; charset=utf-8",
          "size": 0
        },
        "resources": []
      },
      "error_message": "exceptions.TypeError"
    }

Details contain:

* `error_type` which is a class of exception
* `error_message` message provided with error
* `error_data` is a plain text with stack trace
* `service` service object, on which exception was recorded
* `created` exception recorded timestamp
* `request` information on request associated with this error:

    * `event_type` name of Event Type associated with request
    * `client` requesting client information
    * `request` details on request received
    * `response` details on response send back
    * `resources` list of resources affected

Autoconfiguration
~~~~~~~~~~~~~~~~~

Autoconfiguration endpoint allows to perform monitoring configuration based on `settings` values.
This API endpoint is available to superusers/staff only. Response is wrapped with standard envelope.

``POST /monitoring/api/autoconfigure/``

.. code-block:: json

    {
        "status": "ok",
        "success": true,
        "errors": {}
    }
