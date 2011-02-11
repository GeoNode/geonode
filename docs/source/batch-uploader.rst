Batch Uploader
==============

This page describes how to enable GeoNode to accept layers uploaded in batch mode via FTP.

TODO: Discuss Other potential methods of upload. WebDAV, AWS S3, REST (curl etc)

Dependencies
=============

installed during bootstrap process.

django-celery - http://pypi.python.org/pypi/django-celery

ghettoq - https://github.com/ask/ghettoq

django-notification - http://pypi.python.org/pypi/django-notification/0.1.3

Django Database Configuration
-----------------------------

Due to multithreading issues with sqlite, it is not recommended to use
it as a database back end when running a task queue in production. 
A proper relational database service (postgresql, mysql etc) should be
used. This functionality has only been tested with PostgreSQL which 
requires the use of the psycopg2 python module for interacting with the
database service. The django database is configured in 
src/GeoNode/geonode/settings.py or src/GeoNode/geonode/local_settings.py

psycopg2 - http://initd.org/psycopg/


GeoServer FTP Service
=====================

GeoServer can provide an FTP Service to runs on a configured port, which
authenticates via GeoNodes user database and accepts uploads of shapefiles, 
zipped  shapefiles and raster (tiff) files. Upon successful upload, GeoNode 
is notified of the newly uploaded data and registers it with GeoServer and 
into its own DB as well as writing the layer metadata to GeoNetwork. 
The User who uploaded the files is notified of successful registration 
of the layer in GeoNode, or of failure and a description of the reason 
for the failure. 

The FTP Services is configured via ftp.xml which is stored in the 
GEOSERVER_DATA_DIR

gs-data/ftp.xml

    <?xml version="1.0" ?>
    <ftp>
    <!--true to enable the FTP service, false to disable it-->
    <enabled>true</enabled>
    <!--Port where the FTP Service listens for connections-->
    <ftpPort>21</ftpPort>
    <!--number of seconds during which no network activity is allowed before a session is closed due to inactivity-->
    <idleTimeout>120</idleTimeout>
    <!--IP Address used for binding the local socket. If unset, the server binds to all available network interfaces-->
    <serverAddress></serverAddress>
    <!--Ports to be used for PASV data connections. Ports can be defined as single ports, closed or open ranges:
    Multiple definitions can be separated by commas, for example:
    2300 : only use port 2300 as the passive port
    2300-2399 : use all ports in the range
    2300- : use all ports larger than 2300
    2300, 2305, 2400- : use 2300 or 2305 or any port larger than 2400
    -->
    <passivePorts>2300-2400</passivePorts>
    <!--Address on which the server will listen to passive data connections,
    if not set defaults to the same address as the control socket for the session.-->
    <passiveAddress></passiveAddress>
    <!--the address the server will claim to be listening on in the PASV reply.
    Useful when the server is behind a NAT firewall and the client sees a different address than the server is using.-->
    <passiveExternalAddress></passiveExternalAddress>
    </ftp>

TODO: Address potential passive ftp problems when running an FTP service
on Amazon Web Services.


Django Celery Database Queue
============================

Upon completion of the upload to the FTP service, the GeoNode application
is notified of the file and begins the process of registering it in its
own layer registry as well as in the GeoServer and GeoNetwork applications.
This process happens asynchronously insofar as the uploaded files are 
queued for processing in the order they are received. The Celery Distributed
Task Queue module is used to control and monitor this process. GeoNode
uses the ghettoq task queue on top of a django database accessed via the ORM
to store task metadata including status. Other message brokers, including
RabbitMQ can be used with Django Celery but configuration is beyond the scope
of this documentation.

The django-manage.py command will create the tables required to store task
metadata with the syncdb command.

    django-admin.py syncdb --settings=geonode.settings

Other Queues

 * RabbitMQ

TODO: Provide an interface to the message queue that allows the user to
check the status of queued uploads.


Notifications
=============

Upon completion of the Layer registration process, a notification is
prepared for the User which uploaded the files. If the registration
was successful, a link is provided to the new layer in GeoNode.
If registration failed, some indication of the cause of the failure
is provided. 

TODO: Provide functionality for correcting the issue causing the 
failure (specify projection etc) and re-attempt registration.

TODO: Provide access to notifications in GeoNode UI along with other 
messages in the Users Dashboard.

http://dev.geonode.org/trac/wiki/UserProfile


Celery daemon
=============

Development Mode
----------------

In development mode the celery queue monitoring service can be started
with the -c option to the paver host command.

    paver host -c

... or if starting GeoNode via separate commands for jetty and django, 
a third command in a seperate terminal is required.

    django-admin.py celeryd --settings=geonode.settings

Production
----------

In production mode, the celery queue monitoring service should be daemonized
and stopped/started with other system services.

More documentation on how this can be accomplished on various platforms
and distribution is described in the Celery Documentation here.

http://celeryq.org/docs/cookbook/daemonizing.html#example-django-configuration


Logging
=======

The Celery Task Queue daemon diverts stderr and stdout from the normal django log
to its own log for the pieces of code that are executed asynchronously using the 
task queue. In development mode, celery.log will be stored in the top level directory
where paver or django-admin.py are run from, in production, the log file location is
configured in the daemonization setup (/var/log/celeryd.log if the default init scripts
are used).

The celery logs are a very useful place to look at complete stacktraces of upload errors
when developing and testing.


Potential Upload Issues
=======================

Projection
----------

The most common cause of failed uploads is a missing or unrecognized projection
file. In this case, the layer is not fully registered with GeoServer and as such
is unable to be used in GeoNode. Currently the only way to fix this problem is 
to login as an administrator to the GeoServer application and and use the UI to 
specify the proper projection for the layer and then run the updatelayers management
command. TODO:
