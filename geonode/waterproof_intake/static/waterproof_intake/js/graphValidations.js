const connectionsType = {
    EC: { name: 'Extraction connection', id: 'EC', style: 'EXTRACTIONCONNECTION', funcionreference: 'EC' },
    CH: { name: 'Channel', id: 'CH', style: 'CHANNEL', funcionreference: 'C' },
    PL: { name: 'Pipeline', id: 'PL', style: 'PIPELINE', funcionreference: 'T' },
    CN: { name: 'Connection', id: 'CN', style: 'CONNECTION', funcionreference: 'CON' },
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
                `Q${idvar}`,
                `CSed${idvar}`,
                `CN${idvar}`,
                `CP${idvar}`,
                `WSed${idvar}`,
                `WN${idvar}`,
                `WP${idvar}`,
                `WSedRet${idvar}`,
                `WNRet${idvar}`,
                `WPRet${idvar}`
            ];

            $.ajax({
                url: `/intake/loadFunctionBySymbol/${type.funcionreference}`,
                success: function(result2) {
                    let external = false;
                    if (type.id == 'EI') external = true;
                    let value = {
                        "connectorType": type.id,
                        "varcost": varcost,
                        "external": external,
                        'resultdb': JSON.parse(result),
                        'name': type.name,
                        "funcost": JSON.parse(result2)
                    };

                    value = JSON.stringify(value);
                    cell.setValue(value);
                    graph.model.setStyle(cell, type.style);
                    //add data in HTML for connectors
                    if (typeof(cell.value) == "string" && cell.value.length > 0) {
                        try {
                            let obj = JSON.parse(cell.value);
                            let dbfields = obj.resultdb;
                            label = connectionsType[obj.connectorType].name;
                            $('#titleDiagram').text(connectionsType[obj.connectorType].name);
                            $('#titleCostFunSmall').text(`ID: ${cell.id} - ${connectionsType[obj.connectorType].name}`);
                            addData2HTML(dbfields, cell)
                        } catch (e) {
                            label = "";
                        }
                    }
                }
            });
        }
    });
}

function clearDataHtml() {
    $('#aguaDiagram').prop('disabled', true);
    $('#sedimentosDiagram').prop('disabled', true);
    $('#nitrogenoDiagram').prop('disabled', true);
    $('#fosforoDiagram').prop('disabled', true);
    $('#idDiagram').val('');
    $('#titleDiagram').empty();
    $('#aguaDiagram').val('');
    $('#titleCostFunSmall').empty();
    $('#sedimentosDiagram').val('');
    $('#nitrogenoDiagram').val('');
    $('#fosforoDiagram').val('');
    $('#funcostgenerate div').remove();
    $('#funcostgenerate').empty();
}

function funcost(ecuation_db, ecuation_name, index, MQ) {
    $('#funcostgenerate').append(
        `<div class="alert alert-info" role="alert" idvalue="fun_${index}" style="margin-bottom: 12px">
        <a name="glyphicon-trash" idvalue="${index}" class="alert-link close" style="opacity: 1"><span class="glyphicon glyphicon-trash text-danger" aria-hidden="true"></span></a>
        <h4>${ecuation_name}</h4><a name="glyphicon-edit" idvalue="${index}" class="alert-link close" style="opacity: 1"><span class="glyphicon glyphicon-edit" aria-hidden="true"></span></a>
        <p name="render_ecuation">${ ecuation_db }</p>
    </div>
    `);
    $('p[name=render_ecuation]').each(function() {
        MQ.StaticMath(this);
    });
}

function addData(element, MQ) {
    //add data in HTML for connectors
    if (typeof(element.value) == "string" && element.value.length > 0) {
        let obj = JSON.parse(element.value);
        let dbfields = obj.resultdb;
        label = connectionsType[obj.connectorType].name;
        $('#titleDiagram').text(connectionsType[obj.connectorType].name);
        $('#titleCostFunSmall').text(`ID: ${element.id} - ${connectionsType[obj.connectorType].name}`);
        $('#idDiagram').val(element.id);
        addData2HTML(dbfields, element)
        funcostdb = obj.funcost;
        for (let index = 0; index < funcostdb.length; index++) {
            funcost(funcostdb[index].fields.function_value, funcostdb[index].fields.function_name, index, MQ);
        }
    } else {
        $('#titleDiagram').text(element.getAttribute('name'));
        $('#titleCostFunSmall').text(`ID: ${element.id} - ${element.getAttribute('name')}`);
        $('#idDiagram').val(element.id);
        if (element.getAttribute('resultdb') == undefined && element.getAttribute('funcost') == undefined) return;
        resultdb = JSON.parse(element.getAttribute('resultdb'));
        if (element.getAttribute('name') == 'River') {
            return addData2HTML(resultdb, element);
        }
        if (element.getAttribute('funcost') == undefined) return addData2HTML(resultdb, element);
        funcostdb = JSON.parse(element.getAttribute('funcost'));
        if (resultdb.length == 0 && funcostdb.length == 0) return;
        $('#titleDiagram').text(resultdb[0].fields.categorys);
        addData2HTML(resultdb, element);
        for (let index = 0; index < funcostdb.length; index++) {
            funcost(funcostdb[index].fields.function_value, funcostdb[index].fields.function_name, index, MQ);

        }
    }

}

