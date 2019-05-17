Frontend building is delegated to [NPM](https://www.npmjs.com/) and so leverages the NodeJS ecosystem.

In particular:

 * a **[package.json](https://github.com/geosolutions-it/MapStore2/blob/master/package.json)** file is used to configure frontend dependencies, needed tools and building scripts
 * **[babel](https://babeljs.io/)** is used for ES6/7 and JSX transpiling integrated with the other tools (e.g. webpack)
 * **[webpack-dev-server](http://webpack.github.io/docs/webpack-dev-server.html)** is used to host the development application instance
 * **[mocha](http://mochajs.org/)/[expect](https://github.com/mjackson/expect)** is used as a testing framework (with BDD style unit-tests)
 * **[webpack](http://webpack.github.io/)**: as the bundling tool, for development (see [webpack.config.js](https://github.com/geosolutions-it/MapStore2/blob/master/webpack.config.js)), deploy (see [prod-webpack.config.js](https://github.com/geosolutions-it/MapStore2/blob/master/prod-webpack.config.js)) and test (see [test.webpack.js](https://github.com/geosolutions-it/MapStore2/blob/master/tests.webpack.js)
 * **[karma](http://karma-runner.github.io/)** is used as the test suite runner, with several plugins to allow for custom reporting, browser running and so on; the test suite running is configured through different configuration files, for **[single running](https://github.com/geosolutions-it/MapStore2/blob/master/karma.conf.single-run.js)**  or **[continuous testing](https://github.com/geosolutions-it/MapStore2/blob/master/karma.conf.continuous-test.js)**
 * **[istanbul](https://gotwarlost.github.io/istanbul/)/[coveralls](https://www.npmjs.com/package/coveralls)** are used for code coverage reporting
 * **[eslint](eslint.org)** is used to enforce coding styles guidelines, the tool is configured using a **[.eslintrc](https://github.com/geosolutions-it/MapStore2/blob/master/.eslintrc)** file

# Available scripts
 * download dependencies and init developer environment

`npm install`

 * start development instance

`npm start`

* start development instance with examples

`npm run examples`

 * run test suite once

`npm test`

 * run continuous test suite running

`npm run continuoustest`
 
 * run single build / bundling

`npm run compile`

 * run ESLint checks

`npm run lint`

 * run tests from Maven

`npm run mvntest`

 * build for travis

`npm run travis`