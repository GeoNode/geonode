To create a new project you can use the createProject script:

```
node ./createProject.js <projectName> <projectVersion> <projectDescription> <gitRepositoryUrl> <outputFolder>
```

All the arguments are mandatory:
 * **projectName**: short project name that will be used as the repository name on github, webapp path and name in package.json
 * **projectVersion**: project version in package.json
 * **projectDescription**: project description, used in sample index page and as description in package.json
 * **gitRepositoryUrl**: full url to the github repository where the project will be published
 * **outputFolder**: folder where the project will be created (must exist)

At the end of the script execution, the given outputFolder will be populated by all the configuration files needed to start working on the project and a sample application with two pages (home and main). Moreover, the local git repo will be initialized and the MapStore2 submodule added and downloaded.

Following steps are:
 * npm install to download dependencies
 * npm start to test the project
 * git add / push to publish the initial project on the git repo