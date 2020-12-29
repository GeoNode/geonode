/**
 * @file Create Intake wizard step
 * validations & interactions
 * @version 1.0
 */
var urlParams = (function(url) {
    var result = new Object();
    var params = window.location.search.slice(1).split('&');
    for (var i = 0; i < params.length; i++) {
        idx = params[i].indexOf('=');
        if (idx > 0) {
            result[params[i].substring(0, idx)] = params[i].substring(idx + 1);
        }
    }
    return result;
})(window.location.href);

var mxLanguage = urlParams['lang'];
var map;
var mapDelimit;
var snapMarker;
var snapMarkerMapDelimit;
var catchmentPoly;
var catchmentPolyDelimit;
var mapLoader;
$(document).ready(function() {

    $("#intakeWECB").click(function() {
        $('#intakeECTAG tr').remove();
        $('#intakeEITA tr').remove();
        $('#autoAdjustHeightF').css("height", "auto");
        typeProcessInterpolation = Number($("#typeProcessInterpolation").val());
        numberYearsInterpolationValue = Number($("#numberYearsInterpolationValue").val());
        initialDataExtractionInterpolationValue = Number($("#initialDataExtractionInterpolationValue").val());
        finalDataExtractionInterpolationValue = Number($("#finalDataExtractionInterpolationValue").val());

        // Linear interpolation
        if (typeProcessInterpolation == 1) {
            m = (finalDataExtractionInterpolationValue - initialDataExtractionInterpolationValue) / (numberYearsInterpolationValue - 0)
            b = (-1 * m * 0) + initialDataExtractionInterpolationValue;

            for (let index = 0; index <= numberYearsInterpolationValue; index++) {
                $('#intakeECTAG').append(`<tr>
                <th class="text-center" scope="row">${index}</th>
                <td class="text-center">${((m*index)+b).toFixed(2)}</td>
              </tr>`);
            }
        }

        // Potencial interpolation
        if (typeProcessInterpolation == 2) {
            m = (Math.log(finalDataExtractionInterpolationValue) - Math.log(initialDataExtractionInterpolationValue)) / ((Math.log(numberYearsInterpolationValue) - Math.log(1)));
            b = Math.exp((-1 * m * Math.log(1)) + Math.log(initialDataExtractionInterpolationValue));

            for (let index = 1; index <= numberYearsInterpolationValue; index++) {
                $('#intakeECTAG').append(`<tr>
                <th class="text-center" scope="row">${index}</th>
                <td class="text-center">${(b*(Math.pow(index,m)))}</td>
              </tr>`);
            }
        }

        // Exponential interpolation
        if (typeProcessInterpolation == 3) {
            m = (Math.log(finalDataExtractionInterpolationValue) - Math.log(initialDataExtractionInterpolationValue)) / (numberYearsInterpolationValue - 0)
            b = Math.exp((-1 * m * 0) + Math.log(initialDataExtractionInterpolationValue));

            for (let index = 0; index <= numberYearsInterpolationValue; index++) {
                $('#intakeECTAG').append(`<tr>
                <th class="text-center" scope="row">${index}</th>
                <td class="text-center">${(b*(Math.exp(m*index)))}</td>
              </tr>`);
            }

        }

        for (let index = 0; index < numberYearsInterpolationValue; index++) {
            $('#intakeEITA').append(`<tr>
                  <th class="text-center" scope="col">${index+1}</th>
                  <td class="text-center" scope="col"><input type="text" class="form-control" required></td>
                  <td class="text-center" scope="col"><input type="text" class="form-control" required></td>
                  <td class="text-center" scope="col"><input type="text" class="form-control" required></td>
                  <td class="text-center" scope="col"><input type="text" class="form-control" required></td>
              </tr>`);
        }
    });

    $('#smartwizard').smartWizard("next").click(function() {
        $('#autoAdjustHeightF').css("height", "auto");
        mapid.invalidateSize();
        map.invalidateSize();
    });

    $('#intakeNIBYMI').click(function() {
        $('#intakeWEMI div').remove();
        intakeNIYMI = Number($("#intakeNIYMI").val());
        for (let index = 0; index < intakeNIYMI; index++) {
            $('#intakeWEMI').append(`<div class="form-group">
                <label class="col-sm-1 control-label">${index+1}</label>
                <div class="col-sm-11">
                    <input type="text" class="form-control" required>
                </div>
            </div>`);
        }
    });

    MathJax = {
        loader: {
            load: ['input/asciimath']
        },
        asciimath: {
            delimiters: [
                ['`math`', '`math`']
            ]
        }
    };

    $('#smartwizard').smartWizard("next").click(function() {
        $('#autoAdjustHeightF').css("height", "auto");
        map.invalidateSize();
    });

    $('#smartwizard').smartWizard({
        selected: 1,
        theme: 'dots',
        enableURLhash: false,
        autoAdjustHeight: true,
        transition: {
            animation: 'slide-horizontal', // Effect on navigation, none/fade/slide-horizontal/slide-vertical/slide-swing
        },
        toolbarSettings: {
            toolbarPosition: 'bottom', // both bottom
            toolbarButtonPosition: 'center', // both bottom
        }
    });

    $("#smartwizard").on("showStep", function(e, anchorObject, stepIndex, stepDirection) {
        if (stepIndex == 3) {
            if (catchmentPoly)
                mapDelimit.fitBounds(catchmentPoly.getBounds());
            changeFileEvent();
        }
    });
    map = L.map('map', {}).setView([4.1, -74.1], 5);
    mapDelimit = L.map('mapid').setView([4.1, -74.1], 5);
    var osm = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
    });
    var osmid = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
    });
    map.addLayer(osm);
    mapDelimit.addLayer(osmid);

    L.control.mapCenterCoord().addTo(map);

    L.control.coordinates({
        position: "bottomleft", //optional default "bootomright"
        decimals: 2, //optional default 4
        decimalSeperator: ".", //optional default "."
        labelTemplateLat: "Latitude: {y}", //optional default "Lat: {y}"
        labelTemplateLng: "Longitude: {x}", //optional default "Lng: {x}"
        enableUserInput: true, //optional default true
        useDMS: false, //optional default false
        useLatLngOrder: true, //ordering of labels, default false-> lng-lat
        markerType: L.marker, //optional default L.marker
        markerProps: {}, //optional default {},
        centerUserCoordinates: true,
        labelFormatterLng: function(lng) { return lng + " lng" }, //optional default none,
        labelFormatterLat: function(lat) { return lat + " lat" }, //optional default none      
    }).addTo(map);

    $("#validateBtn").on("click", validateCoordinateWithApi);

    if (!mapLoader) {
        mapLoader = L.control.loader().addTo(map);
    }

    mapLoader.hide();

    createEditor(editorUrl);

    var menu1Tab = document.getElementById('mapid');
    var observer2 = new MutationObserver(function() {
        if (menu1Tab.style.display != 'none') {
            mapDelimit.invalidateSize();
        }
    });
    observer2.observe(menu1Tab, { attributes: true });

});

