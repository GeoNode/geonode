#Building and developing

Due to the dual nature of the project (Java backend and Javascript frontend) building and developing using the MapStore 2 framework requires two distinct set of tools
 * [Apache Maven](https://maven.apache.org/) for Java
 * [NPM](https://www.npmjs.com/) for Javascript.

A basic knowledge of both tools is required.

# Developing and debugging the MapStore 2 framework
To start developing the MapStore 2 framework you have to:
 * download developer tools and frontend dependencies locally:

`npm install`

After a while (depending on the network bandwidth) the full set of dependencies and tools will be downloaded to the **node_modules** subfolder.

 * start a development instance of the framework and example applications:

`npm run examples`

 * or you can start a development instance **without the examples**:

`npm start`

Then point your preferred browser to [http://localhost:8081](http://localhost:8081).

The HomePage contains links to the available demo applications.

## Frontend debugging
The development instance uses file watching and live reload, so each time a MapStore 2 file is changed, the browser will reload the updated application.

Use your favourite editor / IDE to develop and debug on the browser as needed.

We suggest to use one of the following:

 * [Atom](https://atom.io/) with the following plugins:
   - editorconfig
   - linter
   - linter-eslint
   - react
   - lcovinfo
   - minimap & minimap-highlight-selected
   - highlight-line & highlight-selected
 * [Sublime Text Editor](http://www.sublimetext.com/) with the following plugins:
   - Babel
   - Babel snippets
   - Emmet

## Backend services debugging
TBD

## Frontend testing
To run the MapStore 2 frontend test suite you can use:

`npm test`

You can also have a continuosly running watching test runner, that will execute the complete suite each time a file is changed, launching:

`npm run continuoustest`

To run ESLint checks launch:

`npm run lint`

To run the same tests Travis will check (before a pull request):
`npm run travis`

More information on frontend building tools and configuration is available [here](frontend-building-tools-and-configuration)

# General building and deploying
Maven is the main tool for building and deploying a complete application. It takes care of:
 * building the java libraries and webapp(s)
 * calling NPM as needed to take care of the frontend builds
 * launching both backend and frontend test suites
 * creating the final war for deploy into a J2EE container (e.g. Tomcat)

To create the final war, you have several options:
 * full build, including submodules and frontend (e.g. GeoStore)

`./build.sh`

 * fast build (will use the last compiled version of submodules and compiled frontend)

`mvn clean install`

# Troubleshooting

## Autowatch doesn't work on Linux.
You should need to increase `max_user_watches` variable for inotify.
```
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
```
