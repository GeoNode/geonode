# Introduction
The easiest way to try out MapStore2 is to download and extract the binary package available on MapStore2 [release page](https://github.com/geosolutions-it/MapStore2/releases/latest).
Here you can find some preconfigured maps as well users and groups.
The goal for this package is to ease all the requirements needed for you to take MapStore2 for a test-drive.

We hope you enjoy MapStore2!

# How to run
Go to the location where you saved the zip file, unzip the contents and run:

Windows: `mapstore2_startup.bat`

Linux: `./mapstore2_startup.sh`

Point you browser to: [http://localhost:8800/mapstore](http://localhost:8800/mapstore)

To stop MapStore2 simply do:

Windows: `mapstore2_shutdown.bat`

Linux: `./mapstore2_shutdown.sh`

# Package Contents
* [MapStore2](https://github.com/geosolutions-it/MapStore2/releases/latest)
* [Tomcat7](http://www.apache.org/dist/tomcat/tomcat-7/v7.0.75/)
* [Java JRE (Win and Linux)](http://www.oracle.com/technetwork/java/javase/downloads/jre7-downloads-1880261.html)

# Demo Maps
* **Unesco Italian sites** - Simple WMS layer map demo
* **Aerial Imagery** - Simple map demo showing some aerial imagery data
* **WFS Query Map** - Demo map configured with MapStore2 built-in ability to query feature over WFS
* **Multi-Layered Map** - A more real world approach to a simple WMS map built with MapStore2 with multiple layers.
* **User Map and User1 Map** - Map only visible to *user* and *user1* respectively, to demonstrate MapStore2 capabilities on user/group management and permissions.

# Demo accounts/groups

| **Users**       | **Groups**            |
|-----------------|-----------------------|
| **admin/admin** | MyGroupAdmin,everyone |
| guest           | everyone              |
| user/user       | everyone              |
| user1/user1     | everyone, MyGroup     |