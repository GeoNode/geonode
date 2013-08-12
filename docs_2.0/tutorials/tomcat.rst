Tomcat Installation and Configuration
=====================================


Install Tomcat
--------------
Go to http://tomcat.apache.org and get the latest version of tomcat (tar.gz package). To install tomcat go to your folder *Downloads* and unpack the *tar* file.

  $ cd /Downloads
	$ tar xzvf apache-tomcat-7.0.xx.tar.gz

Copy the unpacked folder to another directory, where you want tomcat to be, e.g /myproject/ or /usr/local or even /opt/ (you might have to have root permissions on that)

	$ sudo cp -r apache-tomcat-7.0.42/ /opt/

Setup Environment Variable JAVA_HOME
------------------------------------

type::
	$ echo $JAVA_HOME
nothing happend, therefore edit /etc/profile
	$ cd /etc
	$ sudo gedit profile
and add the following line to the end of the file!
	export JAVA_HOME=/etc/java-6-openjdk
	$ source /etc/profile

Configure Tomcat
----------------

.# edit the "conf\server.xml" - Set the TCP Port Number
   I won't do this for now! Port=8080 at the moment!
.# edit the "conf\web.xml" - Enabling Directory Listing
   won't do that either (would set listening to true)
.# edit the "conf\context.xml" - Enabling Automatic Reload
   won't do that either (would set reloadable=true)
.# edit the "conf\tomcat-user.xmls"
   to enable the tomcat's manager, paste those lines into the file
<tomcat-users>
  <role rolename="manager-gui"/>
  <user username="manager" password="xxxx" roles="manager-gui"/>
</tomcat-users>

Start Tomcat Server
-------------------

the executable programs and scripts are in the 'bin' directory

	$ cd /opt/apache-tomcat-7.0.42/bin
	$ ./catalina.sh run
if that doesn't work, try
	$ sudo chmod uga+x *.sh
at first and then
	$ ./catalina.sh run (sudo!)
again!

=> didn't worked because java/bin wasn't found
so i changed the directory of $JAVA_HOME in profile again to
	/usr/lib/jvm/java-6-openjdk
and did again	
	$ source /etc/profile
and then tried again
	$ cd /opt/apache-tomcat-7.0.42/bin
	$ sudo ./catalina.sh run
If tomcat is in directory /opt ``sudo`` has to be used! (root user is needed!!!)
check http://localhost:8080
and   http://localhost:8080/examples	(this might cause problems with geoserver?)
=> wuhu tomcat is running!

to shut down tomcat:
	$ cd /opt/apache-tomcat-7.0.42/bin
	$ ./shutdown.sh

Geoserver
---------

download *geoserver.war*; i've already got it on the machine (because of geonode)
	/home/barbara/geonode/downloaded/geoserver.war
	sudo su
to be root user and then copy this to
	/opt/apache-tomcat-7.0.42/webapps
using
	$ cp geoserver.war /opt/apache-tomcat-7.0.42/webapps
and then start tomcat
	$ cd /opt/apache-tomcat-7.0.42/bin
	$ sudo ./catalina.sh run
this takes a while.
Then try to attend
	http://localhost:8080/geoserver
and it is running!!!!!

for testing:
------------
	
  $ paver start_django

=> I didn't started geoserver using paver start_geoserver
but was able to attend localhost:8080/geoserver as well (was running)
=> stores and layers vanished, but i can login with my superuser barbara
