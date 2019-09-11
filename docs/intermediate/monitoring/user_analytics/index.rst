Monitoring: User Analytics
==========================

Purpose
-------

UA should provide information about GeoNode resources usage at user level (not request level, like plain monitoring).

Requests
--------

1. total number of unique sessions on GeoNode (excluding ows requests) per day. This gives a base view of the reach.

    * requests from all sessions of all types, ows and non-ows

      ``GET /monitoring/api/metric_data/request.users/?last=(x*86400)&interval=86400&group_by=label``

    * non-ows related

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=(x*86400)&interval=86400&group_by=label&event_type=other``

    * only ows related

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=(x*86400)&interval=86400&group_by=label&event_type=OWS:ALL``

      .. code-block:: json

          {
            "data": {
              "input_valid_from": "2018-07-11T15:41:06.419Z",
              "input_valid_to": "2018-07-12T15:41:06.419Z",
              "data": [
                {
                  "valid_from": "2018-07-11T15:41:06.419Z",
                  "data": [
                    {
                      "samples_count": 82,
                      "val": 9,
                      "min": "0.0000",
                      "max": "24.0000",
                      "sum": "82.0000",
                      "metric_count": 16
                    }
                  ],
                  "valid_to": "2018-07-12T15:41:06.419Z"
                }
              ],
              "metric": "request.users",
              "interval": 86400.0,
              "type": "value",
              "axis_label": "Count",
              "label": null
            }
          }

2. total number of unique sessions per URL (excluding ows requests). Let me see how many users visits the layers page or the maps page

    * get number of unique tracking ids for urls

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=(x*86400)&interval=86400&group_by=resource_on_label&resource_type=url&event_type=other``

      .. code-block:: json

          {
            "data": {
              "input_valid_from": "2018-07-11T15:39:25.126Z",
              "input_valid_to": "2018-07-12T15:39:25.126Z",
              "data": [
                {
                  "valid_from": "2018-07-11T15:39:25.126Z",
                  "data": [
                    {
                      "resource": {
                        "type": "url",
                        "name": "/layers/",
                        "id": 15
                      },
                      "metric_count": 2,
                      "val": 2,
                      "min": "1.0000",
                      "max": "1.0000",
                      "sum": "2.0000",
                      "samples_count": 2
                    },
                    {
                      "resource": {
                        "type": "url",
                        "name": "/",
                        "id": 16
                      },
                      "metric_count": 2,
                      "val": 2,
                      "min": "1.0000",
                      "max": "1.0000",
                      "sum": "2.0000",
                      "samples_count": 2
                    },
                    {
                      "resource": {
                        "type": "url",
                        "name": "/documents/",
                        "id": 21
                      },
                      "metric_count": 1,
                      "val": 1,
                      "min": "1.0000",
                      "max": "1.0000",
                      "sum": "1.0000",
                      "samples_count": 1
                    }
                  ],
                  "valid_to": "2018-07-12T15:39:25.126Z"
                }
              ],
              "metric": "request.users",
              "interval": 86400.0,
              "type": "value",
              "axis_label": "Count",
              "label": null
            }
          }

