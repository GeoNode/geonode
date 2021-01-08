const connectionsType={
    EC: {name:'Extraction connection', id:'EC', style:'Extraction_connection'},
    EI: {name:'External input', id:'EI', style:'External_input'},
    PL: {name:'Pipeline', id:'PL', style:'Pipeline'},
    CN: {name:'Connection', id:'CN', style:'Connection'},
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
    let idvar = cell.id;
    let varcost = [
        `Q_${idvar} (m³)`,
        `CSed_${idvar} (mg/l)`,
        `CN_${idvar} (mg/l)`,
        `CP_${idvar} (mg/l)`,
        `WSed_${idvar} (Ton)`,
        `WN_${idvar} (Kg)`,
        `WP_${idvar} (Kg)`,
        `WSed_ret_${idvar} (Ton)`,
        `WN_ret_${idvar} (Kg)`,
        `WP_ret_${idvar} (Kg)`
    ];
    let value = {
        "connectorType": type.id,
        "varcost": varcost
    };
    value = JSON.stringify(value);
    cell.setValue(value);
    graph.model.setStyle(cell, type.style);

}

function deleteWithValidations(editor){
    let msg = "Selected element is connected with Extraction connection element. Can't be deleted!";
    if (editor.graph.isEnabled()) {
        let cells = editor.graph.getSelectionCells();
        let cells2Remove = cells.filter(cell => (cell.style != "rio" &&
                cell.style != "csinfra" &&
                cell.style != connectionsType.EC.style) ||
            parseInt(cell.id) > 4);
        if (cells2Remove.length > 0) {
            let vertexIsEC = false;
            cells2Remove.filter(cell =>{
                if (cell.edges != null && cell.edges.length > 0){
                    for (let c in cell.edges){
                        if (cell.edges[c].style == connectionsType.EC.style){
                            vertexIsEC = true;
                            break;
                        }
                    }
                }
            });
            if (vertexIsEC){
                mxUtils.alert(msg);                
            }else{
                editor.graph.removeCells(cells2Remove);
            }
            
        }
    }
}