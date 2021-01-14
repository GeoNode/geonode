const connectionsType = {
    EC: { name: 'Extraction connection', id: 'EC', style: 'Extraction_connection' },
    CH: { name: 'Channel', id: 'CH', style: 'CHANNEL' },
    PL: { name: 'Pipeline', id: 'PL', style: 'Pipeline' },
    CN: { name: 'Connection', id: 'CN', style: 'Connection' },
}

function customMenuForConnectors() {

}

// Function to create the entries in the popupmenu
function createPopupMenu(graph, menu, cell, evt) {


    if (cell != null) {
        if (cell.geometry.width == 0 && cell.geometry.height == 0) {
            if (cell.hasOwnProperty("value") && cell.value != undefined) {
                if (typeof(cell.value) == 'string' && cell.value.indexOf("connectorType") != -1) {
                    let obj = JSON.parse(cell.value);
                    if (obj.connectorType == connectionsType.EC.id) {
                        // selected edge is Extraction Connection, can't change type
                        return;
                    }
                }
            }
            let existEC = false; // validate just one Extraction connection type
            for (k in graph.model.cells) {
                let cell = graph.model.cells[k];
                if (cell.hasOwnProperty("value") && cell.value != undefined) {

                    if (typeof(cell.value) == 'string' && cell.value.indexOf("connectorType") != -1) {
                        let obj = JSON.parse(cell.value);
                        if (obj.connectorType == connectionsType.EC.id) {
                            existEC = true;
                            break;
                        }
                    }
                }
            }
            for (k in connectionsType) {
                let type = connectionsType[k];
                if (k != connectionsType.EC.id) {
                    menu.addItem(connectionsType[k].name, '', function() {
                        updateStyleLine(graph, cell, type);
                    });
                } else {
                    if (!existEC) {
                        menu.addItem(connectionsType[k].name, '', function() {
                            updateStyleLine(graph, cell, type);
                        });
                    }
                }
            }
        }
    } else {
        menu.addItem('No-Cell Item', '', function() {
            mxUtils.alert('MenuItem2');
        });
    }
};

function updateStyleLine(graph, cell, type) {
    $.ajax({
        url: `/intake/loadProcess/${type.style}`,
        success: function(result) {
            let idvar = cell.id;
            let varcost = [
                `Q_${idvar}`,
                `CSed_${idvar}`,
                `CN_${idvar}`,
                `CP_${idvar}`,
                `WSed_${idvar}`,
                `WN_${idvar}`,
                `WP_${idvar}`,
                `WSed_ret_${idvar}`,
                `WN_ret_${idvar}`,
                `WP_ret_${idvar}`
            ];

            let external = false;
            if (type.id == 'EI') external = true;
            let value = {
                "connectorType": type.id,
                "varcost": varcost,
                "external": external,
                'resultdb': result,
                'name': type.name
            };
            value = JSON.stringify(value);
            cell.setValue(value);
            graph.model.setStyle(cell, type.style);

            //add data in HTML for connectors
            if (typeof(cell.value) == "string" && cell.value.length > 0) {
                try {
                    let obj = JSON.parse(cell.value);
                    let dbfields = JSON.parse(obj.resultdb);
                    label = connectionsType[obj.connectorType].name;
                    $('#titleDiagram').text(connectionsType[obj.connectorType].name);

                    // Add Value to Panel Information Right on HTML
                    $('#aguaDiagram').val(dbfields[0].fields.predefined_transp_water_perc);
                    $('#sedimentosDiagram').val(dbfields[0].fields.predefined_sediment_perc);
                    $('#nitrogenoDiagram').val(dbfields[0].fields.predefined_nitrogen_perc);
                    $('#fosforoDiagram').val(dbfields[0].fields.predefined_phosphorus_perc);
                    // Add Validator 
                    $('#aguaDiagram').attr('min', dbfields[0].fields.minimal_transp_water_perc);
                    $('#aguaDiagram').attr('max', dbfields[0].fields.maximal_transp_water_perc);
                    $('#sedimentosDiagram').attr('min', dbfields[0].fields.minimal_sediment_perc);
                    $('#sedimentosDiagram').attr('max', dbfields[0].fields.maximal_sediment_perc);
                    $('#nitrogenoDiagram').attr('min', dbfields[0].fields.minimal_nitrogen_perc);
                    $('#nitrogenoDiagram').attr('max', dbfields[0].fields.maximal_nitrogen_perc);
                    $('#fosforoDiagram').attr('min', dbfields[0].fields.minimal_phosphorus_perc);
                    $('#fosforoDiagram').attr('max', dbfields[0].fields.maximal_phosphorus_perc);
                } catch (e) {
                    label = "";
                }
            }
        }
    });
}

