/**
 * @file Create Intake wizard step
 * validations & interactions
 * @version 1.0
 */
var urlParams = (function (url) {
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
var basinId;
var mapDelimit;
var snapMarker;
var snapMarkerMapDelimit;
var catchmentPoly;
var catchmentPolyDelimit;
var editablepolygon;
var validPolygon;
var isFile;
var delimitationFileType;
var xmlGraph;
var waterExtractionData = {};
var waterExtractionValue;
const delimitationFileEnum = {
    GEOJSON: 'geojson',
    SHP: 'shapefile'
}
const interpolationType = {
    LINEAR: 'LINEAR',
    POTENTIAL: 'POTENTIAL',
    EXPONENTIAL: 'EXPONENTIAL',
    LOGISTICS: 'LOGISTICS'
}

var mapLoader;
$(document).ready(function () {
    $("#intakeWECB").click(function () {
        $('#intakeECTAG tr').remove();
        $('#IntakeTDLE table').remove();
        $('#externalSelect option').remove();


        $('#autoAdjustHeightF').css("height", "auto");
        typeProcessInterpolation = Number($("#typeProcessInterpolation").val());
        numberYearsInterpolationValue = Number($("#numberYearsInterpolationValue").val());
        initialDataExtractionInterpolationValue = Number($("#initialDataExtractionInterpolationValue").val());
        finalDataExtractionInterpolationValue = Number($("#finalDataExtractionInterpolationValue").val());

        // Linear interpolation
        if (typeProcessInterpolation == 1) {
            waterExtractionValue = [];
            waterExtractionData.typeInterpolation = interpolationType.LINEAR;
            m = (finalDataExtractionInterpolationValue - initialDataExtractionInterpolationValue) / (numberYearsInterpolationValue - 0)
            b = (-1 * m * 0) + initialDataExtractionInterpolationValue;

            for (let index = 0; index <= numberYearsInterpolationValue; index++) {
                var yearData = {};
                yearData.year = index + 1;
                yearData.value = ((m * index) + b).toFixed(2);
                waterExtractionValue.push(yearData);
                $('#intakeECTAG').append(`<tr>
                <th class="text-center" scope="row">${index}</th>
                <td class="text-center">${((m * index) + b).toFixed(2)}</td>
              </tr>`);
            }
        }

        // Potencial interpolation
        if (typeProcessInterpolation == 2) {
            waterExtractionData.typeInterpolation = interpolationType.POTENTIAL;
            m = (Math.log(finalDataExtractionInterpolationValue) - Math.log(initialDataExtractionInterpolationValue)) / ((Math.log(numberYearsInterpolationValue + 1) - Math.log(1)));
            b = Math.exp((-1 * m * Math.log(1)) + Math.log(initialDataExtractionInterpolationValue));
            for (let index = 1; index <= numberYearsInterpolationValue + 1; index++) {
                $('#intakeECTAG').append(`<tr>
                <th class="text-center" scope="row">${index - 1}</th>
                <td class="text-center">${(b * (Math.pow(index, m))).toFixed(2)}</td>
              </tr>`);
            }
        }

        // Exponential interpolation
        if (typeProcessInterpolation == 3) {
            waterExtractionData.typeInterpolation = interpolationType.EXPONENTIAL;
            m = (Math.log(finalDataExtractionInterpolationValue) - Math.log(initialDataExtractionInterpolationValue)) / (numberYearsInterpolationValue - 0)
            b = Math.exp((-1 * m * 0) + Math.log(initialDataExtractionInterpolationValue));
            for (let index = 0; index <= numberYearsInterpolationValue; index++) {
                var yearData = {};
                yearData.year = index + 1;
                yearData.value = (b * (Math.exp(m * index)));
                $('#intakeECTAG').append(`<tr>
                <th class="text-center" scope="row">${index}</th>
                <td class="text-center">${(b * (Math.exp(m * index))).toFixed(2)}</td>
              </tr>`);
            }

        }

        // Interpolación Logistica
        if (typeProcessInterpolation == 4) {
            waterExtractionData.typeInterpolation = interpolationType.LOGISTICS;
            r = (-Math.log(0.000000001) / initialDataExtractionInterpolationValue);
            for (let index = 0; index <= numberYearsInterpolationValue; index++) {
                $('#intakeECTAG').append(`<tr>
                <th class="text-center" scope="row">${index}</th>
                <td class="text-center">${((finalDataExtractionInterpolationValue) / (1 + ((finalDataExtractionInterpolationValue / initialDataExtractionInterpolationValue) - 1) * Math.exp(-r * index))).toFixed(2)}</td>
              </tr>`);
            }
        }

        externalInput(numberYearsInterpolationValue);
        // Set object data for later persistence
        waterExtractionData.yearCount = numberYearsInterpolationValue;
        waterExtractionData.initialValue = initialDataExtractionInterpolationValue;
        waterExtractionData.finalValue = finalDataExtractionInterpolationValue;
        waterExtractionData.yearValues = waterExtractionValue;
        $('#waterExtraction').val(JSON.stringify(waterExtractionData));

    });

    function externalInput(numYear) {
        var rows = "";
        $('#externalSelect').append(`<option value="null" selected>Choose here</option>`);
        for (let p = 0; p < graphData.length; p++) {
            if (graphData[p].external == 'true') {
                $('#externalSelect').append(`
                            <option value="${graphData[p].id}">${graphData[p].id} - External Input</option>
                 `);
                rows = "";
                for (let index = 0; index <= numYear; index++) {
                    rows += (`<tr>
                                <th class="text-center" scope="col" name="year_${graphData[p].id}" year_value="${index + 1}">${index + 1}</th>
                                <td class="text-center" scope="col"><input type="text" class="form-control" name="waterVolume_${index + 1}_${graphData[p].id}"></td>
                                <td class="text-center" scope="col"><input type="text" class="form-control" name="sediment_${index + 1}_${graphData[p].id}"></td>
                                <td class="text-center" scope="col"><input type="text" class="form-control" name="nitrogen_${index + 1}_${graphData[p].id}" ></td>
                                <td class="text-center" scope="col"><input type="text" class="form-control" name="phosphorus_${index + 1}_${graphData[p].id}"></td>
                          </tr>`);
                }
                $('#IntakeTDLE').append(`
                        <table class="table" id="table_${graphData[p].id}" style="display: none">
                            <thead>
                                <tr>
                                    <th class="text-center" scope="col">Year</th>
                                    <th class="text-center" scope="col">Water Volume (m3)</th>
                                    <th class="text-center" scope="col">Sediment (Ton)</th>
                                    <th class="text-center" scope="col">Nitrogen (Kg)</th>
                                    <th class="text-center" scope="col">Phosphorus (Kg)</th>
                                </tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>    
                `);
            }

        }


    }


    $('#saveExternalData').click(function () {
        for (let id = 0; id < graphData.length; id++) {
            if (graphData[id].external) {
                graphData[id].externaldata = [];
                $(`th[name=year_${graphData[id].id}]`).each(function () {
                    graphData[id].externaldata.push({
                        "year": $(this).attr('year_value'),
                        "water": $(`input[name="waterVolume_${$(this).attr('year_value')}_${graphData[id].id}"]`).val(),
                        "sediment": $(`input[name="sediment_${$(this).attr('year_value')}_${graphData[id].id}"]`).val(),
                        "nitrogen": $(`input[name="nitrogen_${$(this).attr('year_value')}_${graphData[id].id}"]`).val(),
                        "phosphorus": $(`input[name="phosphorus_${$(this).attr('year_value')}_${graphData[id].id}"]`).val()
                    })
                });
                graphData[id].externaldata = JSON.stringify(graphData[id].externaldata);
            }
        }


        $('#graphElements').val(JSON.stringify(graphData));
    });

    $('#externalSelect').change(function () {
        for (let t = 0; t < graphData.length; t++) {
            if (graphData[t].external == 'true') {
                $(`#table_${graphData[t].id}`).css('display', 'none');
            }
        }
        $(`#table_${$('#externalSelect').val()}`).css('display', 'block');
    });

    $('#smartwizard').smartWizard("next").click(function () {
        $('#autoAdjustHeightF').css("height", "auto");
        mapDelimit.invalidateSize();
        map.invalidateSize();
    });

    $('#intakeNIBYMI').click(function () {
        $('#intakeWEMI div').remove();
        intakeNIYMI = Number($("#intakeNIYMI").val());
        for (let index = 0; index < intakeNIYMI; index++) {
            $('#intakeWEMI').append(`<div class="form-group">
                <label class="col-sm-1 control-label">${index + 1}</label>
                <div class="col-sm-11">
                    <input type="text" class="form-control">
                </div>
            </div>`);
        }
    });


    $('#smartwizard').smartWizard("next").click(function () {
        $('#autoAdjustHeightF').css("height", "auto");
        map.invalidateSize();
    });

    $('#smartwizard').smartWizard({
        selected: 0,
        theme: 'dots',
        enableURLhash: false,
        autoAdjustHeight: true,
        transition: {
            animation: 'slide-horizontal', // Effect on navigation, none/fade/slide-horizontal/slide-vertical/slide-swing
        },
        toolbarSettings: {
            toolbarPosition: 'bottom', // both bottom
            toolbarButtonPosition: 'center', // both bottom
        },
        keyboardSettings: {
            keyNavigation: false
        }
    });

    $("#smartwizard").on("showStep", function (e, anchorObject, stepIndex, stepDirection) {
        if (stepIndex == 3) {
            if (catchmentPoly)
                mapDelimit.fitBounds(catchmentPoly.getBounds());
            changeFileEvent();
        }
    });
    map = L.map('map', {}).setView([4.1, -74.1], 5);
    mapDelimit = L.map('mapid', { editable: true }).setView([4.1, -74.1], 5);
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
        labelFormatterLng: function (lng) { return lng + " lng" }, //optional default none,
        labelFormatterLat: function (lat) { return lat + " lat" }, //optional default none      
    }).addTo(map);

    $("#validateBtn").on("click", function () {
        Swal.fire({
            title: 'Delimitar punto y cuenca',
            text: "El sistema ajustará las coordenadas del punto a la captación más cercana, ¿Desea continuar?",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Ajustar punto',
            cancelButtonText: 'Cancelar',
        }).then((result) => {
            if (result.isConfirmed) {
                mapLoader = L.control.loader().addTo(map);
                validateCoordinateWithApi();
            }
        })
    });
    $('#btnDelimitArea').on("click", delimitIntakeArea)
    $('#btnValidateArea').on("click", validateIntakeArea)
    if (!mapLoader) {
        mapLoader = L.control.loader().addTo(map);
    }

    mapLoader.hide();

    createEditor(editorUrl);

    var menu1Tab = document.getElementById('mapid');
    var observer2 = new MutationObserver(function () {
        if (menu1Tab.style.display != 'none') {
            mapDelimit.invalidateSize();
        }
    });
    observer2.observe(menu1Tab, { attributes: true });

});