3. total number of unique sessions per event_type: for example total number of unique visits of resource pages (indipendently by resource type and id)

    * to get number of requests

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=86400&interval=86400&group_by=event_type``

    * to get number of unique tracking ids

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=86400&interval=86400&group_by=event_type_on_label``

    * to get number of unique tracking ids for each event_type on a given resource type

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=86400&interval=86400&group_by=event_type_on_label&resource_type=url``

      .. code-block:: json

        {
          "data": {
            "input_valid_from": "2018-07-11T17:54:41.467Z",
            "input_valid_to": "2018-07-12T17:54:41.467Z",
            "data": [
              {
                "valid_from": "2018-07-11T17:54:41.467Z",
                "data": [
                  {
                    "samples_count": 5,
                    "event_type": "all",
                    "val": 2,
                    "min": "1.0000",
                    "max": "1.0000",
                    "sum": "5.0000",
                    "metric_count": 5
                  },
                  {
                    "samples_count": 5,
                    "event_type": "other",
                    "val": 2,
                    "min": "1.0000",
                    "max": "1.0000",
                    "sum": "5.0000",
                    "metric_count": 5
                  },
                  {
                    "samples_count": 5,
                    "event_type": "view",
                    "val": 2,
                    "min": "1.0000",
                    "max": "1.0000",
                    "sum": "5.0000",
                    "metric_count": 5
                  }
                ],
                "valid_to": "2018-07-12T17:54:41.467Z"
              }
            ],
            "metric": "request.users",
            "interval": 86400.0,
            "type": "value",
            "axis_label": "Count",
            "label": null
          }
        }

    * to get number of unique users for each event type on specific resource type

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=86400&interval=86400&group_by=event_type_on_user&resource_type=url``

      .. code-block:: json

        {
          "data": {
            "input_valid_from": "2018-07-11T17:54:41.467Z",
            "input_valid_to": "2018-07-12T17:54:41.467Z",
            "data": [
              {
                "valid_from": "2018-07-11T17:54:41.467Z",
                "data": [
                  {
                    "samples_count": 5,
                    "event_type": "all",
                    "val": 2,
                    "min": "1.0000",
                    "max": "1.0000",
                    "sum": "5.0000",
                    "metric_count": 5
                  },
                  {
                    "samples_count": 5,
                    "event_type": "other",
                    "val": 1,
                    "min": "1.0000",
                    "max": "1.0000",
                    "sum": "5.0000",
                    "metric_count": 5
                  },
                  {
                    "samples_count": 5,
                    "event_type": "view",
                    "val": 1,
                    "min": "1.0000",
                    "max": "1.0000",
                    "sum": "5.0000",
                    "metric_count": 5
                  }
                ],
                "valid_to": "2018-07-12T17:54:41.467Z"
              }
            ],
            "metric": "request.users",
            "interval": 86400.0,
            "type": "value",
            "axis_label": "Count",
            "label": null
          }
        }

4. total number of unique sessions per event_type and single resource: let me see what was the most visited map page in this day, or what was the most downloaded document, what was the most requested ows layer, etc.

    * list of most visited resources of `url` type

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=86400&interval=86400&group_by=resource_on_label&resource_type=url``

    * list of unique tracking ids for each resource (can be narrowed down to specific resource type with `resource_type` values).

      ``GET /monitoring/api/metric_data/request.users/?``
      ``last=86400&interval=86400&group_by=resource_on_label``

      .. code-block:: json

          {
            "data": {
              "input_valid_from": "2018-07-11T17:56:49.381Z",
              "input_valid_to": "2018-07-12T17:56:49.381Z",
              "data": [
                {
                  "valid_from": "2018-07-11T17:56:49.381Z",
                  "data": [
                    {
                      "resource": {
                        "type": "",
                        "name": "",
                        "id": 1
                      },
                      "metric_count": 16,
                      "val": 9,
                      "min": "0.0000",
                      "max": "24.0000",
                      "sum": "82.0000",
                      "samples_count": 82
                    },
                    {
                      "resource": {
                        "type": "layer",
                        "name": "geonode:ne_50m_admin_0_countries_lakes",
                        "id": 2
                      },
                      "metric_count": 4,
                      "val": 3,
                      "min": "0.0000",
                      "max": "2.0000",
                      "sum": "3.0000",
                      "samples_count": 3
                    },
                    {
                      "resource": {
                        "type": "layer",
                        "name": "geonode:world_iso2",
                        "id": 12
                      },
                      "metric_count": 4,
                      "val": 2,
                      "min": "0.0000",
                      "max": "5.0000",
                      "sum": "8.0000",
                      "samples_count": 8
                    },
                    {
                      "resource": {
                        "type": "url",
                        "name": "/layers/",
                        "id": 15
                      },
                      "metric_count": 2,
                      "val": 2,
                      "min": "1.0000",
                      "max": "1.0000",
                      "sum": "2.0000",
                      "samples_count": 2
                    },
                    {
                      "resource": {
                        "type": "url",
                        "name": "/",
                        "id": 16
                      },
                      "metric_count": 2,
                      "val": 2,
                      "min": "1.0000",
                      "max": "1.0000",
                      "sum": "2.0000",
                      "samples_count": 2
                    },
                    {
                      "resource": {
                        "type": "url",
                        "name": "/documents/",
                        "id": 21
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
                        "type": "document",
                        "name": "GeoServer Configuration.pdf",
                        "id": 22
                      },
                      "metric_count": 1,
                      "val": 1,
                      "min": "5.0000",
                      "max": "5.0000",
                      "sum": "5.0000",
                      "samples_count": 5
                    }
                  ],
                  "valid_to": "2018-07-12T17:56:49.381Z"
                }
              ],
              "metric": "request.users",
              "interval": 86400.0,
              "type": "value",
              "axis_label": "Count",
              "label": null
            }
          }

