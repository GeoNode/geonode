/*
Ext JS - JavaScript Library
Copyright (c) 2006-2009, Ext JS, LLC
All rights reserved.
licensing@extjs.com

http://extjs.com/license

Open Source License
------------------------------------------------------------------------------------------
Ext is licensed under the terms of the Open Source GPL 3.0 license. 

http://www.gnu.org/licenses/gpl.html

There are several FLOSS exceptions available for use with this release for
open source applications that are distributed under a license other than the GPL.

* Open Source License Exception for Applications

  http://extjs.com/products/floss-exception.php

* Open Source License Exception for Development

  http://extjs.com/products/ux-exception.php


Commercial License
------------------------------------------------------------------------------------------
This is the appropriate option if you are creating proprietary applications and you are 
not prepared to distribute and share the source code of your application under the 
GPL v3 license. Please visit http://extjs.com/license for more details.


OEM / Reseller License
------------------------------------------------------------------------------------------
For more details, please visit: http://extjs.com/license.

--

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.
*/
Ext.grid.RowExpander=function(config){Ext.apply(this,config);this.addEvents({beforeexpand:true,expand:true,beforecollapse:true,collapse:true});Ext.grid.RowExpander.superclass.constructor.call(this);if(this.tpl){if(typeof this.tpl=='string'){this.tpl=new Ext.Template(this.tpl);}
this.tpl.compile();}
this.state={};this.bodyContent={};};Ext.extend(Ext.grid.RowExpander,Ext.util.Observable,{header:"",width:20,sortable:false,fixed:true,menuDisabled:true,dataIndex:'',id:'expander',lazyRender:true,enableCaching:true,getRowClass:function(record,rowIndex,p,ds){p.cols=p.cols-1;var content=this.bodyContent[record.id];if(!content&&!this.lazyRender){content=this.getBodyContent(record,rowIndex);}
if(content){p.body=content;}
return this.state[record.id]?'x-grid3-row-expanded':'x-grid3-row-collapsed';},init:function(grid){this.grid=grid;var view=grid.getView();view.getRowClass=this.getRowClass.createDelegate(this);view.enableRowBody=true;grid.on('render',function(){view.mainBody.on('mousedown',this.onMouseDown,this);},this);},getBodyContent:function(record,index){if(!this.enableCaching){return this.tpl.apply(record.data);}
var content=this.bodyContent[record.id];if(!content){content=this.tpl.apply(record.data);this.bodyContent[record.id]=content;}
return content;},onMouseDown:function(e,t){if(t.className=='x-grid3-row-expander'){e.stopEvent();var row=e.getTarget('.x-grid3-row');this.toggleRow(row);}},renderer:function(v,p,record){p.cellAttr='rowspan="2"';return'<div class="x-grid3-row-expander">&#160;</div>';},beforeExpand:function(record,body,rowIndex){if(this.fireEvent('beforeexpand',this,record,body,rowIndex)!==false){if(this.tpl&&this.lazyRender){body.innerHTML=this.getBodyContent(record,rowIndex);}
return true;}else{return false;}},toggleRow:function(row){if(typeof row=='number'){row=this.grid.view.getRow(row);}
this[Ext.fly(row).hasClass('x-grid3-row-collapsed')?'expandRow':'collapseRow'](row);},expandRow:function(row){if(typeof row=='number'){row=this.grid.view.getRow(row);}
var record=this.grid.store.getAt(row.rowIndex);var body=Ext.DomQuery.selectNode('tr:nth(2) div.x-grid3-row-body',row);if(this.beforeExpand(record,body,row.rowIndex)){this.state[record.id]=true;Ext.fly(row).replaceClass('x-grid3-row-collapsed','x-grid3-row-expanded');this.fireEvent('expand',this,record,body,row.rowIndex);}},collapseRow:function(row){if(typeof row=='number'){row=this.grid.view.getRow(row);}
var record=this.grid.store.getAt(row.rowIndex);var body=Ext.fly(row).child('tr:nth(1) div.x-grid3-row-body',true);if(this.fireEvent('beforecollapse',this,record,body,row.rowIndex)!==false){this.state[record.id]=false;Ext.fly(row).replaceClass('x-grid3-row-expanded','x-grid3-row-collapsed');this.fireEvent('collapse',this,record,body,row.rowIndex);}}});