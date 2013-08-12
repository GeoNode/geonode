Servlet Container Installation
==============================

If you installed geonode in developing mode following this guide (LINK), then geonode will be using *jetty* as servlet container. This is a default setting and you can also use tomcat as servlet container. This tutorial will teach you how to change jetty with tomcat. 

Tomcat Installation
-------------------

#. Download and unpack Tomcat

   Go to http://tomcat.apache.org and get the latest version of tomcat (tar.gz package). To install tomcat go to your folder *Downloads* and unpack the *tar* file.

   .. code-block:: console

	$ cd /Downloads
	$ tar xzvf apache-tomcat-7.0.xx.tar.gz

   Copy the unpacked folder to another directory, whereever you want tomcat to be, e.g /myproject/ or /usr/local or even /opt/ (you might have to have root permissions on that)

   .. code-block:: console

	$ sudo cp -r apache-tomcat-7.0.42/ /opt/

#. Setup Environment Variable JAVA_HOME

   In a next step we have to set the environment variable JAVA_HOME, containing the JDK installed directory. To proove whether it is already set, type
   
   .. code-block:: console
   
   	$ echo $JAVA_HOME
   
   If nothing happens, it means that your variable is unset at the moment! Therefore you have to edit the file called *profile.
  
   .. code-block:: console
   
	$ cd /etc
	$ sudo gedit profile
	
   The JAVA_HOME variable is basically the path to your JDK. If your variable is not set, you should now where Java has been installed in your directory and copy the path.
   
   Add the following line to the very end of the file::

	export JAVA_HOME=/path/to/your/JDK
	
	e.g
	
	export JAVA_HOME=/usr/lib/jvm/java-6-openjdk
	
   Now rerun the script
   
   .. code-block:: console
   
	$ source /etc/profile

#. Configure Tomcat Server

Tomcat 7 will be running on the port 8080 as default. This can be changed in the server.xml file which can be found in the folder *conf*. Leave the settings as they are at the moment. For more information on the configuration of tomcat visit http:ladida.

.. todo:: Is this really necessary?
          .# edit the "conf\tomcat-user.xmls"
          to enable the tomcat's manager, paste those lines into the file
         <tomcat-users>
           <role rolename="manager-gui"/>
           <user username="manager" password="xxxx" roles="manager-gui"/>
         </tomcat-users>

#. Start Tomcat Server

The executable programs and scripts are in the 'bin' directory of Tomcat. So go to your bin folder and run the *catalina.sh* script.

.. code-block::

	$ cd /opt/apache-tomcat-7.0.42/bin
	$ ./catalina.sh run
	
If that doesn't work for now, try 

.. code-block::

	$ sudo chmod uga+x *.sh
	
at first and then again

.. code-block::

	$ sudo ./catalina.sh run
again!

.. hint:: You might get an error that ``java/bin`` wasn´t found. If that´s the case, please check again your path to the JDK and again change it in the *profile* file. Don´t forget to rerun the script afterwards!

Now type http://localhost:8080 and http://localhost:8080/examples and you should see the starting page of Tomcat.

.. image:: img/startpage_tomcat.PNG
.. todo:: CREATE THIS IMAGE!

To shut down tomcat:

.. code-blocks::

	$ cd /opt/apache-tomcat-7.0.42/bin
	$ ./shutdown.sh

Deploying Geoserver
-------------------

When installing geonode in developing mode, you´ve also got a *geoserver.war* file included. You will find this in your geonode directory::

	geonode/downloaded/geoserver.war

Now copy this file into the *webapps* folder of tomcat

.. code-block::

	$ sudo cp geoserver.war /opt/apache-tomcat-7.0.42/webapps
	
By starting tomcat it will unpack the geoserver.war and create a new directory ``tomcat/webapps/geoserver``. 

.. code-block::

	$ cd /opt/apache-tomcat-7.0.42/bin
	$ sudo ./catalina.sh run
	
Let´s try to attend http://localhost:8080/geoserver. You will now see the geoserver homepage.

.. figure:: img/geoserver_homepage.PNG
.. todo:: CREATE THIS IMAGE!


for testing:
------------
	
  $ paver start_django

=> I didn't started geoserver using paver start_geoserver
but was able to attend localhost:8080/geoserver as well (was running)
=> stores and layers vanished, but i can login with my superuser barbara