function clearDataHtml(cell, evt) {
    $('#idDiagram').empty();
    $('#titleDiagram').empty();
    $('#aguaDiagram').val('');
    $('#sedimentosDiagram').val('');
    $('#nitrogenoDiagram').val('');
    $('#fosforoDiagram').val('');
    cell = evt.getProperty("cell");
    var show = false;
    if (cell.getAttribute('name') == 'River') show = true;
    $('#aguaDiagram').prop('disabled', show);
    $('#sedimentosDiagram').prop('disabled', show);
    $('#nitrogenoDiagram').prop('disabled', show);
    $('#fosforoDiagram').prop('disabled', show);

}

function addData(element) {
    //add data in HTML for connectors
    if (typeof(element.value) == "string" && element.value.length > 0) {
        let obj = JSON.parse(element.value);
        let dbfields = JSON.parse(obj.resultdb);
        label = connectionsType[obj.connectorType].name;
        $('#titleDiagram').text(connectionsType[obj.connectorType].name);

        // Add Value to Panel Information Right on HTML
        $('#aguaDiagram').val(dbfields[0].fields.predefined_transp_water_perc);
        $('#sedimentosDiagram').val(dbfields[0].fields.predefined_sediment_perc);
        $('#nitrogenoDiagram').val(dbfields[0].fields.predefined_nitrogen_perc);
        $('#fosforoDiagram').val(dbfields[0].fields.predefined_phosphorus_perc);
        // Add Validator 
        $('#aguaDiagram').attr('min', dbfields[0].fields.minimal_transp_water_perc);
        $('#aguaDiagram').attr('max', dbfields[0].fields.maximal_transp_water_perc);
        $('#sedimentosDiagram').attr('min', dbfields[0].fields.minimal_sediment_perc);
        $('#sedimentosDiagram').attr('max', dbfields[0].fields.maximal_sediment_perc);
        $('#nitrogenoDiagram').attr('min', dbfields[0].fields.minimal_nitrogen_perc);
        $('#nitrogenoDiagram').attr('max', dbfields[0].fields.maximal_nitrogen_perc);
        $('#fosforoDiagram').attr('min', dbfields[0].fields.minimal_phosphorus_perc);
        $('#fosforoDiagram').attr('max', dbfields[0].fields.maximal_phosphorus_perc);

    }
    $('#titleDiagram').text(element.getAttribute('name'));
    $('#idDiagram').val(element.id);
    if (element.getAttribute('resultdb') == undefined) return;
    resultdb = JSON.parse(element.getAttribute('resultdb'));
    if (resultdb.length == 0) return;
    $('#titleDiagram').text(resultdb[0].fields.categorys);

    // Add Value to Panel Information Right on HTML
    $('#aguaDiagram').val(resultdb[0].fields.predefined_transp_water_perc);
    $('#sedimentosDiagram').val(resultdb[0].fields.predefined_sediment_perc);
    $('#nitrogenoDiagram').val(resultdb[0].fields.predefined_nitrogen_perc);
    $('#fosforoDiagram').val(resultdb[0].fields.predefined_phosphorus_perc);
    // Add Validator 
    $('#aguaDiagram').attr('min', resultdb[0].fields.minimal_transp_water_perc);
    $('#aguaDiagram').attr('max', resultdb[0].fields.maximal_transp_water_perc);
    $('#sedimentosDiagram').attr('min', resultdb[0].fields.minimal_sediment_perc);
    $('#sedimentosDiagram').attr('max', resultdb[0].fields.maximal_sediment_perc);
    $('#nitrogenoDiagram').attr('min', resultdb[0].fields.minimal_nitrogen_perc);
    $('#nitrogenoDiagram').attr('max', resultdb[0].fields.maximal_nitrogen_perc);
    $('#fosforoDiagram').attr('min', resultdb[0].fields.minimal_phosphorus_perc);
    $('#fosforoDiagram').attr('max', resultdb[0].fields.maximal_phosphorus_perc);

}

function deleteWithValidations(editor) {
    let msg = "Selected element is connected with Extraction connection element. Can't be deleted!";
    if (editor.graph.isEnabled()) {
        let cells = editor.graph.getSelectionCells();
        let cells2Remove = cells.filter(cell => (cell.style != "rio" &&
                cell.style != "csinfra" &&
                cell.style != connectionsType.EC.style) ||
            parseInt(cell.id) > 4);
        if (cells2Remove.length > 0) {
            let vertexIsEC = false;
            cells2Remove.filter(cell => {
                if (cell.edges != null && cell.edges.length > 0) {
                    for (let c in cell.edges) {
                        if (cell.edges[c].style == connectionsType.EC.style) {
                            vertexIsEC = true;
                            break;
                        }
                    }
                }
            });
            if (vertexIsEC) {
                mxUtils.alert(msg);
            } else {
                editor.graph.removeCells(cells2Remove);
            }

        }
    }
}