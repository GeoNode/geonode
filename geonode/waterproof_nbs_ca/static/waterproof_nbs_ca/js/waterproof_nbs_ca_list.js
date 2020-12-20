/**
 * @file Create form validations
 * @author Luis Saltron
 * @version 1.0
 */
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
    // Default layer style
    var defaultStyle = {
        fillColor: "#337ab7",
        color: "#333333",
        weight: 0.2,
        fillOpacity: 0
    };
    initialize = function () {
        console.log('init event loaded');
        // Transformations widget change option event
        $('#menu-toggle').click(function (e) {
            e.preventDefault();
            $('#wrapper').toggleClass('toggled');
        });

        // show/hide div with checkbuttons 
        $("#riosTransition").change(function () {
            dato = $("#riosTransition").val();
            var data_value = $(`#selectlanduse${dato}`).attr('data-value');
            $('div[name=selectlanduse]').each(function () {
                $('div[name=selectlanduse]').css({
                    "display": "none"
                });
                $('div[name=selectlanduse]').find('input[type=checkbox]:checked').each(function (idx, input) {
                    input.checked = false;
                });
            });
            if (dato == data_value) {
                $(`#selectlanduse${dato}`).css({
                    "display": "block"
                })
            }
        });
        fillTransitionsDropdown(transitionsDropdown);
        submitFormEvent();
        changeCountryEvent(countryDropdown, currencyDropdown);
        changeFileEvent();
        initMap();
    };
    submitFormEvent = function () {
        console.log('submit event loaded');
        var formData = new FormData();
        $('#submit').on('click', function () {
            // NBS name
            formData.append('nameNBS', $('#nameNBS').val());
            // NBS description
            formData.append('descNBS', $('#descNBS').val());
            // NBS country
            formData.append('countryNBS', $('#countryNBS').val());
            // NBS currency cost
            formData.append('currencyCost', $('#currencyCost').val());
            // NBS Time required to generate maximun benefit (yr)
            formData.append('maxBenefitTime', $('#maxBenefitTime').val());
            // NBS Percentage of benefit associated with interventions at time t=0
            formData.append('benefitTimePorc', $('#benefitTimePorc').val());
            // NBS Consecution Time Total Benefits
            formData.append('totalConsecTime', $('#totalConsecTime').val());
            // NBS Maintenance Perodicity
            formData.append('maintenancePeriod', $('#maintenancePeriod').val());
            // NBS Unit Implementation Cost (US$/ha)
            formData.append('implementCost', $('#implementCost').val());
            // NBS Unit Maintenace Cost (US$/ha)
            formData.append('maintenanceCost', $('#maintenanceCost').val());
            // NBS Unit Oportunity Cost (US$/ha)
            formData.append('oportunityCost', $('#oportunityCost').val());
            // NBS RIOS Transformations selected
            formData.append('riosTransformation', getTransformationsSelected());
            var file = $('#restrictedArea')[0].files[0];
            // validate extension file
            var extension = validExtension(file);
            if (extension.extension == 'geojson') { //GeoJSON
                // Restricted area extension file
                formData.append('extension', 'geojson');
                // NBS restricted area geographic file
                formData.append('restrictedArea', $('#restrictedArea')[0].files[0]);
                // Type action for view
                formData.append('action', 'create-nbs');
                // Required session token
                formData.append('csrfmiddlewaretoken', token);
                $.ajax({
                    type: 'POST',
                    url: '/waterproof_nbs_ca/create/' + countryId,
                    data: formData,
                    cache: false,
                    processData: false,
                    contentType: false,
                    enctype: 'multipart/form-data',
                    success: function () {
                        Swal.fire(
                            'Excelente',
                            'La SBN ha sido guardada con éxito',
                            'success'
                        )
                        setTimeout(function () { location.href = "/waterproof_nbs_ca/"; }, 1000);
                    },
                    error: function (xhr, errmsg, err) {
                        console.log(xhr.status + ":" + xhr.responseText)
                    }
                });
            } else { // ZIP
                var reader = new FileReader();
                reader.onload = function (evt) {
                    var contents = evt.target.result;
                    shp(contents).then(function (shpToGeojson) {
                        var restrictedArea = JSON.stringify(shpToGeojson);
                        // Restricted area extension file
                        formData.append('extension', 'zip');
                        // NBS restricted area geographic file
                        formData.append('restrictedArea', restrictedArea);
                        // Type action for view
                        formData.append('action', 'create-nbs');
                        // Required session token
                        formData.append('csrfmiddlewaretoken', token);
                        $.ajax({
                            type: 'POST',
                            url: '/waterproof_nbs_ca/create/' + countryId,
                            data: formData,
                            cache: false,
                            processData: false,
                            contentType: false,
                            enctype: 'multipart/form-data',
                            success: function () {
                                Swal.fire(
                                    'Excelente',
                                    'La SBN ha sido guardada con éxito',
                                    'success'
                                )
                                setTimeout(function () { location.href = "/waterproof_nbs_ca/"; }, 1000);
                            },
                            error: function (xhr, errmsg, err) {
                                console.log(xhr.status + ":" + xhr.responseText)
                            }
                        });
                    });
                };
                reader.onerror = function (event) {
                    console.error("File could not be read! Code " + event.target.error.code);
                    //alert("El archivo no pudo ser cargado: " + event.target.error.code);
                };
                reader.readAsArrayBuffer(file);
            }
        });
    };
    /** 
    * Initialize map 
    */
    initMap = function () {
        map = L.map('mapid').setView([51.505, -0.09], 13);

        // Basemap layer
        L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
            maxZoom: 18,
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
                'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
            id: 'mapbox/streets-v11',
            tileSize: 512,
            zoomOffset: -1
        }).addTo(map);
        // Countries layer
        let countries = new L.GeoJSON.AJAX(countriesLayerUrl,
            {
                style: defaultStyle,
                onEachFeature: onEachFeature
            }
        );
        countries.addTo(map);

        // When countries layer is loaded fire dropdown event change
        countries.on("data:loaded", function () {
            let mapClick = false;
            // Preload selected country form list view
            updateCountryMap(userCountryCode);
            // Filter datables with country name
            table.search(userCountryName).draw();
            // Update url to create with country id parameter
            udpateCreateUrl(userCountryId);
        });

        function onEachFeature(feature, layer) {
            layer.on({
                click: updateDropdownCountry
            });
        }

        function updateDropdownCountry(feature) {
            let mapClick = true;
           
            let layerClicked = feature.target;
            if (lastClickedLayer) {
                lastClickedLayer.setStyle(defaultStyle);
            }
            layerClicked.setStyle(highlighPolygon);
            let countryCode = feature.sourceTarget.feature.id;
            
            $.ajax({
                url: '/waterproof_nbs_ca/load-countryByCode/',
                data: {
                    'code': countryCode
                },
                success: function (result) {
                    result = JSON.parse(result);
                    $('#countryLabel').text(result[0].fields.name);
                    table.search(result[0].fields.name).draw();
                    let countryId = result[0].pk;
                    udpateCreateUrl(countryId);
                    //
                    $.ajax({
                        url: '/waterproof_nbs_ca/load-regionByCountry/',
                        data: {
                            'country': countryId
                        },
                        success: function (result) {
                            result = JSON.parse(result);
                            $('#regionLabel').text(result[0].fields.name);

                        }
                    });
                    $.ajax({
                        url: '/waterproof_nbs_ca/load-currencyByCountry/',
                        data: {
                            'country': countryId
                        },
                        success: function (result) {
                            result = JSON.parse(result);
                            $('#currencyLabel').text('('+result[0].fields.code+') - '+result[0].fields.name);
                        }
                    });
                }
            });
            lastClickedLayer = feature.target;
        }
        //map.on('click', onMapClick);
    }
    udpateCreateUrl = function (countryId) {
       $('#createUrl').attr('href','create/'+countryId)
    };
    /** 
    * Get the transformations selected
    * @param {Array} transformations transformations selected
    */
    getTransformationsSelected = function () {
        var transformations = [];
        // Obtención de valores de los check de la solución
        $('input[name=itemRT]:checked').each(function () {
            transformations.push($(this).val());
        });
        return transformations;
    };
    /** 
  * Change currency option based in country selected
  * @param {HTML} countryDropdown    Country dropdown
  * @param {HTML} currencyDropdown   Currency  dropdown
  *
  */
    changeCountryEvent = function (countryDropdown, currencyDropdown) {
        // Rios transitions dropdown listener
        countryDropdown.click(function (event, params) {
            // Get load activities from urls Django parameter
            var country_id = $(this).val();
            var countryName = $(this).find(':selected').text();
            var countryCode = $(this).find(':selected').attr('data-value');
            if (params) {
                if (!params.mapClick) {
                    updateCountryMap(countryCode);
                }
            }
            else {
                updateCountryMap(countryCode);
            }
            /** 
             * Get filtered activities by transition id 
             * @param {String} url   activities URL 
             * @param {Object} data  transition id  
             *
             * @return {String} activities in HTML option format
             */
            $.ajax({
                url: '/waterproof_nbs_ca/load-currencyByCountry/',
                data: {
                    'country': country_id
                },
                success: function (result) {
                    result = JSON.parse(result);
                    currencyDropdown.val(result[0].pk);
                    $('#currencyLabel').text('(' + result[0].fields.code + ') - ' + result[0].fields.name);
                    $('#countryLabel').text(countryName);
                    /** 
                     * Get filtered activities by transition id 
                     * @param {String} url   activities URL 
                     * @param {Object} data  transition id  
                     *
                     * @return {String} activities in HTML option format
                     */
                    $.ajax({
                        url: '/waterproof_nbs_ca/load-regionByCountry/',
                        data: {
                            'country': country_id
                        },
                        success: function (result) {
                            result = JSON.parse(result);
                            $('#regionLabel').text(result[0].fields.name);

                        }
                    });
                }
            });
        });
    };
    updateCountryMap = function (countryCode) {
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
    
    }
    /** 
     * Validate input file on change
     * @param {HTML} dropdown Dropdown selected element
     */
    changeFileEvent = function () {
        $('#restrictedArea').change(function (evt) {
            var file = evt.currentTarget.files[0];
            var extension = validExtension(file);
            // Validate file's extension
            if (extension.valid) { //Valid
                console.log('Extension valid!');
                // Validate file's extension
                if (extension.extension == 'geojson') { //GeoJSON
                    var readerGeoJson = new FileReader();
                    readerGeoJson.onload = function (evt) {
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
                                    if (prj.toLocaleLowerCase().indexOf("gcs_wgs_1984") == -1) {
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
    };
    checkEmptyFile = function () {

    };
    /** 
     * Populate transitions options in dropdown 
     * @param {HTML} dropdown Dropdown selected element
     *
     */
    fillTransitionsDropdown = function (dropdown) {
        $.ajax({
            url: '/waterproof_nbs_ca/load-transitions',
            success: function (result) {
                result = JSON.parse(result);
                $.each(result, function (index, transition) {
                    dropdown.append($("<option />").val(transition.pk).text(transition.fields.name));
                });
                dropdown.val(1).change();
            }
        });
    };
    /** 
     * Get if file has a valid shape or GeoJSON extension 
     * @param {StriFileng} file   zip or GeoJSON file
     *
     * @return {Object} extension Object contain extension and is valid
     */
    validExtension = function (file) {
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
    };
    loadFile = function (file, name) {
        console.log('Start loading file function!');
    };
    // Init 
    initialize();
});