.. _geoserver.jmeter_controlflow:


Configuring JMeter for testing Control Flow plugin
==================================================

This section explains how GeoServer performances are improved when using Control-Flow plugin. 

This plugin avoid GeoServer to execute too many requests together, which could lead to bad performances, by reducing the number of concurrent operations to execute and appending the others to a queue. This behaviour improves GeoServer scalability. 

.. note:: This example requires to have already completed :ref:`Adding a ShapeFile <geoserver.add_shp>` and :ref:`Adding a Style <geoserver.add_style>` sections.

Configure JMeter
----------------
	
#. Go to ``$TRAINING_ROOT/data/jmeter_data`` and copy the file ``template.jmx`` file into ``controlflow.jmx``

#. From the training root, on the command line, run ``jmeter.bat`` (or ``jmeter.sh`` if you're on Linux) to start JMeter

#. On the top left go to :guilabel:`File --> Open` and search for the new *jmx* file copied

#. Disable **View Results Tree** section

#. In the ``CSV Data Set Config`` element, modify the **path** of the CSV file by setting the path for the file ``controlflow.csv`` in the ``$TRAINING_ROOT/data/jmeter_data`` directory
	  
#. In the **HTTP Request Default** element modify the following parameters:

	.. list-table::
		  :widths: 30 50

		  * - **Name**
		    - **Value**
		  * - layers
		    - geosolutions:Mainrd
		  * - srs
		    - EPSG:2876
	
	
Test without Control Flow
-------------------------

#. Run the test

	.. note:: Remember to run and stop the test a few times for having stable results
   
#. When the test is completed, Save the results in a text file. 

	You should notice that the throughput initially increases and then starts to decrease. This is associated to a bad scalability of the input requests. Remember which number of threads provides better throughput (it should be *8*). This value indicates the maximum number of concurrent requests that the server can execute simultaneously.

   .. figure:: img/jmeter34.png
      :align: center
   
      *Decreased throughput (Note the results may be different in other machines)*	
	
#. Remove the result from JMeter by clicking on :guilabel:`Run --> Clear All` on the menu

#. Stop GeoServer

Configure Control Flow
----------------------
#. Go to ``$TRAINING_ROOT/data/plugins/not_installed`` and copy ``geoserver-2.6-SNAPSHOT-control-flow-plugin.zip`` zip file inside ``$TRAINING_ROOT/tomcat-6.0.36/instances/instance1/webapps/geoserver/WEB-INF/lib``

#. Unzip the content of ``geoserver-2.6-SNAPSHOT-control-flow-plugin.zip`` inside the same folder

#. Go to ``$TRAINING_ROOT/geoserver_data`` and create a new file called ``controlflow.properties`` and add the following snippet

		.. code-block:: xml
			
			# don't allow more than 8 WMS GetMap in parallel
			ows.wms.getmap=8
			
		This code snippet indicates that no more than 8 *GetMap* request can be executed simultaneously by the WMS service. Other informations about the configuration can be found in the next section

		.. note:: If during your test you have found another number for the maximum throughput, you should set that value instead of 8 
		
Test with Control Flow
----------------------

#. Restart GeoServer

#. Run again the test.
		
	You may see that the throughput is no more reduced after the control-flow configuration, because the input requests are scheduled by the control-flow plugin, improving GeoServer scalability.
	
   .. figure:: img/jmeter35.png
      :align: center
   
      *Stable throughput (Note the results may be different in other machines)*		