$('#btnaddcost').click(function() {

    $('#intakeaddcost').append(`<div class="form-group">
                                    <label for="exampleInputEmail1">Costo:</label>
                                    <input type="text" class="form-control">
                                </div>`);

});

window.onbeforeunload = function() { return mxResources.get('changesLost'); };


/** 
 * Validate input file on change
 * @param {HTML} dropdown Dropdown selected element
 */
function changeFileEvent() {
    $('#intakeArea').change(function(evt) {
        var file = evt.currentTarget.files[0];
        var extension = validExtension(file);
        // Validate file's extension
        if (extension.valid) { //Valid
            console.log('Extension valid!');
            // Validate file's extension
            if (extension.extension == 'geojson') { //GeoJSON
                var readerGeoJson = new FileReader();
                readerGeoJson.onload = function(evt) {
                    var contents = evt.target.result;
                    geojson = JSON.parse(contents);
                    loadFile(geojson, file.name);
                }
                readerGeoJson.readAsText(file);
            } else { //Zip
                var reader = new FileReader();
                var filename, readShp = false,
                    readDbf = false,
                    readShx = false,
                    readPrj = false,
                    prj, coord = true;
                var prjName;
                reader.onload = function(evt) {
                    var contents = evt.target.result;
                    JSZip.loadAsync(file).then(function(zip) {
                        zip.forEach(function(relativePath, zipEntry) {
                            filename = zipEntry.name.toLocaleLowerCase();
                            if (filename.indexOf(".shp") != -1) {
                                readShp = true;
                            }
                            if (filename.indexOf(".dbf") != -1) {
                                readDbf = true;
                            }
                            if (filename.indexOf(".shx") != -1) {
                                readShx = true;
                            }
                            if (filename.indexOf(".prj") != -1) {
                                readPrj = true;
                                prjName = zipEntry.name;
                            }
                        });
                        // Valid shapefile with minimum files req
                        if (readShp && readDbf && readPrj && readShx) {
                            zip.file(prjName).async("string").then(function(data) {
                                prj = data;
                                // Validar sistema de referencia
                                if (!prj) {
                                    Swal.fire({
                                        icon: 'error',
                                        title: 'Error en shapefile',
                                        text: 'Sistema de proyección incorrecto',
                                    })
                                }
                                // Shapefile válido
                                else {
                                    shp(contents).then(function(shpToGeojson) {
                                        geojson = shpToGeojson;
                                        let polygonStyle = {
                                            fillColor: "#337ab7",
                                            color: "#333333",
                                            weight: 0.2,
                                            fillOpacity: 0.3
                                        };
                                        var layer = L.geoJSON(geojson, { style: polygonStyle })
                                        layer.addTo(mapDelimit);
                                        map.fitBounds(layer.getBounds())
                                            //loadShapefile(geojson, file.name);
                                    }).catch(function(e) {
                                        Swal.fire({
                                            icon: 'error',
                                            title: 'Error en shapefile',
                                            text: 'Ha ocurrido un error de lectura en el shapefile',
                                        })
                                        console.log("Ocurrió error convirtiendo el shapefile " + e);
                                    });
                                }
                            });
                        } else { // Missing req files
                            // Miss .shp
                            if (!readShp) {
                                Swal.fire({
                                    icon: 'error',
                                    title: 'Error en shapefile',
                                    text: 'Falta el archivo .shp requerido',
                                })
                            }
                            // Miss .dbf
                            if (!readDbf) {
                                Swal.fire({
                                    icon: 'error',
                                    title: 'Error en shapefile',
                                    text: 'Falta el archivo .dbf requerido',
                                })
                            }
                            // Miss .shx
                            if (!readShx) {
                                Swal.fire({
                                    icon: 'error',
                                    title: 'Error en shapefile',
                                    text: 'Falta el archivo .shx requerido',
                                })
                            }
                            // Miss .prj
                            if (!readPrj) {
                                Swal.fire({
                                    icon: 'error',
                                    title: 'Error en shapefile',
                                    text: 'Falta el archivo .prj requerido',
                                })
                            }
                        }
                    });
                };
                reader.onerror = function(event) {
                    console.error("File could not be read! Code " + event.target.error.code);
                    //alert("El archivo no pudo ser cargado: " + event.target.error.code);
                };
                reader.readAsArrayBuffer(file);
            }
        } else { //Invalid extension
            Swal.fire({
                icon: 'error',
                title: 'Error de extensión',
                text: 'La extensión del archivo no está soportada, debe ser GeoJSON o un shapefile .zip',
            })
        }
    });
}
/** 
 * Get if file has a valid shape or GeoJSON extension 
 * @param {StriFileng} file   zip or GeoJSON file
 *
 * @return {Object} extension Object contain extension and is valid
 */
function validExtension(file) {
    var fileExtension = {};
    if (file.name.lastIndexOf(".") > 0) {
        var extension = file.name.substring(file.name.lastIndexOf(".") + 1, file.name.length);
        fileExtension.extension = extension;
    }
    if (file.type == 'application/x-zip-compressed' || file.type == 'application/zip') {
        fileExtension.valid = true;
    } else if (file.type == 'application/geo+json') {
        fileExtension.valid = true;
    } else {
        fileExtension.valid = false;
    }
    return fileExtension;
}