window.onbeforeunload = function () { return mxResources.get('changesLost'); };

/** 
 * Delimit manually the intake polygon
 */
function delimitIntakeArea() {
    isFile = false;
    var copyCoordinates = [];
    console.log('Delimiting');
    var polygonKeys = Object.keys(catchmentPoly._layers);
    var keyNamePolygon = polygonKeys[0];
    var geometryCoordinates = catchmentPoly._layers[keyNamePolygon].feature.geometry.coordinates[0];
    geometryCoordinates.forEach(function (geom) {
        var coordinates = [];
        coordinates.push(geom[1]);
        coordinates.push(geom[0]);
        copyCoordinates.push(coordinates);
    })
    editablepolygon = L.polygon(copyCoordinates, { color: 'red' });
    editablepolygon.addTo(mapDelimit)
    editablepolygon.enableEdit();
    editablepolygon.on('dblclick', L.DomEvent.stop).on('dblclick', editablepolygon.toggleEdit);
}

function validateIntakeArea() {
    var editablePolygonJson = editablepolygon.toGeoJSON();
    var intakePolygonJson = catchmentPoly.toGeoJSON();
    var pointIntakeJson=snapMarker.toGeoJSON();
    /** 
     * Get filtered activities by transition id 
     * @param {String} url   activities URL 
     * @param {Object} data  transition id  
     *
     * @return {String} activities in HTML option format
     */
    $.ajax({
        url: '/intake/validateGeometry/',
        type: 'POST',
        data: {
            'editablePolygon': JSON.stringify(editablePolygonJson),
            'intakePolygon': JSON.stringify(intakePolygonJson),
            'isFile': JSON.stringify(isFile),
            'typeDelimit': delimitationFileType
        },
        success: function (result) {
            if (!result.validPolygon) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error de Geometría',
                    text: 'El polígono editado no es válido, por favor intente de nuevo',
                })
            } else if (!result.polygonContains) {
                Swal.fire({
                    icon: 'error',
                    title: 'El polígono debe estar dentro del área de la captación',
                    text: 'El polígono editado no es válido, por favor intente de nuevo',
                })
                // Correct geometry
            } else {
                Swal.fire(
                    'Excelente',
                    'El polígono es válido y está dentro de la captación',
                    'success'
                );
                // Set original intake area geom in hidden input for posterior reading
                $('#intakeAreaPolygon').val(JSON.stringify(intakePolygonJson));
                $('#basinId').val(basinId);
                // Set delimited area geom in hidden input for posterior reading
                $('#delimitArea').val(JSON.stringify(editablePolygonJson));
                $('#pointIntake').val(JSON.stringify(pointIntakeJson));
                $('#isFile').val(JSON.stringify(isFile));
                $('#typeDelimit').val(JSON.stringify(delimitationFileType));
            }
        },
        error: function (error) {
            console.log(error);
        }
    });
}

