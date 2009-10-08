Hazard Reporting Category Django App
====================================

The Category App annotates data layers in the GeoNode with risk information.
This information can be used to inform navigational tools such as the layer
list in the reporting :doc:`/reporting-application/frontend`.

Model
-----

The Category App manages three types of entity:

1. ``Hazard``: A type of hazard (such as storm surge or landslides). Each
   ``Hazard`` contains the following fields:
   
       ``name`` 
           the display name to use for the hazard grouping in user interface
           elements

   and is associated with multiple ``Period`` records and multiple
   ``RadiusInfo`` records.

2. ``Period``: A range of time over which data is aggregated.  Each ``Period``
   contains the following fields:
   
    ``typename``
        The single typename for the coverage layer containing the data for the 
        given hazard and period. This is currently a string (assumed to be
        hosted by the GeoServer that accompanies the GeoNode) but might be
        changed to reference some Layer type in the future.

    ``length``
        The duration of the period, measured in years.

   Each ``Period`` is related to a single ``Hazard`` record.

3. ``RadiusInfo``: A mapping from a range of scale denominator values to the
   real-world radius of the area across which data should be collected for the
   reporting application.  Each ``RadiusInfo`` contains the following fields:

    ``minscale``
        The minimum scale denominator (inclusive) of the range where this
        radius is applicable.

    ``maxscale``
        The maximum scale denominator (exclusive) of the range where this
        radius is applicable.

    ``radius``
        The radius in meters of the buffer to apply when gathering report data
        in the given scale range.

   Each ``RadiusInfo`` is related to a single ``Hazard`` record.

.. todo:: 

    Discuss Django hazard record layout with the client (Oscar) to ensure that
    it properly models the task at hand.


JavaScript Interaction
----------------------

In order to make the category and range data more accessible to
JavaScript applications, the Hazard categories will need to be
converted to a JSON encoding.  A typical JSON document would look
like::

    [{"hazard": "Zombie Attack",
      "radii": [
          {"min": 10000, "max": 100000, "radius": "300"},
          {"min": 1000, "max": 10000, "radius": "30"}
      ],
      "periods": [
          {"length": 100, "typename": "zombies:attack_100y"},
          {"length": 20, "typename": "zombies:attack_20y"}
      ]
    },{"hazard": "Candy Drought",
      "radii": [...],
      "periods": [...]
    }]

.. note:: 

    Since the configuration will be known at page load time, this can
    be simply injected into the page instead of providing a REST API.

Administration
--------------

For the current iteration, administration will be provided using the
excellent administration interface provided by Django.
