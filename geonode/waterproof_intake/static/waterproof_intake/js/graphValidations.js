const connectionsType={
    EC: {name:'Extraction connection', id:'EC', color:'#008000'},
    EI: {name:'External input', id:'EI', color:'#e6e200'},
    PL: {name:'Pipeline', id:'PL', color:'#191970'},
    CN: {name:'Connection', id:'CN', color:'#555555'},
}

function customMenuForConnectors(){

}

// Function to create the entries in the popupmenu
function createPopupMenu(graph, menu, cell, evt){

    
    if (cell != null){
        if (cell.geometry.width == 0 && cell.geometry.height == 0){
            let existEC = false; // validate just one Extraction connection type
            for (k in graph.model.cells){
                let cell = graph.model.cells[k];
                if (cell.hasOwnProperty("value") && cell.value != undefined){

                    if (typeof(cell.value) == 'string' && cell.value.indexOf("connectorType") != -1){
                        let obj = JSON.parse(cell.value);
                        if (obj.connectorType == connectionsType.EC.id){
                            existEC = true;
                            break;
                        }
                    }
                }
            }
            for (k in connectionsType){
                let type = connectionsType[k];
                if (k != connectionsType.EC.id){
                    menu.addItem(connectionsType[k].name, '', function(){
                        updateStyleLine(graph, cell, type);
                    });
                }else{
                    if (!existEC){
                        menu.addItem(connectionsType[k].name, '', function(){
                            updateStyleLine(graph, cell, type);
                        });
                    }
                }                
            }            
        }        
    }
    else{
        menu.addItem('No-Cell Item', '', function(){
            mxUtils.alert('MenuItem2');
        });
    }        
};

function updateStyleLine(graph,cell, type){
    let strokeWidth = "4";    
    let style = "strokeWidth=" + strokeWidth + ";strokeColor=" + type.color + ";";
    let value = {
        "connectorType" : type.id
    }
    value = JSON.stringify(value);
    cell.setValue(value);
    graph.model.setStyle(cell, style);    
    
}