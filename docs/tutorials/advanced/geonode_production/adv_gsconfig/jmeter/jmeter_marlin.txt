.. _geoserver.jmeter_marlin:


Configuring JMeter for testing the Marlin renderer
==================================================

This section explains how GeoServer performances are improved when using the **Marlin** renderer.

The Oracle JDK and OpenJDK come with two different anti-aliased renderers:

* Oracle JDK uses **Ductus**, a fast native renderer that has scalability issues (good for desktop use, less so on the server side)

* OpenJDK uses **Pisces**, a pure java renderer that is not as fast as "Ductus", but has good scalability (anecdotally, it becomes faster than Ductus above the 4 concurrent requests) 

The `Marlin <https://github.com/bourgesl/marlin-renderer>`_ renderer is an improved version of Pisces that is as fast, if not faster, than Ductus, and scales up just as well as Pisces.


Configure JMeter
----------------
	
#. Go to ``$TRAINING_ROOT/data/jmeter_data`` and copy the file ``template.jmx`` file creating a ``marlin.jmx`` file

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
		    - boulder
		  * - srs
		    - EPSG:2876
	
	
Test without Marlin
-------------------

#. Go and remove the contro

#. Run the test

	.. note:: Remember to run and stop the test a few times for having stable results
   
#. When the test is completed, Save the results in a text file. 

   .. figure:: img/no_marlin.png
      :align: center
      
      *Throughput without Marlin (Note the results may be different in other machines)*
	
#. Remove the result from JMeter by clicking on :guilabel:`Run --> Clear All` on the menu

#. Stop GeoServer

Setup Marlin
------------

#. Stop GeoServer

#. Download the Marlin rasterizer library at `https://github.com/bourgesl/marlin-renderer/releases/download/v0.4.4/marlin-0.4.4.jar <https://github.com/bourgesl/marlin-renderer/releases/download/v0.4.4/marlin-0.4.4.jar>`_ and save it in ``%TRAINING_ROOT%\data``

#. Open ``%TRAINING_ROOT%\setenv.bat`` and add the following lines to enable the Marlin renderer, right before the "Tomcat options for the JVM" section::

            REM Marlin support
            set JAVA_OPTS=%JAVA_OPTS% -Xbootclasspath/p:"%ROOT%\data\marlin-0.4.4.jar" 
            set JAVA_OPTS=%JAVA_OPTS% -Dsun.java2d.renderer=org.marlin.pisces.PiscesRenderingEngine
		
#. Start GeoServer again

#. Go to the map preview and open the ``boulder`` layer, you should see the following in the Tomcat console::

            INFO: ===============================================================================
            INFO: Marlin software rasterizer           = ENABLED
            INFO: Version                              = [marlin-0.4.4]
            INFO: sun.java2d.renderer                  = org.marlin.pisces.PiscesRenderingEngine
            INFO: sun.java2d.renderer.useThreadLocal   = true
            INFO: sun.java2d.renderer.useRef           = soft
            INFO: sun.java2d.renderer.pixelsize        = 2048
            INFO: sun.java2d.renderer.subPixel_log2_X  = 3
            INFO: sun.java2d.renderer.subPixel_log2_Y  = 3
            INFO: sun.java2d.renderer.tileSize_log2    = 5
            INFO: sun.java2d.renderer.useFastMath      = true
            INFO: sun.java2d.renderer.useSimplifier    = false
            INFO: sun.java2d.renderer.doStats          = false
            INFO: sun.java2d.renderer.doMonitors       = false
            INFO: sun.java2d.renderer.doChecks         = false
            INFO: sun.java2d.renderer.useJul           = false
            INFO: sun.java2d.renderer.logCreateContext = false
            INFO: sun.java2d.renderer.logUnsafeMalloc  = false
            INFO: ===============================================================================
		
Test with Marlin renderer
-------------------------

#. Run again the test.
		
	You may see that the throughput got significantly higher, especially at mid-high thread counts
	
   .. figure:: img/marlin.png
      :align: center
   
      *Throughput with Marlin (Note the results may be different in other machines)*		