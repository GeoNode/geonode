/**
 * @file Edit form validations
 * @version 1.0
 */
$(function () {
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
    var transformations = [];
    var lastClickedLayer;
    initialize = function () {
        $('#example').DataTable();
        console.log('init event loaded');
        var dato;
        var countryDropdown = $('#countryNBS');
        var currencyDropdown = $('#currencyCost');
        var transitionsDropdown = $('#riosTransition');
        var activitiesDropdown = $('#riosActivity');
        var transformDropdown = $('#riosTransformation');
        var loadAreaChecked = $('#loadArea');

        // show/hide div with checkbuttons 
        $("#riosTransition").change(function () {
            dato = $("#riosTransition").val();
            var data_value = $(`#selectlanduse${dato}`).attr('data-value');
            $('div[name=selectlanduse]').each(function (idx, input) {
                $('div[name=selectlanduse]').css({
                    "display": "none"
                });
                var valueInput = input.getAttribute('data-value')
                if (valueInput !== dato) {
                    $(`#selectlanduse${valueInput}`).find('input[type=checkbox]:checked').each(function (idx, input) {
                        input.checked = false;
                    });
                }
            });
            if (dato == data_value) {
                $(`#selectlanduse${dato}`).css({
                    "display": "block"
                })
            }
            else {
                $('div[name=selectlanduse]').find('input[type=checkbox]:checked').each(function (idx, input) {
                    input.checked = false;
                });
            }
        });
        // Event to show or hide restricted area edition
        loadAreaChecked.click(function (e) {
            var checked = e.currentTarget.checked
            if (checked)
                $('#areas').show();
            else
                $('#areas').hide();
        });

        // Populate countries options
        // Populate currencies options
        fillCurrencyDropdown(currencyDropdown);
        fillTransitionsDropdown(transitionsDropdown);
        // Change transition dropdown event listener
        changeTransitionEvent(transitionsDropdown, activitiesDropdown);
        // Change country dropdown event listener 
        changeCountryEvent(countryDropdown, currencyDropdown);
        submitFormEvent();
        changeFileEvent();
        initMap();
    };
    submitFormEvent = function () {
        console.log('submit event loaded');
        var formData = new FormData();
        var uploadNewArea = false;
        $('#submit').on('click', function () {
            var loadAreaChecked = ('#loadArea');
            var sbnId = $('#sbnId').val();
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
            formData.append('benefitTimePorc', parseFloat($('#benefitTimePorc').val()));
            // NBS Consecution Time Total Benefits
            formData.append('totalConsecTime', $('#totalConsecTime').val());
            // NBS Maintenance Perodicity
            formData.append('maintenancePeriod', $('#maintenancePeriod').val());
            // NBS Unit Implementation Cost (US$/ha)
            formData.append('implementCost', parseFloat($('#implementCost').val()));
            // NBS Unit Maintenace Cost (US$/ha)
            formData.append('maintenanceCost', parseFloat($('#maintenanceCost').val()));
            // NBS Unit Oportunity Cost (US$/ha)
            formData.append('oportunityCost', parseFloat($('#oportunityCost').val()));
            // NBS RIOS Transformations selected
            formData.append('riosTransformation', getTransformationsSelected());

            // Validate if user want's to be upload new restricted area
            if ($('#loadArea')[0].checked) { // Upload new restricted area
                var file = $('#restrictedArea')[0].files[0];
                uploadNewArea = true;
                formData.append('uploadNewArea', uploadNewArea);
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
                        url: '/waterproof_nbs_ca/edit/',
                        data: formData,
                        cache: false,
                        processData: false,
                        contentType: false,
                        enctype: 'multipart/form-data',
                        success: function () {
                            Swal.fire(
                                'Excelente',
                                'La SBN ha sido editada con éxito',
                                'success'
                            )
                            location.href = "/waterproof_nbs_ca/"
                        },
                        error: function (xhr, errmsg, err) {
                            console.log(xhr.status + ":" + xhr.responseText)
                        }
                    });
                }
                else { // ZIP

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
                                url: '/waterproof_nbs_ca/edit/' + sbnId,
                                data: formData,
                                cache: false,
                                processData: false,
                                contentType: false,
                                enctype: 'multipart/form-data',
                                success: function () {
                                    Swal.fire(
                                        'Excelente',
                                        'La SBN ha sido editada con éxito',
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
            }
            else { // Maintain same restricted area
                // Type action for view
                formData.append('action', 'edit-nbs');
                uploadNewArea = false;
                formData.append('uploadNewArea', uploadNewArea);
                // Required session token
                formData.append('csrfmiddlewaretoken', token);
                $.ajax({
                    type: 'POST',
                    url: '/waterproof_nbs_ca/edit/' + sbnId,
                    data: formData,
                    cache: false,
                    processData: false,
                    contentType: false,
                    enctype: 'multipart/form-data',
                    success: function () {
                        Swal.fire(
                            'Excelente',
                            'La SBN ha sido editada con éxito',
                            'success'
                        )
                        setTimeout(function () { location.href = "/waterproof_nbs_ca/"; }, 1000);
                    },
                    error: function (xhr, errmsg, err) {
                        console.log(xhr.status + ":" + xhr.responseText)
                    }
                });
            }
        });
    };
    /** 
     * Validate input file on change
     *
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
            $('#countryNBS option[value=' + countryId + ']').attr('selected', true).trigger('click', { mapClick });

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
            $('#countryNBS option[data-value=' + countryCode + ']').attr('selected', true).trigger('click', { mapClick });

            lastClickedLayer = feature.target;
        }
        //map.on('click', onMapClick);
    }
    /** 
   * Get the transformations selected
   * @param {Array} transformations transformations selected
   */
    getTransformationsSelected = function () {
        var transformations = [];
        // Obtención de valores de los check de la solución
        $('input[data-value=itemRT]:checked').each(function () {
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
    };
    /** 
     * Change acitivy option based in transition selected
     * @param {HTML} transDropdown Transitions dropdown
     * @param {HTML} activDropdown Activities  dropdown
     *
     */
    changeTransitionEvent = function (transDropdown, activDropdown) {
        // Rios transitions dropdown listener
        transDropdown.change(function () {
            // Get load activities from urls Django parameter
            var transition_id = $(this).val();

            /** 
             * Get filtered activities by transition id 
             * @param {String} url   activities URL 
             * @param {Object} data  transition id  
             *
             * @return {String} activities in HTML option format
             */
            $.ajax({
                url: '/waterproof_nbs_ca/load-activityByTransition/',
                data: {
                    'transition': transition_id
                },
                success: function (result) {
                    result = JSON.parse(result);
                    // Empty before poupulate new options
                    activDropdown.empty();
                    $.each(result, function (index, activity) {
                        activDropdown.append($("<option />").val(activity.pk).text(activity.fields.name));
                    });
                    //activDropdown.val($('#' + activDropdown[0].id + ' option:first').val()).change();
                }
            });
        });
    };

    /** 
     * Populate countries options in dropdown 
     * @param {HTML} dropdown Dropdown selected element
     *
     */
    fillCountryDropdown = function (dropdown) {
        $.ajax({
            url: '/waterproof_nbs_ca/load-allCountries',
            success: function (result) {
                result = JSON.parse(result);
                $.each(result, function (index, country) {
                    dropdown.append($("<option />").val(country.pk).text(country.fields.name));
                });
                dropdown.val(countryNbs).change();
            }
        });
    };
    /** 
     * Populate currencies options in dropdown 
     * @param {HTML} dropdown Dropdown selected element
     *
     */
    fillCurrencyDropdown = function (dropdown) {
        $.ajax({
            url: '/waterproof_nbs_ca/load-allCurrencies',
            success: function (result) {
                result = JSON.parse(result);
                $.each(result, function (index, currency) {
                    dropdown.append($("<option />").val(currency.pk).text(currency.fields.code + ' (' + currency.fields.symbol + ') - ' + currency.fields.name));
                });
            }
        });
    };
    /** 
     * Populate transitions options in dropdown 
     * @param {HTML} dropdown Dropdown selected element
     *
     */
    fillTransitionsDropdown = function (dropdown) {

        dropdown.change();

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