.. maps.style:

Styling layers
==============

.. todo:: Is there no way to style layers without making a map? This page should ideally go in the layers section.

In this interface, we can pause in our map creation and change the style of one of our uploaded layers. GeoNode allows you to edit layer styles graphically, without the need to resort to programming or requiring a technical background.

We'll be editing the :file:`san_andres_y_providencia_poi` layer.

#. In the layer list, uncheck all of the layers except the above, so that only this one is visible (not including the base layer).

   .. figure:: img/layersunchecked.png

      *Only one layer visible*

#. Zoom in closer using the toolbar or the mouse.

   .. figure:: img/zoomedin.png

      *Zoomed in to see the layer better*

#. In the layer list, click to select the remaining layer and then click the palette icon (:guilabel:`Layer Styles`). This will bring up the style manager.

   .. figure:: img/styles.png

      *Styles manager*

#. This layer has one style (named the same as the layer) and one rule in that style. Click the rule (:guilabel:`Untitled 1`) to select it, and then click on :guilabel:`Edit` below it.

   .. figure:: img/editrulelink.png

      *Edit style rule link*

#. Edit the style. You can choose from simple shapes, add labels, and even adjust the look of the points based on attribute values and scale.

   .. todo:: This section could definitely be expanded upon, and could even be a mini-workshop on creating nicely styled layers through the GUI.

   .. figure:: img/editrulebasic.png

      *Editing basic style rules*

   .. figure:: img/editrulelink.png

      *Editing style labels*

#. When done, click :guilabel:`Save`, then click on the word :guilabel:`Layers` to return to the layer list.

   .. figure:: img/styledlayer.png

      *Styled layer*
