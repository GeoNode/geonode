var React = require('react');
var connect = require('react-redux').connect;
var LMap = require('../../../components/map/leaflet/Map');
var LLayer = require('../../../components/map/leaflet/Layer');

var MyApp = React.createClass({
    propTypes: {
        // redux store slice with map configuration (bound through connect to store at the end of the file)
        mapConfig: React.PropTypes.object,
        // redux store dispatch func
        dispatch: React.PropTypes.func
    },
    renderLayers(layers) {
        if (layers) {
            return layers.map(function(layer) {
                return <LLayer type={layer.type} key={layer.name} options={layer} />;
            });
        }
        return null;
    },
    render() {
        // wait for loaded configuration before rendering
        if (this.props.mapConfig && this.props.mapConfig.map) {
            return (
                <LMap id="map" center={this.props.mapConfig.map.center} zoom={this.props.mapConfig.map.zoom}>
                     {this.renderLayers(this.props.mapConfig.layers)}
                </LMap>
            );
        }
        return null;
    }
});

// include support for OSM and WMS layers
require('../../../components/map/leaflet/plugins/OSMLayer');
require('../../../components/map/leaflet/plugins/WMSLayer');

// connect Redux store slice with map configuration
module.exports = connect((state) => {
    return {
        mapConfig: state.mapConfig
    };
})(MyApp);
