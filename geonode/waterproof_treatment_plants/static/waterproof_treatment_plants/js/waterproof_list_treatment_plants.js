/**
 * @file Create form validations
 * @author Luis Saltron
 * @version 1.0
 */
 console.log(1)
$(function () {
    var table = $('#example').DataTable();
    var countryDropdown = $('#countryNBS');
    var currencyDropdown = $('#currencyCost');
    var transitionsDropdown = $('#riosTransition');
    var transformations = [];
    var lastClickedLayer;
    var map;
    var highlighPolygon = {
        fillColor: "#337ab7",
        color: "#333333",
        weight: 0.2,
        fillOpacity: 0.7
    };
    var defaultStyle = {
        fillColor: "#337ab7",
        color: "#333333",
        weight: 0.2,
        fillOpacity: 0
    };
    initialize = function () {
        console.log(2)
        initMap();
        var idViewTreeTreatmentPlant = $('#idViewTreeTreatmentPlant');

        idViewTreeTreatmentPlant.click(function (e) {
            alert(1412)
        });
    };
    initMap = function () {
        console.log(3)
        map = L.map('mapid').setView([51.505, -0.09], 13);
        L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
            maxZoom: 18,
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
                'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
            id: 'mapbox/streets-v11',
            tileSize: 512,
            zoomOffset: -1
        }).addTo(map);
        let countries = new L.GeoJSON.AJAX(countriesLayerUrl,
            {
                style: defaultStyle
            }
        );
        countries.addTo(map);

        countries.on("data:loaded", function () {
            let mapClick = false;
            updateCountryMap(userCountryCode);
        });
        $('#createUrl').attr('href','create/' + userCountryId)
    };
    updateCountryMap = function (countryCode) {
        console.log(4)
        map.eachLayer(function (layer) {
            if (layer.feature) {
                if (layer.feature.id == countryCode) {
                    if (lastClickedLayer) {
                        lastClickedLayer.setStyle(defaultStyle);
                    }
                    layer.setStyle(highlighPolygon);
                    map.fitBounds(layer.getBounds());
                    lastClickedLayer = layer;
                }
            }
        });
    };
    initialize();
});