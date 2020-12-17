/**
 * @file Create form validations
 * @author Luis Saltron
 * @version 1.0
 */
$(function() {
    initialize = function() {
        $('#example').DataTable();
        console.log('init event loaded');
        var countryDropdown = $('#countryNBS');
        var currencyDropdown = $('#currencyCost');
        var transitionsDropdown = $('#riosTransition');
        var activitiesDropdown = $('#riosActivity');
        var transformDropdown = $('#riosTransformation');
        // Transformations widget change option event
        $("#menu-toggle").click(function(e) {
            e.preventDefault();
            $("#wrapper").toggleClass("toggled");
        });
        // Populate countries options
        fillCountryDropdown(countryDropdown);
        // Populate currencies options
        fillCurrencyDropdown(currencyDropdown);
        // Populate currencies options
        fillTransitionsDropdown(transitionsDropdown);
        // Change transition dropdown event listener
        //changeTransitionEvent(transitionsDropdown, activitiesDropdown);
        // Change country dropdown event listener 
        //changeCountryEvent(countryDropdown, currencyDropdown);
        // Change transition dropdown event listener
        //changeActivityEvent(activitiesDropdown, transformDropdown);
        submitFormEvent();
        changeFileEvent();
    };
    submitFormEvent = function() {
        console.log('submit event loaded');
        var formData = new FormData();
        $('#submit').on('click', function() {
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
            formData.append('riosTransformation', $('#riosTransformation').val());
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
                    url: '/waterproof_nbs_ca/create/',
                    data: formData,
                    cache: false,
                    processData: false,
                    contentType: false,
                    enctype: 'multipart/form-data',
                    success: function() {
                        Swal.fire(
                            'Excelente',
                            'La SBN ha sido guardada con éxito',
                            'success'
                        )
                        setTimeout(function() { location.href = "/waterproof_nbs_ca/"; }, 1000);
                    },
                    error: function(xhr, errmsg, err) {
                        console.log(xhr.status + ":" + xhr.responseText)
                    }
                });
            } else { // ZIP
                var reader = new FileReader();
                reader.onload = function(evt) {
                    var contents = evt.target.result;
                    shp(contents).then(function(shpToGeojson) {
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
                            url: '/waterproof_nbs_ca/create/',
                            data: formData,
                            cache: false,
                            processData: false,
                            contentType: false,
                            enctype: 'multipart/form-data',
                            success: function() {
                                Swal.fire(
                                    'Excelente',
                                    'La SBN ha sido guardada con éxito',
                                    'success'
                                )
                                setTimeout(function() { location.href = "/waterproof_nbs_ca/"; }, 1000);
                            },
                            error: function(xhr, errmsg, err) {
                                console.log(xhr.status + ":" + xhr.responseText)
                            }
                        });
                    });
                };
                reader.onerror = function(event) {
                    console.error("File could not be read! Code " + event.target.error.code);
                    //alert("El archivo no pudo ser cargado: " + event.target.error.code);
                };
                reader.readAsArrayBuffer(file);
            }
        });
    };
    /** 
     * Validate input file on change
     *
     */
    changeFileEvent = function() {
        $('#restrictedArea').change(function(evt) {
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
                                    if (prj.toLocaleLowerCase().indexOf("gcs_wgs_1984") == -1) {
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
    };
    checkEmptyFile = function() {

    };
    /** 
     * Change currency option based in country selected
     * @param {HTML} countryDropdown    Country dropdown
     * @param {HTML} currencyDropdown   Currency  dropdown
     *
     */
    changeCountryEvent = function(countryDropdown, currencyDropdown) {
        // Rios transitions dropdown listener
        countryDropdown.change(function() {
            // Get load activities from urls Django parameter
            var country_id = $(this).val();

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
                success: function(result) {
                    result = JSON.parse(result);
                    currencyDropdown.val(result[0].pk);
                }
            });
        });
    };
    /** 
     * Change acitivy option based in transition selected
     * @param {HTML} transDropdown Transitions dropdown
     * @param {HTML} activDropdown Activities  dropdown
     *
     *
    changeTransitionEvent = function(transDropdown, activDropdown) {
        // Rios transitions dropdown listener
        transDropdown.change(function() {
            // Get load activities from urls Django parameter
            var transition_id = $(this).val();

            /** 
             * Get filtered activities by transition id 
             * @param {String} url   activities URL 
             * @param {Object} data  transition id  
             *
             * @return {String} activities in HTML option format
             *
            $.ajax({
                url: '/waterproof_nbs_ca/load-activityByTransition/',
                data: {
                    'transition': transition_id
                },
                success: function(result) {
                    result = JSON.parse(result);
                    // Empty before poupulate new options
                    activDropdown.empty();
                    $.each(result, function(index, activity) {
                        activDropdown.append($("<option />").val(activity.pk).text(activity.fields.name));
                    });
                    activDropdown.val($('#' + activDropdown[0].id + ' option:first').val()).change();
                }
            });
        });
    };
    /** 
     * Change transformation options based in activity selected
     * @param {HTML} transDropdown Transitions dropdown
     * @param {HTML} activDropdown Activities  dropdown
     *
     *
    changeActivityEvent = function(activityDropdown, transformDropdown) {
        // Rios transitions dropdown listener
        activityDropdown.change(function() {
            // Get load activities from urls Django parameter
            var activity_id = $(this).val();

            /** 
             * Get filtered activities by transition id 
             * @param {String} url   activities URL 
             * @param {Object} data  transition id  
             *
             * @return {String} activities in HTML option format
             *
            $.ajax({
                url: '/waterproof_nbs_ca/load-transformationByActivity/',
                data: {
                    'activity': activity_id
                },
                success: function(result) {
                    result = JSON.parse(result);
                    // Empty before poupulate new options
                    transformDropdown.empty();
                    $.each(result, function(index, transformation) {
                        transformDropdown.append($("<option />").val(transformation.pk).text(transformation.fields.name));
                        transformDropdown.bootstrapDualListbox('refresh');

                    });
                }
            });
        });
    };
    /** 
     * Populate countries options in dropdown 
     * @param {HTML} dropdown Dropdown selected element
     *
     */
    fillCountryDropdown = function(dropdown) {
        $.ajax({
            url: '/waterproof_nbs_ca/load-allCountries',
            success: function(result) {
                result = JSON.parse(result);
                $.each(result, function(index, country) {
                    dropdown.append($("<option />").val(country.pk).text(country.fields.name));
                });
            }
        });
    };
    /** 
     * Populate currencies options in dropdown 
     * @param {HTML} dropdown Dropdown selected element
     *
     */
    fillCurrencyDropdown = function(dropdown) {
        $.ajax({
            url: '/waterproof_nbs_ca/load-allCurrencies',
            success: function(result) {
                result = JSON.parse(result);
                $.each(result, function(index, currency) {
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
    fillTransitionsDropdown = function(dropdown) {
        $.ajax({
            url: '/waterproof_nbs_ca/load-transitions',
            success: function(result) {
                result = JSON.parse(result);
                $.each(result, function(index, transition) {
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
    validExtension = function(file) {
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
    loadFile = function(file, name) {
        console.log('Start loading file function!');
    };
    // Init 
    initialize();
});