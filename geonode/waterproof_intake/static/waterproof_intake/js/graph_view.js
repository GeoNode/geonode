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
var connection = [];
var funcostdb = [];
var bandera = true;

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

    mxGraph.prototype.isCellLocked = function(cell) {
        return (cell !== null) ? true : false;;
    }

    mxToolbar.prototype.destroy = true;

    // Enables connections in the graph and disables
    // reset of zoom and translate on root change
    // (ie. switch between XML and graphical mode).
    editor.graph.setConnectable(false);

    // Clones the source if new connection has no target
    //editor.graph.connectionHandler.setCreateTarget(true);

    var style = editor.graph.getStylesheet().getDefaultEdgeStyle();
    style[mxConstants.STYLE_ROUNDED] = true;
    style[mxConstants.STYLE_EDGE] = mxEdgeStyle.ElbowConnector;
    style[mxConstants.STYLE_STROKEWIDTH] = 4;
    style[mxConstants.STYLE_STROKECOLOR] = "#ff0000";
    style[mxConstants.STYLE_FONTSIZE] = '11';
    style[mxConstants.STYLE_ALIGN] = mxConstants.ALIGN_CENTER;
    style[mxConstants.STYLE_VERTICAL_ALIGN] = mxConstants.ALIGN_BOTTOM;


    // Installs a popupmenu handler using local function (see below).
    editor.graph.popupMenuHandler.factoryMethod = function(menu, cell, evt) {
        return createPopupMenu(editor.graph, menu, cell, evt);
    };

    // Removes cells when [DELETE] is pressed
    // elements with id == 2 is River and id==3 is CSINFRA can't remove
    var keyHandler = new mxKeyHandler(editor.graph);
    keyHandler.bindKey(46, function(evt) {
        deleteWithValidationsView(editor);
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
            label = "This connection doesn't have a defined type, \n please define a type";
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

    //Validate connections between elements
    editor.graph.getEdgeValidationError = function(edge, source, target) {
        if (source != null && target != null &&
            this.model.getValue(source) != null &&
            this.model.getValue(target) != null) {
            //water intake 
            if (source.style != 'rio' && target.style == 'bocatoma') return 'The water intake element can only receive connection from the river element';
            //floating intake
            if (source.style != 'rio' && source.style != 'reservorioagua' && source.style != 'embalse' && target.style == 'bocatomaflotante')
                return 'The floating intake element can only receive connection from the river, reservoir and water reservoir';
            //side intake
            if (source.style != 'rio' && source.style != 'reservorioagua' && source.style != 'embalse' && target.style == 'bocatomalateral')
                return 'The side intake element can only receive connection from the river, reservoir and water reservoir';
            //connection with itself
            if (source.style == target.style) return 'No element could connect to itself';
        }
        // "Supercall"
        return mxGraph.prototype.getEdgeValidationError.apply(this, arguments);
    }

    // Defines a new action to switch between
    // XML and graphical display
    var textNode = document.getElementById('xml');
    var graphNode = editor.graph.container;

    //esto va para edit :v
    xmlDoc = mxUtils.parseXml(xmlGraph)
    var dec = new mxCodec(xmlDoc);
    dec.decode(xmlDoc.documentElement, editor.graph.getModel());


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
    };


    //use jquery
    $(document).ready(function() {

        var MQ = MathQuill.getInterface(2);
        var CostSelected = null;
        var mathFieldSpan = document.getElementById('math-field');
        var latexSpan = document.getElementById('latex');
        var mathField = MQ.MathField(mathFieldSpan, {
            spaceBehavesLikeTab: true,
            handlers: {
                edit: function() {
                    latexSpan.textContent = mathField.latex();
                }
            }
        });

        //Load data from figure to html
        editor.graph.addListener(mxEvent.CLICK, function(sender, evt) {
            selectedCell = evt.getProperty('cell');
            // Clear Inputs
            if (selectedCell != undefined) clearDataHtmlView(selectedCell, evt);
            if (selectedCell != undefined) { addDataView(selectedCell, MQ); } else { clearDataHtmlView(selectedCell, evt); }
        });
    });

}