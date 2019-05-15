# Quick Start:

Clone the repository with the --recursive option to automatically clone submodules:

`git clone --recursive https://github.com/geosolutions-it/MapStore2.git`

Install NodeJS >= 4.6.1 , if needed, from [here](https://nodejs.org/en/download/releases/).

Update npm to 3.x, using:

`npm install -g npm@3`

Start the demo locally:

`npm cache clean` (this is useful to prevent errors on Windows during install)

`npm install`

`npm start`

Then point your preferred browser to [http://localhost:8081](http://localhost:8081).

Install latest Maven, if needed, from [here](https://maven.apache.org/download.cgi) (version 3.1.0 is required).

Build the deployable war:

`./build.sh`

Deploy the generated mapstore.war file (in web/target) to your favourite J2EE container (e.g. Tomcat).

# Developers documentation
 * [Infrastructure](infrastructure-and-general-architecture)
 * [Building and deploying](building-and-developing)
 * [Developing with MapStore 2](developing-with-mapstore-2-intro)
 * [Configuration](configuration-files)
 * [Migration](mapstore-migration-guide)
