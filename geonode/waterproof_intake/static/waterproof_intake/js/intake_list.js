/**
 * @file Create form validations
 * @author Luis Saltron
 * @version 1.0
 */
$(function() {
    var table = $('#example').DataTable(
        {
            'dom': 'lrtip'
        }
    );
    var countryDropdown = $('#countryNBS');
    var currencyDropdown = $('#currencyCost');
    var transitionsDropdown = $('#riosTransition');
    var transformations = [];
    var lastClickedLayer;
    var map;
    var lyrsPolygons = [];
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
    initialize = function() {
        console.log('init event loaded');
        // Transformations widget change option event
        $('#menu-toggle').click(function(e) {
            e.preventDefault();
            $('#wrapper').toggleClass('toggled');
        });

        // show/hide div with checkbuttons 
        $("#riosTransition").change(function() {
            dato = $("#riosTransition").val();
            var data_value = $(`#selectlanduse${dato}`).attr('data-value');
            $('div[name=selectlanduse]').each(function() {
                $('div[name=selectlanduse]').css({
                    "display": "none"
                });
                $('div[name=selectlanduse]').find('input[type=checkbox]:checked').each(function(idx, input) {
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

        changeCountryEvent(countryDropdown, currencyDropdown);
        changeFileEvent();
        initMap();
    };
    /** 
     * Initialize map 
     */
    
    TILELAYER = 'http://{s}.tile.osm.org/{z}/{x}/{y}.png';
    IMAGE_LYR_URL = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}";
    HYDRO_LYR_URL = "https://tiles.arcgis.com/tiles/P3ePLMYs2RVChkJx/arcgis/rest/services/Esri_Hydro_Reference_Overlay/MapServer/tile/{z}/{y}/{x}";
    CENTER = [4.582, -74.4879];
    MAXZOOM = 11;

    initMap = function() {

        //drawPolygons();        


        map = L.map('mapidcuenca', { 
            scrollWheelZoom: false, 
            zoomControl: false, 
            photonControl: true, 
            photonControlOptions: { 
                resultsHandler: showSearchPoints, 
                selectedResultHandler : selectedResultHandler,
                placeholder: 'Search City...', 
                position: 'topleft', 
                url: SEARCH_CITY_API_URL 
            } 
        });
        let initialCoords = CENTER;
        // find in localStorage if cityCoords exist
        var cityCoords = localStorage.getItem('cityCoords');
        if (cityCoords == undefined){
            cityCoords = initialCoords;
            table.search('').draw();
        }else{
            initialCoords = JSON.parse(cityCoords);
            table.search(localStorage.getItem('city').substr(0, 5)).draw();
            try{
                $("#countryLabel").html(localStorage.getItem('country'));
                $("#cityLabel").html(localStorage.getItem('city'));
                $("#regionLabel").html(localStorage.getItem('region'));
                $("#currencyLabel").html(localStorage.getItem('currency'));
                $("#listIntakes").show();
            }catch(e){

            }

        }
        waterproof["cityCoords"] = cityCoords;

        map.setView(initialCoords, 5);

        searchPoints.addTo(map);

        var tilelayer = L.tileLayer(TILELAYER, { maxZoom: MAXZOOM, attribution: 'Data \u00a9 <a href="http://www.openstreetmap.org/copyright"> OpenStreetMap Contributors </a> Tiles \u00a9 Komoot' }).addTo(map);
        var images = L.tileLayer(IMAGE_LYR_URL);
        
        
        var hydroLyr = L.tileLayer(HYDRO_LYR_URL);

        var baseLayers = {
            OpenStreetMap: tilelayer,
            Images: images,
            /* Grayscale: gray,   */          
        };

        var overlays = {
            "Hydro (esri)": hydroLyr,
        };


        var zoomControl = new L.Control.Zoom({ position: 'topright' }).addTo(map);
        L.control.layers(baseLayers,overlays,{position: 'topleft'}).addTo(map);

        //var c = new L.Control.Coordinates();        
        //c.addTo(map);


        function onMapClick(e) {
            // c.setCoordinates(e);
        }
        map.on('click', onMapClick);
    }

    var searchPoints = L.geoJson(null, {
        onEachFeature: function(feature, layer) {
            layer.bindPopup(feature.properties.name);
        }
    });

    function showSearchPoints(geojson) {
        console.log(localStorage.getItem('city'))
        //searchPoints.writeLayers('Bogotá');
        searchPoints.clearLayers();
        let geojsonFilter = geojson.features.filter(feature => feature.properties.type == "city");
        searchPoints.addData(geojsonFilter);
        //let cityName = null
        /*if (cityCoords == undefined){
             cityName = geojsonFilter[0].properties.name;
        }else{
            cityName = localStorage.getItem('city')
        }*/
        let cityName = geojsonFilter[0].properties.name;
        console.log(geojsonFilter[0].properties.name)
        //table.search(localStorage.getItem('city').substr(0, 2)).draw();
        table.search(cityName.substr(0, 5)).draw();
        drawPolygons();        
    }

    function selectedResultHandler(feat){

        waterproof["cityCoords"] = [feat.geometry.coordinates[1], feat.geometry.coordinates[0]];
        localStorage.setItem('cityCoords', JSON.stringify(waterproof["cityCoords"]));


        searchPoints.eachLayer(function(layer){
            if (layer.feature.properties.osm_id != feat.properties.osm_id){
                layer.remove();
            }
        });
        let country = feat.properties.country;
        let cityName = feat.properties.name;
        let countryCode = feat.properties.countrycode.toLowerCase();

        $("#countryLabel").html(country);
        $("#cityLabel").html(cityName);
        localStorage.setItem('city', cityName);

        let urlAPI = '{{ SEARCH_COUNTRY_API_URL }}' + countryCode;

        $.get(urlAPI, function(data){
            //console.log(data);
            $("#regionLabel").html(data.region);
            $("#currencyLabel").html(data.currencies[0].name + " - " + data.currencies[0].symbol);
            $("#listIntakes").show();
            
            localStorage.setItem('country', country);
            localStorage.setItem('region', data.region);
            localStorage.setItem('currency', data.currencies[0].name + " - " + data.currencies[0].symbol);
        });
    }

    udpateCreateUrl = function(countryId) {
        $('#createUrl').attr('href', 'create/' + countryId)
    };
    /** 
     * Get the transformations selected
     * @param {Array} transformations transformations selected
     */
    getTransformationsSelected = function() {
        var transformations = [];
        // Obtención de valores de los check de la solución
        $('input[name=itemRT]:checked').each(function() {
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
    changeCountryEvent = function(countryDropdown, currencyDropdown) {
        // Rios transitions dropdown listener
        countryDropdown.click(function(event, params) {
            // Get load activities from urls Django parameter
            var country_id = $(this).val();
            var countryName = $(this).find(':selected').text();
            var countryCode = $(this).find(':selected').attr('data-value');
            if (params) {
                if (!params.mapClick) {
                    updateCountryMap(countryCode);
                }
            } else {
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
                success: function(result) {
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
                        success: function(result) {
                            result = JSON.parse(result);
                            $('#regionLabel').text(result[0].fields.name);

                        }
                    });
                }
            });
        });
    };
    updateCountryMap = function(countryCode) {
            map.eachLayer(function(layer) {
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

    //draw polygons
    drawPolygons = function(){
        // TODO: Next line only for test purpose
        //intakePolygons = polygons;
        
        lyrsPolygons.forEach(lyr => map.removeLayer(lyr));
        lyrsPolygons = [];

        intakePolygons.forEach(feature =>{
            let poly = feature.polygon;
            if (poly.indexOf("SRID") >= 0){
                poly = poly.split(";")[1];
            }
            lyrsPolygons.push(omnivore.wkt.parse(poly).addTo(map));
        });
    }

    menu = function(){
        $('.topnav a').click(function(){
            $('#sideNavigation').style.width = "250px";
            $("#main").style.marginLeft = "250px";
          });
    }

});