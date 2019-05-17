# Migration from 2017.01.00 to 2017.02.00
The version 2017.02.00 has many improvements and changes:
  * introduced `redux-observable`
  * updated `webpack` to version 2
  * updated `react-intl` to version 2.x
  * updated `react` to [version 15.4.2] (https://facebook.github.io/react/blog/2016/04/07/react-v15.html)
  * updated `react-bootstrap` to version 0.30.7


We suggest you to:
 * align your package.json with the latest version of 2017.02.00.
 * update your webpack files (see below).
 * update your tests to react 15 version. [see upgrade guide](https://facebook.github.io/react/blog/2016/04/07/react-v15.html#upgrade-guide)
 * Update your `react-bootstrap` custom components with the new one (see below).

## Side Effect Management - Introduced redux-observable
To manage complex asynchronous operations the thunk middleware is not enough.
When we started with MapStore 2 there was no alternative to thunk. Now we have some options. After a spike (results available [here](https://github.com/geosolutions-it/MapStore2/issues/1420)) we chose to use redux-observable.
For the future, we strongly recommend to use this library to perform asynchronous tasks.

Introducing this library will allow to :
 * remove business logic from the components event handlers
 * now all new  `actionCreators` should return pure actions. All async stuff will be deferred to the epics.
 * avoid bouncing between components and state to trigger side effect
 * speed up development with `rxjs` functionalities
 * Existing thunk integration will be maintained since all the thunks will be replaced.

If you are using the Plugin system and the StandardStore, you may have only to include the missing new dependencies in your package.json (redux-observable and an updated version of redux).

Check the current package.json to get he most recent versions. For testing we included also redux-mockup-store as a dependency, but you are free to test your epics as you want.
 
For more complex integrations check [this](https://github.com/geosolutions-it/MapStore2/pull/1471) pull request to see how to integrate redux-observable or follow the guide on the [redux-observable site](https://redux-observable.js.org/).

## Webpack update to version 2
We updated webpack (old one is deprecated), check [this pull request](https://github.com/geosolutions-it/MapStore2/pull/1491) to find out how to update your webpack files.
here a list of what we had to update:
 * module.loaders are now module.rules
 * update your package.json with latest versions of webpack, webpack plugins and karma libs and integrations (Take a look to the changes on package.json in the pull request if you want a detailed list of what to update in this case).
 * change your test proxy configuration with the new one.
 
More details on the [webpack site](https://webpack.js.org/guides/migrating/).


## react-intl update to  2.x
See [this pull request](https://github.com/geosolutions-it/MapStore2/pull/1495/files) for the details. You should only have to update your package.json

## react update to 15.4.2
Check this pull request to see how to:
* update your package.json
* update your tests

## React Bootstrap update
The version we are using is not documented anymore, and not too much compatible with react 15 (too many warnings). So this update can not be postponed anymore.
The bigger change in this case is that the Input component do not exists anymore. You will have to replace all your Input with the proper components, and update the `package.json`. See [this pull request](https://github.com/geosolutions-it/MapStore2/pull/1511) for details.