/** 
 * Validate input file on change
 * @param {HTML} dropdown Dropdown selected element
 */
function changeFileEvent() {
    $('#intakeArea').change(function (evt) {
        var file = evt.currentTarget.files[0];
        var extension = validExtension(file);
        // Validate file's extension
        if (extension.valid) { //Valid
            console.log('Extension valid!');
            isFile = true;
            // Validate file's extension
            if (extension.extension == 'geojson') { //GeoJSON
                var readerGeoJson = new FileReader();
                readerGeoJson.onload = function (evt) {
                    var contents = evt.target.result;
                    geojson = JSON.parse(contents);
                    delimitationFileType = delimitationFileEnum.GEOJSON;
                    let polygonStyle = {
                        fillColor: "red",
                        color: "#333333",
                        weight: 0.2,
                        fillOpacity: 0.3
                    };
                    editablepolygon = L.geoJSON(geojson, { style: polygonStyle })
                    editablepolygon.addTo(mapDelimit);
                    mapDelimit.fitBounds(editablepolygon.getBounds())
                    //loadShapefile(geojson, file.name);
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
                reader.onload = function (evt) {
                    var contents = evt.target.result;
                    JSZip.loadAsync(file).then(function (zip) {
                        zip.forEach(function (relativePath, zipEntry) {
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
                            zip.file(prjName).async("string").then(function (data) {
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
                                    shp(contents).then(function (shpToGeojson) {
                                        geojson = shpToGeojson;
                                        delimitationFileType = delimitationFileEnum.SHP;
                                        let polygonStyle = {
                                            fillColor: "#337ab7",
                                            color: "#333333",
                                            weight: 0.2,
                                            fillOpacity: 0.3
                                        };
                                        editablepolygon = L.geoJSON(geojson, { style: polygonStyle })
                                        editablepolygon.addTo(mapDelimit);
                                        mapDelimit.fitBounds(editablepolygon.getBounds())
                                        //loadShapefile(geojson, file.name);
                                    }).catch(function (e) {
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
                reader.onerror = function (event) {
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