5. total number of unique visitor (user) per event_type and single resource: let me see how many users visited the map page in this day, or how many users download some resource, etc.

  * number of unique visitors (users) in a year for a given event_type:

    ``GET /monitoring/api/metric_data/request.users/``
    ``?valid_from=2019-01-01+00:00:00&valid_to=2019-12-31+23:59:59``
    ``&interval=31536000&event_type=upload&group_by=user``

  * number of unique visitors (users) in a given time interval and for a given resource_type.

    ``GET /monitoring/api/metric_data/request.users/``
    ``?valid_from=2019-01-01+00:00:00&valid_to=2019-12-31+23:59:59``
    ``&interval=31536000&resource_type=layer&group_by=user``

  the responses should look like this:

  .. code-block:: json

      {
        "data": {
          "input_valid_from": "2019-01-01T00:00:00Z",
          "input_valid_to": "2019-12-31T23:59:59Z",
          "data": [
            {
              "valid_from": "2019-01-01T00:00:00Z",
              "data": [
                {
                  "samples_count": 3,
                  "val": 2,
                  "min": "1.0000",
                  "max": "2.0000",
                  "sum": "3.0000",
                  "metric_count": 2
                }
              ],
              "valid_to": "2020-01-01T00:00:00Z"
            }
          ],
          "metric": "request.users",
          "interval": 31536000,
          "type": "value",
          "axis_label": "Count",
          "label": null
        }
      }

6. total number of unique tracking ids/sessions for a given user.

  * sessions count for anonymous users:

    ``GET /monitoring/api/metric_data/request.users/``
    ``?valid_from=2019-01-01+00:00:00&valid_to=2019-12-31+23:59:59``
    ``&interval=31536000&group_by=label&user=AnonymousUser``

    .. code-block:: json

      {
        "data": {
          "input_valid_from": "2019-01-01T00:00:00Z",
          "input_valid_to": "2019-12-31T23:59:59Z",
          "data": [
            {
              "valid_from": "2019-01-01T00:00:00Z",
              "data": [
                {
                  "samples_count": 5,
                  "val": 5,
                  "min": "1.0000",
                  "max": "1.0000",
                  "sum": "5.0000",
                  "metric_count": 5
                }
              ],
              "valid_to": "2020-01-01T00:00:00Z"
            }
          ],
          "metric": "request.users",
          "interval": 31536000,
          "type": "value",
          "axis_label": "Count",
          "label": null
        }
      }

7. total number of unique tracking ids/sessions for each user.

  * sessions count for each users:

    ``GET /monitoring/api/metric_data/request.users/``
    ``?valid_from=2019-01-01+00:00:00&valid_to=2019-12-31+23:59:59``
    ``&interval=31536000&group_by=user_on_label``

    .. code-block:: json

      {
        "data": {
          "input_valid_from": "2019-01-01T00:00:00Z",
          "input_valid_to": "2019-12-31T23:59:59Z",
          "data": [
            {
              "valid_from": "2019-01-01T00:00:00Z",
              "data": [
                {
                  "samples_count": 5,
                  "val": 5,
                  "min": "1.0000",
                  "max": "1.0000",
                  "sum": "5.0000",
                  "user": "AnonymousUser",
                  "metric_count": 5
                },
                {
                  "samples_count": 16,
                  "val": 3,
                  "min": "1.0000",
                  "max": "2.0000",
                  "sum": "16.0000",
                  "user": "admin",
                  "metric_count": 14
                },
                {
                  "samples_count": 4,
                  "val": 1,
                  "min": "1.0000",
                  "max": "1.0000",
                  "sum": "4.0000",
                  "user": "user1_username",
                  "metric_count": 4
                }
              ],
              "valid_to": "2020-01-01T00:00:00Z"
            }
          ],
          "metric": "request.users",
          "interval": 31536000,
          "type": "value",
          "axis_label": "Count",
          "label": null
        }
      }

  * sessions count for each users which do something with a layer:

    ``GET /monitoring/api/metric_data/request.users/``
    ``?valid_from=2019-01-01+00:00:00&valid_to=2019-12-31+23:59:59``
    ``&interval=31536000&resource_type=layer&group_by=user_on_label``

    .. code-block:: json

      {
        "data": {
          "input_valid_from": "2019-01-01T00:00:00Z",
          "input_valid_to": "2019-12-31T23:59:59Z",
          "data": [
            {
              "valid_from": "2019-01-01T00:00:00Z",
              "data": [
                {
                  "samples_count": 2,
                  "val": 1,
                  "min": "2.0000",
                  "max": "2.0000",
                  "sum": "2.0000",
                  "user": "admin",
                  "metric_count": 1
                },
                {
                  "samples_count": 1,
                  "val": 1,
                  "min": "1.0000",
                  "max": "1.0000",
                  "sum": "1.0000",
                  "user": "user1_username",
                  "metric_count": 1
                }
              ],
              "valid_to": "2020-01-01T00:00:00Z"
            }
          ],
          "metric": "request.users",
          "interval": 31536000,
          "type": "value",
          "axis_label": "Count",
          "label": null
        }
      }