function addData2HTML(resultdb, cell) {
    var show = false;
    if (cell != undefined && cell.getAttribute('name') == 'River') show = true;
    if (cell != undefined && cell.getAttribute('name') == 'External Input') show = true;
    if (cell != undefined && cell.style == "EXTRACTIONCONNECTION") show = true;
    $('#aguaDiagram').prop('disabled', show);
    if (cell != undefined && cell.style == "CONNECTION") show = true;
    $('#sedimentosDiagram').prop('disabled', show);
    $('#nitrogenoDiagram').prop('disabled', show);
    $('#fosforoDiagram').prop('disabled', show);
    $('#funcostgenerate div').remove();
    $('#funcostgenerate').empty();
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
        let cells2Remove = cells.filter(cell => (cell.style != "rio") || parseInt(cell.id) > 4);
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

        } else {
            mxUtils.alert(`The River can't be Removed`);
        }
    }
}

function validationTransportedWater(editor, cell) {
    var enc = new mxCodec();
    var node = enc.encode(editor.graph.getModel());
    var connectors = [];
    var total = new Number();
    //Select all dom called mxCell
    node.querySelectorAll('mxCell').forEach(function(node) {
        //Validates if a cell is a connector
        if (typeof(cell.value) == 'string' && cell.value.length > 0) {
            //validates which connector y connected with a image
            if (node.getAttribute('source') == cell.source.id) {
                let celda = JSON.parse(node.getAttribute('value'));
                let dbfields = JSON.parse(celda.resultdb);
                connectors.push({
                    'id': node.id,
                    'source': node.getAttribute('source'),
                    'target': node.getAttribute('target'),
                    'water': dbfields[0].fields.predefined_transp_water_perc
                });
            }
        }
    });
    //Get sumatory % Transported water of all connectors
    connectors.forEach(function(dot) {
        total += parseInt(dot.water);
    });
    //Select all dom of the elements called Simboll
    node.querySelectorAll('Symbol').forEach(function(cellfilter) {
        if (node.id == "" && connectors.length > 0) {
            //Validates connectors that are connected with the symbol
            if (cellfilter.id == connectors[0].source) {
                let cells = JSON.parse(cellfilter.getAttribute('resultdb'));
                //Validates sumatory of connectors it's less than %Transported water of the Symbol
                if (total > cells[0].fields.predefined_transp_water_perc) {
                    $('#aguaDiagram').val('');
                    Swal.fire({
                        icon: 'warning',
                        title: `La suma de % de agua transportada de los conectores Salientes de ${cellfilter.getAttribute('label')} no puede ser mayor a ${cells[0].fields.predefined_transp_water_perc}%`,
                        text: `La suma de % de agua transportada de los conectores es ${total}%`
                    })
                }
            }
        }
    });
}

$(document).on('click', '#helpgraph', function() {
    $('#HelpModal').modal('show');
});

var validateinput = function(e) {
    var t = e.value;
    e.value = (t.indexOf(".") >= 0) ? (t.substr(0, t.indexOf(".")) + t.substr(t.indexOf("."), 3)) : t;
    if (parseFloat(e.value) < parseFloat(e.getAttribute('min'))) {
        e.value = e.getAttribute('min');
        Swal.fire({
            icon: 'warning',
            title: `The value must be between ${e.getAttribute('min')} and ${e.getAttribute('max')}`,
            text: `The minimun value is ${e.getAttribute('min')} please use the arrows`
        });
    }
    if (parseFloat(e.value) > parseFloat(e.getAttribute('max'))) {
        e.value = e.getAttribute('max');
        Swal.fire({
            icon: 'warning',
            title: `The value must be between ${e.getAttribute('min')} and ${e.getAttribute('max')}`,
            text: `The maximum value is ${e.getAttribute('max')} please use the arrows`
        });
    }
}

function validationsCsinfraExternal(valida) {
    message = [];
    let symbols = [];
    let mxcell = [];
    valida.querySelectorAll('Symbol').forEach((node) => symbols.push(node.getAttribute('name')));
    if (symbols.includes("CSINFRA") == false) message.push('(Case Study Infrastructure)');
    valida.querySelectorAll('mxCell').forEach((node) => mxcell.push(node.getAttribute('style')));
    if (mxcell.includes("EXTRACTIONCONNECTION") == false) message.push('(Extraction Connection)');
    if (message[1] == undefined) message[1] = "";
    if (message[0] == undefined) return;
    $('#hideCostFuntion').hide();
    Swal.fire({
        icon: 'warning',
        title: `Missing elements`,
        text: `No exist ${message[0]} ${message[1]} in a diagram`
    });
    return true;
}

