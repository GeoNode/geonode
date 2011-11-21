Ext.onReady(function() {
    var mstart = 0,
    lstart = 0,
    limit = 5,
    loadnotify = Ext.get('loading'),
    template = "<li id='item{iid}'><img class='thumb' src='{thumb}'></img>" +
    "<div class='itemButtons'><div id='toggle{iid}'></div><div id='save{iid}'></div><div id='map{iid}'></div></div>" +
    "<div class='itemTitle'><a href='{detail}'>{title}</a></div>" +
    "<div class='itemInfo'>Some kinda of data, uploaded by <a href='{owner_detail}'>{owner}</a> on {last_modified:date(\"F j, Y\")}</div>" +
    "<div class='itemAbstract>{abstract}</div>"+
    "</li>",
    fetching = false,
    list = Ext.query('#search_results ul')[0],
    store = new Ext.data.JsonStore({
        autoDestroy: true,
        storeId: 'items',
        root: 'rows',
        idProperty: 'iid',
        fields: ['title'],
        listeners: []
    }),
    selModel = null,
    dataCartStore = null;

    template = new Ext.DomHelper.createTemplate(template);
    template.compile();

    function handleSave(item) {
        window.open(item.link);
    }

    function handleSelect(button) {
        var selected = button.iconCls == 'cartAddButton';
        var clazz = selected ? 'cartRemoveButton' : 'cartAddButton';
        button.setIconClass(clazz);
        selModel.select(this.iid,selected);
    }

    function handleAddToMap(item) {
        alert("You want to add " + item.title + " to a new map. I'm afraid this is not implemented.");
    }

    function appendResults(results) {
        results = Ext.util.JSON.decode(results.responseText);
        var read = store.reader.readRecords(results);
        store.add(read.records);
        fetching = false;
        loadnotify.hide();
        mstart = results.mstart;
        lstart = results.lstart;
        var saveListeners = {
            click: handleSave
        };
        Ext.each(results.rows,function(r,i) {
            if (r.thumb == null) {
                r.thumb = "/static/theme/img/silk/map.png";
            }
            template.append(list,r);
            if (r.download_links) {
                var items = [];
                Ext.each(r.download_links,function(dl,i) {
                    items.push({
                        iconCls: dl[0],
                        text: dl[1],
                        link: dl[2],
                        listeners: saveListeners
                    });
                });
                new Ext.Button({
                    enableToggle: false,
                    renderTo: 'save' + r.iid,
                    iconCls: "saveButton",
                    menu: {
                        items: items
                    },
                    tooltip : "Save Layer As ..."
                });
            }
            if (r._type == 'layer') {
                var button = new Ext.Button({
                    renderTo: 'toggle' + r.iid,
                    iconCls: 'cartAddButton',
                    tooltip : "Add to selected data"
                });
                button.on('click',handleSelect,r);
                button = new Ext.Button({
                    renderTo: 'map' + r.iid,
                    iconCls: 'addToMapButton',
                    tooltip : "Add data to new map"
                });
                button.on('click',handleAddToMap,r,{'choad':'bar'});
            }
        });

    }

    function fetch() {
        if (fetching) return;
        if (lstart < 0 && mstart < 0) return;
        loadnotify.show();
        fetching = true;
        Ext.Ajax.request({
            // @todo URL
            url: '/maps/newsearch/api',
            method: 'GET',
            success: appendResults,
            params: {
                mstart: mstart,
                lstart: lstart,
                limit: limit
            }
        });
    }

    fetch();
    Ext.get('search_results').on('scroll',function() {
        var scroll = this.getScroll().top;
        var height = this.child('ul').getHeight();
        var view = this.getHeight();
        var perc = (scroll + view) / height;
        if ( perc > .9) {
            fetch();
        }
    });

    function toggleSection(el) {
        var expand = el.dom.classList.contains('collapse');
        var isbbox = el.dom.id == 'refine';
        if (expand) {
            if (isbbox) {
                bbox.enable();
            }
            expandSection(el);
        } else {
            collapseSection(el);
            if (isbbox) {
                bbox.disable();
            }
        }
        el.toggleClass('collapse');
        el.toggleClass('expand');
    }
    function expandSection(el) {
        el.first('.refineControls').slideIn('t',{useDisplay:true});
    }
    function collapseSection(el) {
        el.first('.refineControls').slideOut('t',{useDisplay:true});
    }
    Ext.select('.refineSection').each(function(e,i) {
        if (e.dom.classList.contains('collapse')) {
            collapseSection(e);
        }
        var h = e.first('h5');
        if (e.dom.classList.contains('refine')) {
            h.on('click',function() {
                bbox.enable();
            });
        }
        h.on('click',function(ev) {
            toggleSection(Ext.get(this).parent());
        });
    });

    // fake the grid selection model
    var SelectionModel = new Ext.extend(Ext.util.Observable, {
        grid : {
            store: store
        },
        constructor : function(config) {
            Ext.apply(this, config);
            this.addEvents('rowselect','rowdeselect')
        },
        getButton : function(el) {
            // maybe a better way to do this?
            return Ext.getCmp(el.parent('.x-btn').id);
        },
        clearSelections : function() {
            Ext.select('.cartRemoveButton').each(function(e,i) {
                this.getButton(e).setIconClass('cartAddButton');
            }, this);
        },
        selectRow : function(index, keepExisting) {
            this.getButton(Ext.get('toggle' + index)).setIconClass('cartRemoveButton');
        },
        select: function(index,selected) {
            var record = store.getAt(index);
            this.fireEvent(selected ? 'rowselect' : 'rowdeselect',this,index,record);
        }
    });

    // hacking
    selModel = new SelectionModel();
    dataCartStore = new GeoNode.DataCartStore({
        selModel : selModel
    })
    var bbox = new GeoNode.BoundingBoxWidget({
        proxy: "/proxy/?url=",
        viewerConfig: viewer_config,
        renderTo: 'refine'
    });
    var dataCart = new GeoNode.DataCart({
        store: dataCartStore,
        renderTo: 'data_cart'
    });
    var dataOps = new GeoNode.DataCartOps({
        cart: dataCart,
        renderTo: 'data_ops',

        begin_download_url: '{% url geonode.maps.views.batch_layer_download %}',
        stop_download_url: '{{site}}geoserver/rest/process/batchDownload/kill/',
        download_url: '{{site}}geoserver/rest/process/batchDownload/download/'
    });
});