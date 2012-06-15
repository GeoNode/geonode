Ext.onReady(function(){
	Ext.namespace('Search');
	Search.search = Ext.extend(Ext.util.Observable,{
		startIndex: 0,
		limit: 5,
		loadnotify: Ext.get('loading'),
		itemTemplates: {
			'layer': "<li id='item{iid}'><img class='thumb {thumbclass}' src='{thumb}'></img>" +
				"<div class='itemButtons'><div id='toggle{iid}'></div><div id='save{iid}'></div><div id='map{iid}'></div></div>" +
				"<div class='itemTitle'><a href='{detail_url}'>{title}</a></div>" +
				"<div class='itemInfo'><strong>{_display_type}</strong>, uploaded by <a href='{owner_detail}'>{owner}</a> on {last_modified:date(\"F j, Y\")}</div>" +
				"<div class='itemAbstract'>{description}</div>"+
				"</li>",
			'map': "<li id='item{iid}'><img class='thumb {thumbclass}' src='{thumb}'></img>" +
				"<div class='itemButtons'><div id='toggle{iid}'></div><div id='save{iid}'></div><div id='map{iid}'></div></div>" +
				"<div class='itemTitle'><a href='{detail_url}'>{title}</a></div>" +
				"<div class='itemInfo'><strong>{_type:capitalize}</strong>, created by <a href='{owner_detail}'>{owner}</a> on {last_modified:date(\"F j, Y\")}</div>" +
				"<div class='itemAbstract'>{description}</div>"+
				"</li>"
		},
		contactTemplate: "<li id='item{iid}'><img class='thumb {thumbclass}' src='{thumb}'></img>" +
			"<div class='itemTitle'><a href='{detail}'>{name}</a></div>" +
			"<div class='itemInfo'>User</div>" +
			"</li>",
			filterTemplate: "<div class='{typeclass}'><img height='14' src='{{ STATIC_URL }}theme/img/silk/delete.png' class='removeFilter' href='#removeFilter'> </a><strong>{type}</strong> {value}</div>",
		fetching: false,
		list: Ext.get(Ext.query('#search_results ul')[0]),
		selModel: null,
		dataCartStore: null,
		queryItems: {},
		totalQueryCount: 0,
		activateThumbs: false,
		store: new Ext.data.JsonStore({
			autoDestroy: true,
			storeId: 'items',
			root: '',
			idProperty: 'iid',
			fields: ['title','name'],
			listeners: []
		}),
		constructor: function(){
			for (var i in this.itemTemplates){
				this.itemTemplates[i] = new Ext.DomHelper.createTemplate(this.itemTemplates[i]);
				this.itemTemplates[i].compile();
			}
			this.contactTemplate = new Ext.DomHelper.createTemplate(this.contactTemplate);
			this.contactTemplate.compile();
			this.filterTemplate = new Ext.DomHelper.createTemplate(this.filterTemplate);
			this.filterTemplate.compile();
			
			this.fetch();
			
			var scrollEl = Ext.isIE ? document.body : document;
			Ext.fly(scrollEl).on('scroll',function() {
				if (this.startIndex < 0) return;
				var scroll = Ext.fly(document).getScroll().top;
				var height = this.list.getHeight() + this.list.getTop();
				var windowHeight = Ext.isIE ? document.body.clientHeight : window.innerHeight;
				if (scroll + windowHeight > height) {
					this.fetch();
				}
			},this);
		
			var SelectionModel = this.createSelModel();
			this.selModel = new SelectionModel();
			
			this.dataCartStore = new GeoNode.DataCartStore({
				selModel : this.selModel
			});
			
			this.bbox = new GeoNode.BoundingBoxWidget({
				proxy: "/proxy/?url=",
				viewerConfig: viewer_config,
				renderTo: 'refine',
				listeners: {
					'moveend': function(){alert('ciao');}
				}
			});
			this.bbox.viewer.mapPanel.map.events.register('moveend',this,function(){
				this.queryItems['bbox'] = this.bbox.viewer.mapPanel.map.getExtent().transform(new OpenLayers.Projection('EPSG:900913'),new OpenLayers.Projection('EPSG:4326')).toBBOX();
				this.reset();				
			});
			
			this.dataCart = new GeoNode.DataCart({
				store: this.dataCartStore,
				renderTo: 'data_cart'
			});
			
			this.dataOps = new GeoNode.DataCartOps({
				cart: this.dataCart,
				renderTo: 'data_ops',
				begin_download_url: '{% url layer_batch_download %}',
				stop_download_url: '{{site}}geoserver/rest/process/batchDownload/kill/',
				download_url: '{{site}}geoserver/rest/process/batchDownload/download/'
			});
			
			Ext.select('.refineSection').each(function(e,i) {
				if (e.hasClass('collapse')) {
					this.collapseSection(e);
				}
				var h = e.first('h5');		
				h.on('click',function(ev) {
					this.toggleSection(Ext.get(h).parent());
				},this);
			},this);
			
			var searchForm = Ext.get('searchForm');
			searchForm.on('submit',function(ev) {
				ev.preventDefault();
				this.queryItems['q'] = searchForm.dom.search.value;
				this.queryItems['sort'] = searchForm.dom.sortby.value;
				this.reset();
			},this);
			
			this.enableSearchLink('#bytype a','type',false);
			this.enableSearchLink('#bykeyword a','kw',true);
		},
		createSelModel: function(){
			return new Ext.extend(Ext.util.Observable, {
				grid : {
					store: this.store
				},
				constructor : function(config) {
					Ext.apply(this, config);
					this.addEvents('rowselect','rowdeselect');
				},
				getButton : function(el) {
					// maybe a better way to do this?
						return Ext.getCmp(el.id);
				},
				clearSelections : function() {
					Ext.select('.cartRemoveButton').each(function(e,i) {
						this.getButton(e.parent('.x-btn')).setIconClass('cartAddButton');
					}, this);
				},
				selectRow : function(index, keepExisting) {
					this.getButton(Ext.get('toggle' + index).child('.x-btn')).setIconClass('cartRemoveButton');
				},
				select: function(index,selected) {
					var record = this.grid.store.getAt(index);	
					this.fireEvent(selected ? 'rowselect' : 'rowdeselect',this,index,record);
				}
			});
		},
		handleSelect: function(button,el){
			var selected = button.iconCls == 'cartAddButton';
			var clazz = selected ? 'cartRemoveButton' : 'cartAddButton';
			button.setIconClass(clazz);
			this.selModel.select(button.record_iid,selected);
		},
		toggleSection: function(el){
			var expand = el.hasClass('collapse');
			var isbbox = el.dom.id == 'refine';
			if (expand) {
				if (isbbox) {
					this.bbox.enable();
				}
				this.expandSection(el);
			} else {
				this.collapseSection(el);
				if (isbbox) {
					this.bbox.disable();
				}
			}
			el.toggleClass('collapse');
			el.toggleClass('expand');
		},
		expandSection: function(el){
			el.first('.refineControls').slideIn('t',{useDisplay:true});
		},
		collapseSection: function(el){
			el.first('.refineControls').slideOut('t',{useDisplay:true});
		},
		handleSave: function(item){
			window.open(item.link);
		},
		updateDisplaying: function(){
			var cnt = this.store.getCount(),
			displaying = Ext.get('displaying'),
			note = Ext.get('displayNote');
			if (cnt === 0) {
				displaying.hide();
			} 
			else {
				if (cnt == this.totalQueryCount) {
					note.hide();
				} else {
					note.show();
				}
				displaying.dom.innerHTML = "Displaying " + cnt + " of " + this.totalQueryCount;
				displaying.show();
			}
		},
		appendResults: function(results){
			this.fetching = false;
			this.loadnotify.hide();
			results = Ext.util.JSON.decode(results.responseText);
			this.totalQueryCount = results.total;
			
			this.updateCounts(results.counts);
			this.updateCategories(results.categories);
			this.enableSearchLink('#bycategory a','cat',false);
			
			var read = this.store.reader.readRecords(results.results);
			if (read.records.length === 0) {
				if (this.startIndex === 0) {
					Ext.DomHelper.append(this.list,'<li><h4 class="center">No Results</h4></li>');
				}
				this.startIndex = -1;
				this.updateDisplaying();
				return;
			} else {
				this.startIndex += this.limit;
			}
			this.store.add(read.records);
			this.updateDisplaying();
			this.setResultItem(results);	
		},
		updateCounts: function(counts){
			counts.map ? Ext.fly('map-count').update("(" + counts.map + ")") : Ext.fly('map-count').update("(0)");
			counts.layer ? Ext.fly('layer-count').update("(" + counts.layer + ")") : Ext.fly('layer-count').update("(0)");
			counts.vector ? Ext.fly('vector-count').update("(" + counts.vector + ")") : Ext.fly('vector-count').update("(0)");
			counts.raster ? Ext.fly('raster-count').update("(" + counts.raster + ")") : Ext.fly('raster-count').update("(0)");
			counts.contact ? Ext.fly('contact-count').update("(" + counts.contact + ")") : Ext.fly('contact-count').update("(0)");
		},
		updateCategories: function(categories){
			var list = '';
			for(var i = 0; i < categories.length; i++){
				list+='<li><a href="#'+categories[i]+'">'+categories[i]+'</a></li>';
			};
			Ext.fly('bycategory').update(list);

		},
		setResultItem: function(results){
			var saveListeners = {
				click: this.handleSave
			};
			Ext.each(results.results,function(r,i){		
				if(this.activateThumbs){
					this.enableThumbs(r);
				}
				if (r._type == "contact") {
					this.contactTemplate.append(this.list, r, true);
				}				
				else {
					var item;
					
					if (r._type == 'layer'){
						item = this.itemTemplates['layer'].append(this.list,r,true);
						var button = new Ext.Button({
							renderTo: 'toggle' + r.iid,
							iconCls: 'cartAddButton',
							tooltip : "Add to selected data",
							record_iid: r.iid
						});
						button.on('click',this.handleSelect,this);
					}
					else if (r._type == 'map'){
						item = this.itemTemplates['map'].append(this.list,r,true);
					}
					if(r.thumb != null){
						var img = item.child('.thumb');
						if(!img.hasClass('missing')) {
							this.enableThumbHover(img);
						}
					}
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
						
						button = new Ext.Button({
							renderTo: 'map' + r.iid,
							iconCls: 'addToMapButton',
							tooltip : "Add data to new map",
							record_id: r.name
						});
						button.on('click',this.handleAddToMap,this);
					}
				}
			},this);
		},
		handleAddToMap:function(button,el,opt){
			this.dataOps.createNewMap([button.record_id]);
		},
		enableThumbs: function(r){
			if (r.thumb === null) {
				r.thumb = "{{ STATIC_URL }}theme/img/silk/map.png";
				r.thumbclass = "missing";
			} else {
				r.thumbclass = "";
			}
		},
		enableThumbHover: function(el){
			el.on('mouseover',function(ev) {
				var hover = Ext.get('thumbHover');
				if (hover.dom.src != el.dom.src || !hover.isVisible()) {
					hover.dom.src = el.dom.src;
					hover.setTop(el.getBottom()).
					setLeft(el.getLeft()).fadeIn();
				}
			}).on('mouseout',function() {
				Ext.get('thumbHover').slideOut();
			});
		},
		reset: function(){
			this.store.removeAll(false);
			this.list.select('li').remove();
			this.startIndex = 0;
			this.fetch();
		},
		fetch: function(){
			if (this.fetching) return;
			if (this.startIndex < 0) return;
			this.loadnotify.show();
			this.fetching = true;
			var params = Ext.apply({
				startIndex: this.startIndex,
				limit: this.limit
			},this.queryItems);
			Ext.Ajax.request({
				// @todo URL
				url: '{% url search_api %}',
				method: 'GET',
				success: this.appendResults,
				params: params,
				scope: this
			});
		},
		addActiveFilter: function(typename,querykey,value,queryValue,multiple){
			var el = this.filterTemplate.append("refineSummary",{typeclass:typename.replace(' ','_'),type:typename,value:value},true);
			el.on('click',function(ev) {
				ev.preventDefault();
				el.remove();
				if (multiple) {
					this.queryItems[querykey].remove(queryValue);
					if (this.queryItems[querykey].length === 0) {
					delete this.queryItems[querykey];
					}
				} else {
					delete this.queryItems[querykey];
				}
				this.reset();
			},this);
		},
		enableSearchLink: function(selector,querykey,multiple){
			Ext.select(selector).on('click',function(ev) {
				ev.preventDefault();
				var anchor = Ext.get(ev.target),
				href =  anchor.getAttribute('href'),
				filterType,
				existing;
				if (href[0] == '#') {
					href = href.substring(1);
				} else {
			// IE...
					href = href.substring(href.indexOf("#") + 1);
				}
				if (multiple) {
					existing = this.queryItems[querykey] || [];
					existing.push(href);
					this.queryItems[querykey] = existing;
				} else {
					this.queryItems[querykey] = href;
				}
				filterType = anchor.parent('.refineSection').first('h5').dom.innerHTML;
				if (!multiple) {
					Ext.select('#refineSummary .' + filterType.replace(' ','_')).remove();
				}
				this.addActiveFilter(filterType, querykey, anchor.dom.innerHTML, href, multiple);
				this.reset();
			},this);
		},
	}); //end search
	new Search.search();
}); //end onready
