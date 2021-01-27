var filename, readShp = false,
    readDbf = false,
    readShx = false,
    readPrj = false,
    prj, coord = true,
    prjName;
/** 
 * Get if file has a valid shape or GeoJSON extension 
 * @param {Object} file   zip or GeoJSON file
 *
 * @return {Object} extension Object contain extension and is valid
 */
function validExtension(file) {
    var fileExtension = {};
    if (file.name.lastIndexOf(".") > 0) {
        var extension = file.name.substring(file.name.lastIndexOf(".") + 1, file.name.length);
        fileExtension.extension = extension;
        if (file.type !== "") {
            if (file.type == 'application/x-zip-compressed' || file.type == 'application/zip') {
                fileExtension.valid = true;
            } else if (file.type == 'application/geo+json') {
                fileExtension.valid = true;
            } else {
                fileExtension.valid = false;
            }
        }
        else {
            if (file.extension === 'geojson') {
                fileExtension.valid = true;
            }
            else if (file.extension === 'zip') {
                fileExtension.valid = true;
            }
            else {
                fileExtension.valid = false;
            }
        }
    }
    else {
        fileExtension.valid = false;
    }
    return fileExtension;
}
function validateShapeFile(zip) {
    return new Promise((resolve, reject) => {
        let validShape = false;
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
                else {
                    console.log(prj);
                    validShape = true;
                    resolve(validShape);
                }
            });
        }
        else { // Missing req files
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
}
/** 
 * Validate GeoJSON structure in base of RFC 7946
 * & coordinates range to WSG84  
 * @param {Object} geojson   GeoJSON object
 *
 * @return {Object} extension Object contain extension and is valid
 */
function validateGeoJson(geojson) {
    if (typeof (geojson) === 'object' && geojson !== void (0)) {
        if (geojson.type) {
            if (geojson.type == 'FeatureCollection') {
                if (geojson.features && geojson.features.length > 0) {
                    geojson.features.forEach(function (feature) {
                        console.log(feature);
                    })
                }
            }
            else if (geojson.type == 'Feature') {
                if (geojson.geometry) {
                    if (geojson.geometry.type === 'Polygon') {
                        if (geojson.geometry.coordinates.length > 0) {
                            geojson.geometry.coordinates[0].forEach(function (coord) {
                                if (coord[0] >= -180 && coord[0] <= 180) {
                                    if (coord[1] >= -90 && coord[1] <= 90){
                                        
                                    }
                                }
                            })
                        }
                    }
                }
            }
        }
    }
}
