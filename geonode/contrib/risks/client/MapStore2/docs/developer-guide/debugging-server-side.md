# Run or Debug server side part using mvn and eclipse

To run or debug the server side part of MapStore we suggest to use jetty:run plugin. 
This guide explains how to do it with Eclipse. This procedure is tested with Eclipse Luna. 



## Simply Run the server side part

you can simply run the server side part using `mvn jetty:run` command. To run the server side part only, run: 

```
mvn jetty:run -Pserveronly
```

This will skip the javascript building phase, you can now connect the webpack proxy to the server side proxy and debug client side part using: 

```
npm start
```


## Enable Remote Debugging with jetty:run 

Set the maven options as following : 
```
# Linux 
MAVEN_OPTS="-Xdebug -Xnoagent -Djava.compiler=NONE -Xrunjdwp:transport=dt_socket,address=4000,server=y,suspend=n"
```
```
# Windows
set MAVEN_OPTS=-Xdebug -Xnoagent -Djava.compiler=NONE -Xrunjdwp:transport=dt_socket,address=4000,server=y,suspend=n
```

then run jetty
```
mvn jetty:run -Pserveronly
```


### Setup eclipse project 

* Run eclipse plugin
```
mvn eclipse:eclipse
```
* Import the project in eclipse from **File --> Import** 
* Then select Existing project into the Workspace
* Select root directory as "web" (to avoid eclipse to iterate over all node_modules directories looking for eclipse project) 
* import the project


### Start Debugging with eclipse
* Start Eclipse and open **Run --> Debug Configurations** 
* Create a new Remote Java Application selecting the project "mapstore-web" setting:
  * host localhost
  * port 4000 
  * Click on *Debug* 
Remote debugging is now available. 

> **NOTE** With some version of eclipse you will have to set `suspend=y` in mvn options to make it work. In this case 
the server will wait for the debug connection at port 4000 (`address=4000`)