function validationsNodeAlone(data) {
    let data2 = [];
    data2 = Object.values(data.cells);
    data2.splice(0, 2);
    for (const fin of data2) {
        if (typeof(fin.value) != "string" && fin.edges == null && fin.style != 'rio') {
            mensajeAlert(fin);
            return true;
        } else {
            if (typeof(fin.value) != "string" && fin.edges.length == 0 && fin.style != 'rio' && fin.style != 'externalinput') {
                mensajeAlert(fin);
                return true;
            }
            if (typeof(fin.value) != "string" && fin.edges.length == 1 && fin.style != 'rio' && fin.style != 'externalinput') {
                if (fin.id == fin.edges[0].source.id) {
                    mensajeAlert(fin);
                    return true;
                }
            }
        }
    }
}

function mensajeAlert(fin) {
    Swal.fire({
        icon: 'warning',
        title: `Disconnected elements`,
        text: `Element ${fin.id} - ${fin.getAttribute('name')} is disconnect`
    })
}

function validations(validate, editor) {
    return (validationsCsinfraExternal(validate) == true || validationsNodeAlone(editor) == true) ? true : false;
}


// View Intake

function addDataView(element, MQ) {
    //add data in HTML for connectors
    if (typeof(element.value) == "string" && element.value.length > 0) {
        let obj = JSON.parse(element.value);
        let dbfields = obj.resultdb;
        label = connectionsType[obj.connectorType].name;
        $('#titleDiagram').text(connectionsType[obj.connectorType].name);
        $('#titleCostFunSmall').text(`ID: ${element.id} - ${connectionsType[obj.connectorType].name}`);
        $('#idDiagram').val(element.id);
        addData2HTMLView(dbfields)
        funcostdb = obj.funcost;
        for (let index = 0; index < funcostdb.length; index++) {
            funcostView(funcostdb[index].fields.function_value, funcostdb[index].fields.function_name, index, MQ);
        }
    } else {
        $('#titleDiagram').text(element.getAttribute('name'));
        $('#titleCostFunSmall').text(`ID: ${element.id} - ${element.getAttribute('name')}`);
        $('#idDiagram').val(element.id);
        if (element.getAttribute('resultdb') == undefined && element.getAttribute('funcost') == undefined) return;
        resultdb = JSON.parse(element.getAttribute('resultdb'));
        if (element.getAttribute('name') == 'River') {
            return addData2HTMLView(resultdb);
        }
        if (element.getAttribute('funcost') == undefined) return addData2HTMLView(resultdb);
        funcostdb = JSON.parse(element.getAttribute('funcost'));
        if (resultdb.length == 0 && funcostdb.length == 0) return;
        $('#titleDiagram').text(resultdb[0].fields.categorys);
        addData2HTMLView(resultdb);
        for (let index = 0; index < funcostdb.length; index++) {
            funcostView(funcostdb[index].fields.function_value, funcostdb[index].fields.function_name, index, MQ);

        }
    }

}

function funcostView(ecuation_db, ecuation_name, index, MQ) {
    $('#funcostgenerate').append(
        `<div class="alert alert-info" role="alert" idvalue="fun_${index}" style="margin-bottom: 12px">
        <h4>${ecuation_name}</h4>
        <p name="render_ecuation">${ ecuation_db }</p>
    </div>
    `);
    $('p[name=render_ecuation]').each(function() {
        MQ.StaticMath(this);
    });
}

function clearDataHtmlView() {
    $('#aguaDiagram').prop('disabled', true);
    $('#sedimentosDiagram').prop('disabled', true);
    $('#nitrogenoDiagram').prop('disabled', true);
    $('#fosforoDiagram').prop('disabled', true);
    $('#idDiagram').val('');
    $('#titleDiagram').empty();
    $('#aguaDiagram').val('');
    $('#titleCostFunSmall').empty();
    $('#sedimentosDiagram').val('');
    $('#nitrogenoDiagram').val('');
    $('#fosforoDiagram').val('');
    $('#funcostgenerate div').remove();
    $('#funcostgenerate').empty();
}

function addData2HTMLView(resultdb) {
    var show = true;
    $('#aguaDiagram').prop('disabled', show);
    $('#sedimentosDiagram').prop('disabled', show);
    $('#nitrogenoDiagram').prop('disabled', show);
    $('#fosforoDiagram').prop('disabled', show);
    $('#funcostgenerate div').remove();
    $('#funcostgenerate').empty();
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

function deleteWithValidationsView(editor) {
    if (editor.graph.isEnabled()) {
        let cells = editor.graph.getSelectionCells();
        let cells2Remove = cells.filter(cell => (cell.style != "rio") || parseInt(cell.id) > 400);
        if (cells2Remove.length >= 0) {
            mxUtils.alert(`Isn't Editable`);
        }
    }
}