8. total number of unique users for each monitored resource.

  ``GET /monitoring/api/metric_data/request.users/``
  ``?last=31536000&interval=31536000&group_by=resource_on_user``

  .. code-block:: json

    {
      "data": {
        "input_valid_from": "2018-09-10T14:15:39.454Z",
        "input_valid_to": "2019-09-10T14:15:39.454Z",
        "data": [
          {
            "valid_from": "2018-09-10T14:15:39.454Z",
            "data": [
              {
                "resource": {
                  "href": "/",
                  "type": "url",
                  "name": "/",
                  "id": 1
                },
                "metric_count": 36,
                "val": 4,
                "max": "2.0000",
                "sum": "35.0000",
                "min": "0.0000",
                "samples_count": 35
              },
              {
                "resource": {
                  "href": "/maps/",
                  "type": "url",
                  "name": "/maps/",
                  "id": 3
                },
                "metric_count": 3,
                "val": 2,
                "max": "1.0000",
                "sum": "3.0000",
                "min": "1.0000",
                "samples_count": 3
              },
              {
                "resource": {
                  "href": "",
                  "type": "layer",
                  "name": "geonode:railways",
                  "id": 4
                },
                "metric_count": 5,
                "val": 2,
                "max": "2.0000",
                "sum": "3.0000",
                "min": "0.0000",
                "samples_count": 3
              },
              {
                "resource": {
                  "href": "/layers/",
                  "type": "url",
                  "name": "/layers/",
                  "id": 2
                },
                "metric_count": 4,
                "val": 1,
                "max": "1.0000",
                "sum": "4.0000",
                "min": "1.0000",
                "samples_count": 4
              },
              {
                "resource": {
                  "href": "/documents/2",
                  "type": "document",
                  "name": "test_doc_1.txt",
                  "id": 5
                },
                "metric_count": 2,
                "val": 1,
                "max": "2.0000",
                "sum": "4.0000",
                "min": "2.0000",
                "samples_count": 4
              },
              {
                "resource": {
                  "href": "/maps/3",
                  "type": "map",
                  "name": "test_map",
                  "id": 6
                },
                "metric_count": 1,
                "val": 1,
                "max": "1.0000",
                "sum": "1.0000",
                "min": "1.0000",
                "samples_count": 1
              },
              {
                "resource": {
                  "href": "",
                  "type": "layer",
                  "name": "geonode:waterways",
                  "id": 7
                },
                "metric_count": 2,
                "val": 1,
                "max": "2.0000",
                "sum": "2.0000",
                "min": "0.0000",
                "samples_count": 2
              }
            ],
            "valid_to": "2019-09-10T14:15:39.454Z"
          }
        ],
        "metric": "request.users",
        "interval": 31536000,
        "type": "value",
        "axis_label": "Count",
        "label": null
      }
    }

9. total number of resource monitored in a given time range.

  ``GET /monitoring/api/metric_data/request.users/``
  ``?last=31536000&interval=31536000&group_by=count_on_resource``

  .. code-block:: json

    {
      "data": {
        "input_valid_from": "2018-09-10T14:20:27.335Z",
        "input_valid_to": "2019-09-10T14:20:27.335Z",
        "data": [
          {
            "valid_from": "2018-09-10T14:20:27.335Z",
            "data": [
              {
                "samples_count": 52,
                "val": 7,
                "min": "0.0000",
                "max": "2.0000",
                "sum": "52.0000",
                "metric_count": 53
              }
            ],
            "valid_to": "2019-09-10T14:20:27.335Z"
          }
        ],
        "metric": "request.users",
        "interval": 31536000,
        "type": "value",
        "axis_label": "Count",
        "label": null
      }
    }
