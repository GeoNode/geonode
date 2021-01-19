/**
 * @file Intake system parameter graph
 * configurations (Step 2 of create wizard)
 * @version 1.0
 */
/**  
 * Global variables for save data 
 * @param {Array} resultdb   all data from DB
 * @param {Object} selectedCell  cell selected from Diagram 
 */

var resultdb = [];
var selectedCell;
var graphData = [];

// Program starts here. The document.onLoad executes the
// createEditor function with a given configuration.
// In the config file, the mxEditor.onInit method is
// overridden to invoke this global function as the
// last step in the editor constructor.
function onInit(editor) {
    // Enables rotation handle
    mxVertexHandler.prototype.rotationEnabled = false;

    // Enables guides
    mxGraphHandler.prototype.guidesEnabled = false;

    // Alt disables guides
    mxGuide.prototype.isEnabledForEvent = function(evt) {
        return !mxEvent.isAltDown(evt);
    };

    // Enables snapping waypoints to terminals
    mxEdgeHandler.prototype.snapToTerminals = true;

    // Defines an icon for creating new connections in the connection handler.
    // This will automatically disable the highlighting of the source vertex.
    mxConnectionHandler.prototype.connectImage = new mxImage('/static/mxgraph/images/connector.gif', 16, 16);

    // Enables connections in the graph and disables
    // reset of zoom and translate on root change
    // (ie. switch between XML and graphical mode).
    editor.graph.setConnectable(true);

    // Clones the source if new connection has no target
    //editor.graph.connectionHandler.setCreateTarget(true);

    var style = editor.graph.getStylesheet().getDefaultEdgeStyle();
    style[mxConstants.STYLE_ROUNDED] = true;
    style[mxConstants.STYLE_EDGE] = mxEdgeStyle.ElbowConnector;
    style[mxConstants.STYLE_STROKEWIDTH] = 4;
    style[mxConstants.STYLE_STROKECOLOR] = "#ff0000";
    style[mxConstants.STYLE_FONTSIZE] = '11';
    style[mxConstants.STYLE_ALIGN] = mxConstants.ALIGN_CENTER;
    style[mxConstants.STYLE_VERTICAL_ALIGN] = mxConstants.ALIGN_MIDDLE;


    // Installs a popupmenu handler using local function (see below).
    editor.graph.popupMenuHandler.factoryMethod = function(menu, cell, evt) {
        return createPopupMenu(editor.graph, menu, cell, evt);
    };

    // Removes cells when [DELETE] is pressed
    // elements with id == 2 is River and id==3 is CSINFRA can't remove
    var keyHandler = new mxKeyHandler(editor.graph);
    keyHandler.bindKey(46, function(evt) {
        deleteWithValidations(editor);
    });

    editor.graph.setAllowDanglingEdges(false);
    editor.graph.setMultigraph(false);

    var listener = function(sender, evt) {
        editor.graph.validateGraph();
    };

    editor.graph.getLabel = function(cell) {
        var label = (this.labelsVisible) ? this.convertValueToString(cell) : '';
        var geometry = this.model.getGeometry(cell);

        if (geometry != null && geometry.width == 0) {
            var style = this.getCellStyle(cell);
            var fontSize = style[mxConstants.STYLE_FONTSIZE] || mxConstants.DEFAULT_FONTSIZE;
        }
        if (label == undefined) {
            if (typeof(cell.value) == "string" && cell.value.length > 0) {
                try {
                    let obj = JSON.parse(cell.value);
                    label = connectionsType[obj.connectorType].name + " (" + cell.id + ")";
                } catch (e) {
                    label = "";
                }
            }
        }
        return label;
    };

    editor.graph.addListener(mxEvent.CELLS_ADDED, function(sender, evt) {
        //return;

        let cell = evt.properties.cells[0];
        if (cell.value != undefined && typeof(cell.value) == "object") {
            let lbl = cell.getAttribute("label");
            cell.setAttribute("label", lbl + " (" + cell.id + ")");
            editor.graph.model.setValue(cell, cell.value);
        }
    });

    editor.graph.getModel().addListener(mxEvent.CHANGE, listener);

    // Updates the title if the root changes
    var title = document.getElementById('title');

    if (title != null) {
        var f = function(sender) {
            title.innerHTML = sender.getTitle();
        };

        editor.addListener(mxEvent.ROOT, f);
        f(editor);
    }

    // Changes the zoom on mouseWheel events
    /* mxEvent.addMouseWheelListener(function (evt, up) {
       if (!mxEvent.isConsumed(evt)) {
         if (up) {
           editor.execute('zoomIn');
         }
         else {
           editor.execute('zoomOut');
         }
 
         mxEvent.consume(evt);
       }
     });*/

    // Defines a new action to switch between
    // XML and graphical display
    var textNode = document.getElementById('xml');
    var graphNode = editor.graph.container;
    var parent = editor.graph.getDefaultParent();
    var xmlDocument = mxUtils.createXmlDocument();
    var sourceNode = xmlDocument.createElement('Symbol');
    var sourceNode1 = xmlDocument.createElement('Symbol');


    //Create River at the beginning of the diagram
    var river = editor.graph.insertVertex(parent, null, sourceNode1, 40, 30, 60, 92);
    river.setAttribute('name', 'River');
    river.setAttribute('label', 'River (2)');
    river.setAttribute('externalData', 'false');
    editor.graph.model.setStyle(river, 'rio');
    var temp = [];
    temp.push(
        `Q_${river.id}`,
        `CSed_${river.id}`,
        `CN_${river.id}`,
        `CP_${river.id}`,
        `WSed_${river.id}`,
        `WN_${river.id}`,
        `WP_${river.id}`,
        `WSed_ret_${river.id}`,
        `WN_ret_${river.id}`,
        `WP_ret_${river.id}`
    );

    $.ajax({
        url: `/intake/loadProcess/RIVER`,
        success: function(result) {
            river.setAttribute('varcost', JSON.stringify(temp));
            river.setAttribute('resultdb', result);
        }
    });

    //Create CSINFRA at the beginning of the diagram
    var vertex = editor.graph.insertVertex(parent, null, sourceNode, 500, 30, 60, 92);
    vertex.setAttribute('name', 'CSINFRA');
    vertex.setAttribute('label', 'CS Infra (3)');
    vertex.setAttribute('externalData', 'false');
    editor.graph.model.setStyle(vertex, 'csinfra');
    var temp2 = [];
    temp2.push(
        `Q_${vertex.id}`,
        `CSed_${vertex.id}`,
        `CN_${vertex.id}`,
        `CP_${vertex.id}`,
        `WSed_${vertex.id}`,
        `WN_${vertex.id}`,
        `WP_${vertex.id}`,
        `WSed_ret_${vertex.id}`,
        `WN_ret_${vertex.id}`,
        `WP_ret_${vertex.id}`
    );


    $.ajax({
        url: `/intake/loadProcess/CSINFRA`,
        success: function(result) {
            vertex.setAttribute('varcost', JSON.stringify(temp2));
            vertex.setAttribute('resultdb', result);
        }
    });



    var edge = editor.graph.insertEdge(parent, null, '', parent.children[0], parent.children[1]);

    $.ajax({
        url: `/intake/loadProcess/RIVER`,
        success: function(result) {
            let idvar = edge.id;
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

            let external = false;
            let value = {
                "connectorType": connectionsType.EC.id,
                "varcost": varcost,
                "external": external,
                'resultdb': result,
                'name': connectionsType.EC.name
            };

            edge.setValue(JSON.stringify(value));
            editor.graph.model.setStyle(edge, connectionsType.EC.style);

        }
    });


    // Source nodes needs 1..2 connected Targets
    editor.graph.multiplicities.push(new mxMultiplicity(
        true, 'Symbol', 'name', 'River', 1, 2, ['Symbol'],
        'Rio Must Have 1 or more Elements',
        'Source Must Connect to Target'));

    // Target needs exactly one incoming connection from Source
    editor.graph.multiplicities.push(new mxMultiplicity(
        false, 'Symbol', 'name', 'CSINFRA', 1, 1, ['Symbol'],
        'Target Must Have 1 Source',
        'Target Must Connect From Source'));

    var getdata = document.getElementById('getdata');
    getdata.checked = false;

    var funct = function(editor) {
        if (getdata.checked) {
            //console.log(getdata.checked)
            graphNode.style.display = 'none';
            textNode.style.display = 'inline';

            var enc = new mxCodec();
            var node = enc.encode(editor.graph.getModel());

            textNode.value = mxUtils.getPrettyXml(node);
            textNode.originalValue = textNode.value;
            textNode.focus();
        } else {
            graphNode.style.display = '';

            if (textNode.value != textNode.originalValue) {
                var doc = mxUtils.parseXml(textNode.value);
                var dec = new mxCodec(doc);
                dec.decode(doc.documentElement, editor.graph.getModel());
            }

            textNode.originalValue = null;

            // Makes sure nothing is selected in IE
            if (mxClient.IS_IE) {
                mxUtils.clearSelection();
            }

            textNode.style.display = 'none';

            // Moves the focus back to the graph
            editor.graph.container.focus();
        }
    };

    /* var getd = function(editor){
         graphNode.style.display = 'none';
             textNode.style.display = 'inline';

             var enc = new mxCodec();
             var node = enc.encode(editor.graph.getModel());

             textNode.value = mxUtils.getPrettyXml(node);
             textNode.originalValue = textNode.value;
             textNode.focus();
     }*/

    editor.addAction('switchView', funct);

    // Defines a new action to switch between
    // XML and graphical display
    mxEvent.addListener(getdata, 'click', function() {
        editor.execute('switchView');
    });

    // Create select actions in page
    //var node = document.getElementById('mainActions');
    var buttons = ['group', 'ungroup', 'cut', 'copy', 'paste', 'delete', 'undo', 'redo', 'print', 'show'];

    // Only adds image and SVG export if backend is available
    // NOTE: The old image export in mxEditor is not used, the urlImage is used for the new export.
    if (editor.urlImage != null) {
        // Client-side code for image export
        var exportImage = function(editor) {
            var graph = editor.graph;
            var scale = graph.view.scale;
            var bounds = graph.getGraphBounds();

            // New image export
            var xmlDoc = mxUtils.createXmlDocument();
            var root = xmlDoc.createElement('output');
            xmlDoc.appendChild(root);

            // Renders graph. Offset will be multiplied with state's scale when painting state.
            var xmlCanvas = new mxXmlCanvas2D(root);
            xmlCanvas.translate(Math.floor(1 / scale - bounds.x), Math.floor(1 / scale - bounds.y));
            xmlCanvas.scale(scale);

            var imgExport = new mxImageExport();
            imgExport.drawState(graph.getView().getState(graph.model.root), xmlCanvas);

            // Puts request data together
            var w = Math.ceil(bounds.width * scale + 2);
            var h = Math.ceil(bounds.height * scale + 2);
            var xml = mxUtils.getXml(root);

            // Requests image if request is valid
            if (w > 0 && h > 0) {
                var name = 'export.png';
                var format = 'png';
                var bg = '&bg=#FFFFFF';

                new mxXmlRequest(editor.urlImage, 'filename=' + name + '&format=' + format +
                    bg + '&w=' + w + '&h=' + h + '&xml=' + encodeURIComponent(xml)).
                simulate(document, '_blank');
            }
        };

        editor.addAction('exportImage', exportImage);

        // Client-side code for SVG export
        var exportSvg = function(editor) {
            var graph = editor.graph;
            var scale = graph.view.scale;
            var bounds = graph.getGraphBounds();

            // Prepares SVG document that holds the output
            var svgDoc = mxUtils.createXmlDocument();
            var root = (svgDoc.createElementNS != null) ?
                svgDoc.createElementNS(mxConstants.NS_SVG, 'svg') : svgDoc.createElement('svg');

            if (root.style != null) {
                root.style.backgroundColor = '#FFFFFF';
            } else {
                root.setAttribute('style', 'background-color:#FFFFFF');
            }

            if (svgDoc.createElementNS == null) {
                root.setAttribute('xmlns', mxConstants.NS_SVG);
            }

            root.setAttribute('width', Math.ceil(bounds.width * scale + 2) + 'px');
            root.setAttribute('height', Math.ceil(bounds.height * scale + 2) + 'px');
            root.setAttribute('xmlns:xlink', mxConstants.NS_XLINK);
            root.setAttribute('version', '1.1');

            // Adds group for anti-aliasing via transform
            var group = (svgDoc.createElementNS != null) ?
                svgDoc.createElementNS(mxConstants.NS_SVG, 'g') : svgDoc.createElement('g');
            group.setAttribute('transform', 'translate(0.5,0.5)');
            root.appendChild(group);
            svgDoc.appendChild(root);

            // Renders graph. Offset will be multiplied with state's scale when painting state.
            var svgCanvas = new mxSvgCanvas2D(group);
            svgCanvas.translate(Math.floor(1 / scale - bounds.x), Math.floor(1 / scale - bounds.y));
            svgCanvas.scale(scale);

            var imgExport = new mxImageExport();
            imgExport.drawState(graph.getView().getState(graph.model.root), svgCanvas);

            var name = 'export.svg';
            var xml = encodeURIComponent(mxUtils.getXml(root));

            new mxXmlRequest(editor.urlEcho, 'filename=' + name + '&format=svg' + '&xml=' + xml).simulate(document, "_blank");
        };

        editor.addAction('exportSvg', exportSvg);

        buttons.push('exportImage');
        buttons.push('exportSvg');
    };

    for (var i = 0; i < buttons.length; i++) {
        var button = document.createElement('button');
        mxUtils.write(button, mxResources.get(buttons[i]));

        var factory = function(name) {
            return function() {
                editor.execute(name);
            };
        };

        mxEvent.addListener(button, 'click', factory(buttons[i]));
        //node.appendChild(button);
    }

    //use jquery
    $(document).ready(function() {

        /**
         * Button to save 
         * data on graphData
         * xml on textxml
         */

        $('#inputMathAscii').keyup(function() {
            $('#RenderingMathAscii').text(`'math' ${$(this).val()} 'math'`);
            MathJax.typeset();
        });

        $('#saveAndValideCost').click(function() {
            console.log($('#RenderingMathAscii > mjx-container > mjx-assistive-mml')[0].innerHTML)
        });

        $('#ModalAddCostBtn').click(function() {
            $('#VarCostListGroup div').remove();
            for (const index of graphData) {
                var costlabel = "";
                for (const iterator of JSON.parse(index.varcost)) {
                    costlabel += `<a value="${iterator}" class="list-group-item list-group-item-action" style="padding-top: 4px;padding-bottom: 4px;">${iterator}</a>`
                }
                $('#VarCostListGroup').append(`
                <div class="panel panel-info">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#VarCostListGroup" href="#VarCostListGroup_${index.id}">${index.id} - ${index.name}</a>
                        </h4>
                    </div>
                    <div id="VarCostListGroup_${index.id}" class="panel-collapse collapse">
                        ${costlabel}
                    </div>
                </div>
                `);
            }
        });

        function funcost(ecuation_db) {

            $('#funcostgenerate').append(
                `<div class="form-group">
                <label>Annual Operation and Maintenance Cost</label>
                <div class="input-group">
                    <input type="text" class="form-control" value="${ ecuation_db }" disabled>
                    <span class="input-group-addon edit-group-btn"><span class="glyphicon glyphicon-edit" aria-hidden="true"></span></span>
                    <span class="input-group-addon trash-group-btn"><span class="glyphicon glyphicon-trash" aria-hidden="true"></span></span>
                    </div>
            </div>`);
        }

        jQuery.fn.ForceNumericOnly =
            function() {
                return this.each(function() {
                    $(this).keydown(function(e) {
                        var key = e.charCode || e.keyCode || 0;
                        return (
                            key == 8 ||
                            key == 9 ||
                            key == 13 ||
                            key == 46 ||
                            key == 110 ||
                            key == 190 ||
                            (key >= 35 && key <= 40) ||
                            (key >= 48 && key <= 57) ||
                            (key >= 96 && key <= 105));
                    });
                });
            };

        $("#inputMathAscii").ForceNumericOnly();

        $('#saveGraph').click(function() {
            var enc = new mxCodec();
            var node = enc.encode(editor.graph.getModel());
            var textxml = mxUtils.getPrettyXml(node)
            graphData = [];
            node.querySelectorAll('Symbol').forEach(function(node) {
                graphData.push({
                    'id': node.id,
                    "name": node.getAttribute('name'),
                    'resultdb': node.getAttribute('resultdb'),
                    'varcost': node.getAttribute('varcost'),
                    'funcost': node.getAttribute('funcost'),
                    'external': node.getAttribute('externalData'),
                    'externaldata': []
                })
            });

            node.querySelectorAll('mxCell').forEach(function(node) {
                if (node.id != "") {
                    let value = Object.values(JSON.parse(node.getAttribute('value')));
                    graphData.push({
                        'id': node.id,
                        'source': node.getAttribute('source'),
                        'target': node.getAttribute('target'),
                        'varcost': JSON.stringify(value[1])
                    })
                }
            });
            //console.log(graphData);
            $('#xmlGraph').val(textxml);
            $('#graphElements').val(JSON.stringify(graphData));
            //console.log(textxml);
            // console.log(connetion);
        });

        //load data when add an object in a diagram
        editor.graph.addListener(mxEvent.ADD_CELLS, function(sender, evt) {

            var selectedCell = evt.getProperty("cells");
            var idvar = selectedCell[0].id;
            if (selectedCell != undefined) {
                var varcost = [];
                varcost.push(
                    `Q_${idvar})`,
                    `CSed_${idvar}`,
                    `CN_${idvar}`,
                    `CP_${idvar}`,
                    `WSed_${idvar}`,
                    `WN_${idvar}`,
                    `WP_${idvar}`,
                    `WSed_ret_${idvar}`,
                    `WN_ret_${idvar}`,
                    `WP_ret_${idvar}`
                );
                selectedCell[0].setAttribute('varcost', JSON.stringify(varcost));

                $.ajax({
                    url: `/intake/loadProcess/${selectedCell[0].dbreference}`,
                    success: function(result) {
                        selectedCell[0].setAttribute("resultdb", result);
                    }
                });
            }


        });



        //Load data from figure to html
        editor.graph.addListener(mxEvent.CLICK, function(sender, evt) {
            selectedCell = evt.getProperty("cell");
            // Clear Inputs
            if (selectedCell != undefined) clearDataHtml(selectedCell, evt);
            //console.log(selectedCell)
            if (selectedCell != undefined) addData(selectedCell);
            $('#funcostgenerate div').remove();
            funcost('((11126.6*text(Q)) + 30939.7)*1 + (0.24*((text(Csed) - 56)/56)) + (0.06*((text(CN) - 20)/20))');
            funcost('((11126.6*text(Q)) + 30939.7)*1 + (0.24*((text(Csed) - 56)/56)) + (0.06*((text(CN) - 20)/20))');

        });

        //Add value entered in sediments in the field resultdb
        $('#sedimentosDiagram').keyup(function() {
            if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                var obj = JSON.parse(selectedCell.value);
                let dbfields = JSON.parse(obj.resultdb);
                dbfields[0].fields.predefined_sediment_perc = $('#sedimentosDiagram').val();
                values = JSON.stringify(dbfields);
                obj.resultdb = values;
                selectedCell.setValue(JSON.stringify(obj));
            } else {
                resultdb[0].fields.predefined_sediment_perc = $('#sedimentosDiagram').val();
                selectedCell.setAttribute('resultdb', JSON.stringify(resultdb));
            }

        });

        //Add value entered in nitrogen in the field resultdb
        $('#nitrogenoDiagram').keyup(function() {
            if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                var obj = JSON.parse(selectedCell.value);
                let dbfields = JSON.parse(obj.resultdb);
                dbfields[0].fields.predefined_nitrogen_perc = $('#nitrogenoDiagram').val();
                values = JSON.stringify(dbfields);
                obj.resultdb = values;
                selectedCell.setValue(JSON.stringify(obj));
            } else {
                resultdb[0].fields.predefined_nitrogen_perc = $('#nitrogenoDiagram').val();
                selectedCell.setAttribute('resultdb', JSON.stringify(resultdb));
            }
        });

        //Add value entered in phosphorus in the field resultdb
        $('#fosforoDiagram').keyup(function() {
            if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                var obj = JSON.parse(selectedCell.value);
                let dbfields = JSON.parse(obj.resultdb);
                dbfields[0].fields.predefined_phosphorus_perc = $('#fosforoDiagram').val();
                values = JSON.stringify(dbfields);
                obj.resultdb = values;
                selectedCell.setValue(JSON.stringify(obj));
            } else {
                resultdb[0].fields.predefined_phosphorus_perc = $('#fosforoDiagram').val();
                selectedCell.setAttribute('resultdb', JSON.stringify(resultdb));
            }
        });

        //Add value entered in aguaDiagram in the field resultdb
        $('#aguaDiagram').keyup(function() {
            if (typeof(selectedCell.value) == "string" && selectedCell.value.length > 0) {
                var obj = JSON.parse(selectedCell.value);
                let dbfields = JSON.parse(obj.resultdb);
                dbfields[0].fields.predefined_transp_water_perc = $('#aguaDiagram').val();
                values = JSON.stringify(dbfields);
                obj.resultdb = values;
                selectedCell.setValue(JSON.stringify(obj));
            } else {
                resultdb[0].fields.predefined_transp_water_perc = $('#aguaDiagram').val();
                selectedCell.setAttribute('resultdb', JSON.stringify(resultdb));
            }
        });


        $('#inputMathAscii').click(function() {
            textarea_Click(this);
        });

        $(document).on('click', '.list-group-item', function() {
            addInfo(`(${$(this).attr('value')})`);
        });

        $('button[name=mathKeyBoard]').click(function() {
            addInfo($(this).attr('value'));
        });

        function addInfo(value) {
            var text = $(`#inputMathAscii`).val();
            var selectionStart = $(`#inputMathAscii`)[0].selectionStart;
            var selectionEnd = $(`#inputMathAscii`)[0].selectionEnd;
            var prefixStr = text.substring(0, selectionStart);
            var sufixStr = text.substring(selectionEnd, text.length);
            $(`#inputMathAscii`).val(`${prefixStr}${value}${sufixStr}`);
            $('#RenderingMathAscii').text(`'math' ${prefixStr}${value}${sufixStr} 'math'`);
            MathJax.typeset();
        }


    });

    function textarea_Click(e) {
        var caret = getCaretPosition(e);
        var text = e.value;
        var begin = caret - 1;
        while (begin >= 0) {
            if (text.charAt(begin) == ')') return;
            else if (text.charAt(begin) == '(') break;
            else begin--;
        }

        if (begin >= 0) {
            var end = caret;
            while (end < text.length) {
                if (text.charAt(end) == ')') break;
                else end++;
            }

            if (end < text.length)
                setSelection(begin, end, e);
        }
    }

    function getCaretPosition(textarea) {
        if (textarea.selectionStart) return textarea.selectionStart;
        else return 0;
    }

    function setSelection(begin, end, textarea) {
        if ("selectionStart" in textarea) {
            textarea.selectionStart = begin;
            textarea.selectionEnd = end + 1;
        } else if (document.selection) {
            return;
        }
    }

}