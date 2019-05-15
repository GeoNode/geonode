# Support Tools
The Map plugin allows adding mapping library dependent functionality using support tools. Some are already available for the supported mapping libraries (openlayers, leaflet, cesium), but it's possible to develop new ones.

An example is the MeasurementSupport tool that allows implementing measurement on a map.

The list of enabled tools can be configured using the **tools** property, as in the following example:

```js
{
      "name": "Map",
      "cfg": {
        "tools": ["measurement", "locate", "overview", "scalebar", "draw", "highlight"]
        ...
      }
}
```

Each tool can be configured using the **toolsOptions**. Tool configuration can be mapping library dependent:

```js
"toolsOptions": {
    "scalebar": {
        "leaflet": {
            "position": "bottomright"
        }
        ...
    }
    ...
}
```

or not:

```js
"toolsOptions": {
    "scalebar": {
        "position": "bottomright"
        ...
    }
    ...
}
```

## Custom Support Tools
In addition to standard tools, you can also develop your own, ad configure them to be used. To do that you need to:
 * develop a tool Component, in JSX (e.g. TestSupport), for each supported mapping library

```js
const React = require('react');

const TestSupport = React.createClass({
    propTypes: {
        label: React.PropTypes.string
    },
    render() {
        alert(this.props.label);
        return null;
    }
});

module.exports = TestSupport;
```
 * include the tool(s) in the requires section of plugins.js and give it a **name**:

```js
module.exports = {
    plugins: {
        MapPlugin: require('../plugins/Map'),
        ...
    },
    requires: {
        ...
        TestSupportLeaflet: require('../components/map/leaflet/TestSupport')
    }
};
```
 * configure the Map plugin including the new tool and related options. You can configure the tool to be used for each mapping library, giving it a **name** and **impl** attributes, where:
  * name is a unique name for the tool
  * impl is a placeholder ("{context.ToolName}") where ToolName is the **name** you gave the tool in plugins.js (TestSupportLeaflet in our example)

```js
{
  "name": "Map",
  "cfg": {
    "tools": ["measurement", "locate", "overview", "scalebar", "draw", {
      "leaflet": {
        "name": "test",
        "impl": "{context.TestSupportLeaflet}"
      }
      }],
    "toolsOptions": {
      "test": {
        "label": "ciao"
      }
      ...
    }
  }
}
```

NOTE: When using the "impl" configuration you are responsible for the correct configuration of such tool, **remember to add any other property it may require in the configuration**.
