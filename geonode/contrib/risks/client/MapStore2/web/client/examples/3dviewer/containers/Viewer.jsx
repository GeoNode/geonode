const React = require('react');
const connect = require('react-redux').connect;
const LMap = require('../../../components/map/cesium/Map');
const LLayer = require('../../../components/map/cesium/Layer');

const SearchBar = require("../../../components/mapcontrols/search/SearchBar");
const SearchResultList = require("../../../components/mapcontrols/search/SearchResultList");
const MousePosition = require("../../../components/mapcontrols/mouseposition/MousePosition");
const pointOnSurface = require('turf-point-on-surface');

const {changeMapView} = require('../../../actions/map');
const {changeMousePosition} = require('../../../actions/mousePosition');
const {textSearch, resultsPurge, searchTextChanged, selectSearchItem} = require("../../../actions/search");
const {toggleGraticule} = require('../actions/controls');

const Localized = require('../../../components/I18N/Localized');

const Viewer = React.createClass({
    propTypes: {
        // redux store slice with map configuration (bound through connect to store at the end of the file)
        map: React.PropTypes.object,
        layers: React.PropTypes.array,
        // redux store dispatch func
        dispatch: React.PropTypes.func,
        textSearch: React.PropTypes.func,
        searchTextChanged: React.PropTypes.func,
        resultsPurge: React.PropTypes.func,
        changeMapView: React.PropTypes.func,
        changeMousePosition: React.PropTypes.func,
        toggleGraticule: React.PropTypes.func,
        updateMarker: React.PropTypes.func,
        mousePosition: React.PropTypes.object,
        messages: React.PropTypes.object,
        locale: React.PropTypes.string,
        localeError: React.PropTypes.string,
        searchResults: React.PropTypes.array,
        mapStateSource: React.PropTypes.string,
        showGraticule: React.PropTypes.bool,
        marker: React.PropTypes.object,
        searchText: React.PropTypes.string
    },
    onSearchClick: function(center, option) {
        this.props.updateMarker(center, option);
    },
    getMarkerPoint() {
        let feature = this.props.marker;
        if (feature.type === "Feature") {
            feature = pointOnSurface(feature);
        } else if (feature.lng !== undefined && feature.lat !== undefined) {
            return feature;
        }
        return {
            lat: feature.geometry && feature.geometry.coordinates[1],
            lng: feature.geometry && feature.geometry.coordinates[0]
        };

    },
    renderLayers(layers) {
        if (layers) {

            return layers.map(function(layer) {
                return <LLayer type={layer.type} key={layer.name} options={layer} />;
            }).concat(this.props.showGraticule ? [<LLayer type="graticule" key="graticule" options={{
                name: "graticule",
                visibility: true,
                color: [0.0, 0.0, 0.0, 1.0]
            }}/>] : []).concat(this.props.marker ? [<LLayer type="marker" key="marker" options={{
                name: "marker",
                visibility: true,
                point: this.getMarkerPoint()
            }}/>] : []);
        }
        return null;

    },
    render() {
        // wait for loaded configuration before rendering
        if (this.props.map && this.props.layers && this.props.messages) {
            return (
                <Localized messages={this.props.messages} locale={this.props.locale} loadingError={this.props.localeError}>
                    <div className="fill">
                        <LMap id="map" center={this.props.map.center} zoom={this.props.map.zoom}
                            onMapViewChanges={this.props.changeMapView} mapStateSource={this.props.mapStateSource}
                            onMouseMove={this.props.changeMousePosition}>
                            {this.renderLayers(this.props.layers)}
                        </LMap>
                        <div style={{
                                position: "absolute",
                                zIndex: 1000,
                                right: "20px",
                                top: "20px",
                                backgroundColor: "white",
                                opacity: 0.7,
                                padding: "10px"
                            }}>
                            <label>Graticule:&nbsp;&nbsp;<input type="checkbox" checked={this.props.showGraticule} onChange={this.props.toggleGraticule}/></label>
                        </div>
                        <SearchBar key="seachBar" searchText={this.props.searchText} onSearchTextChange={this.props.searchTextChanged} onSearch={this.props.textSearch} onSearchReset={this.props.resultsPurge} />
                        <SearchResultList key="nominatimresults"
                            results={this.props.searchResults}
                            onItemClick={this.onSearchClick}
                            afterItemClick={this.props.resultsPurge}
                            mapConfig={this.props.map}/>
                            <MousePosition
                                key="mousePosition"
                                enabled={true}
                                mousePosition={this.props.mousePosition}
                                crs="EPSG:4326"/>
                    </div>
                </Localized>
            );
        }
        return null;
    }
});


require('../../../components/map/cesium/plugins/index');

// connect Redux store slice with map configuration
module.exports = connect((state) => {
    return {
        map: state.map || state.mapConfig && state.mapConfig.map,
        mapStateSource: state.map && state.map.mapStateSource,
        layers: state.mapConfig && state.mapConfig.layers,
        messages: state.locale ? state.locale.messages : null,
        locale: state.locale ? state.locale.current : null,
        localeError: state.locale && state.locale.loadingError ? state.locale.loadingError : undefined,
        searchResults: state.searchResults && state.searchResults.results ? state.searchResults.results : null,
        searchText: state.searchResults && state.searchResults.searchText,
        mousePosition: state.mousePosition && state.mousePosition.position || null,
        showGraticule: state.controls && state.controls.graticule || false,
        marker: state.searchResults && state.searchResults.markerPosition || null
    };
}, {
    textSearch,
    searchTextChanged,
    resultsPurge,
    changeMapView,
    changeMousePosition,
    toggleGraticule,
    updateMarker: selectSearchItem
})(Viewer);
