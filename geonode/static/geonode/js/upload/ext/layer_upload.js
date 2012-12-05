function setup(options) {
    Ext.onReady(function() {
        init(options);
    });
}
function init(options) {
    Ext.QuickTips.init();
    options = Ext.apply({
        is_featuretype : true,
        layer_name : null
    },options);

    var xml_unsafe = /(^[^a-zA-Z\._]+)|([^a-zA-Z0-9\._])/g;
    var layer_title;
    if (options.layer_name) {
        layer_title = new Ext.form.TextField({
            id: 'layer_name',
            name: 'layer_name',
            emptyText: options.layer_name,
            fieldLabel: gettext('Name'),
            allowBlank: true,
            disabled: true
        });
    } else {
        layer_title =  new Ext.form.TextField({
            id: 'layer_title',
            fieldLabel: gettext('Title'),
            name: 'layer_title'
        });
    }

    var listeners = {
        "fileselected": function(cmp, value) {
            // remove the path from the filename - avoids C:/fakepath etc.
            cmp.setValue(value.split(/[/\\]/).pop());
        }
    };
    var form_fields = [layer_title,{
            xtype: "hidden",
            name: "csrfmiddlewaretoken",
            value: options.csrf_token
        }];

    var base_file = new Ext.ux.form.FileUploadField({
        id: 'base_file',
        emptyText: gettext('Select a layer data file'),
        fieldLabel: gettext('Data'),
        name: 'base_file',
        allowBlank: false,
        listeners: listeners
    });

    var dbf_file = new Ext.ux.form.FileUploadField({
        id: 'dbf_file',
        emptyText: gettext('Select a .dbf data file'),
        fieldLabel: gettext('DBF'),
        name: 'dbf_file',
        allowBlank: true,
        listeners: listeners,
        validator: function(name) {
            if ((name.length > 0) && (name.search(/\.dbf$/i) == -1)) {
                return gettext("Invalid DBF File.");
            } else {
                return true;
            }
        }
    });

    var shx_file = new Ext.ux.form.FileUploadField({
        id: 'shx_file',
        emptyText: gettext('Select a .shx data file'),
        fieldLabel: gettext('SHX'),
        name: 'shx_file',
        allowBlank: true,
        listeners: listeners,
        validator: function(name) {
            if ((name.length > 0) && (name.search(/\.shx$/i) == -1)) {
                return gettext("Invalid SHX File.");
            } else {
                return true;
            }
        }
    });

    var prj_file = new Ext.ux.form.FileUploadField({
        id: 'prj_file',
        emptyText: gettext('Select a .prj data file (optional)'),
        fieldLabel: gettext('PRJ'),
        name: 'prj_file',
        allowBlank: true,
        listeners: listeners,
        validator: function(name) {
            if ((name.length > 0) && (name.search(/\.prj$/i) == -1)) {
                return gettext("Invalid PRJ File.");
            } else {
                return true;
            }
        }
    });

    var sld_file = new Ext.ux.form.FileUploadField({
        id: 'sld_file',
        emptyText: gettext('Select a .sld style file (optional)'),
        fieldLabel: gettext('SLD'),
        name: 'sld_file',
        allowBlank: true,
        listeners: listeners
    });

    var xml_file = new Ext.ux.form.FileUploadField({
        id: 'xml_file',
        emptyText: gettext('Select a .xml metadata file (ISO, Dublin Core, FGDC [optional])'),
        fieldLabel: gettext('XML'),
        name: 'xml_file',
        allowBlank: true,
        listeners: listeners
    });

    var abstractField = new Ext.form.TextArea({
        id: 'abstract',
        fieldLabel: gettext('Abstract'),
        name: 'abstract',
        allowBlank: true
    });

    var permissionsField = new Ext.form.Hidden({
        name: "permissions"
    });

    form_fields.push(base_file);

    if (options.is_featuretype) {
        form_fields = form_fields.concat(dbf_file, shx_file, prj_file);
    }

    if (!options.layer_name) {
        form_fields = form_fields.concat(sld_file, xml_file, abstractField,permissionsField);
    }

    var fp = new Ext.FormPanel({
        renderTo: 'upload_form',
        fileUpload: true,
        width: 500,
        frame: true,
        autoHeight: true,
        unstyled: true,
        labelWidth: 50,
        bodyStyle: 'padding: 10px 10px 0 10px;',
        defaults: {
            anchor: '95%',
            msgTarget: 'side'
        },
        items: form_fields,
        buttons: [{
            text: gettext('Upload'),
            handler: function(){
                if (fp.getForm().isValid()) {
                    fp.getForm().submit({
                        url: options.form_target,
                        waitMsg: gettext('Uploading your data...'),
                        success: function(form, action) {
                            document.location = action.result.redirect_to;
                        },
                        failure: function(form, action) {
                            Ext.Msg.show({
                                title: gettext('Error'),
                                msg: action.response.responseText,
                                midWidth: 200,
                                modal: true,
                                icon: Ext.Msg.ERROR,
                                buttons: Ext.Msg.Ok
                            });
                        }
                    });
                }
            }
        }]
    });

    var disable_shapefile_inputs = function() {
        dbf_file.hide();
        shx_file.hide();
        prj_file.hide();
    };

    var enable_shapefile_inputs = function() {
        dbf_file.show();
        shx_file.show();
        prj_file.show();
    };

    var check_shapefile = function() {
        if ((/\.shp$/i).test(base_file.getValue())) {
            enable_shapefile_inputs();
        } else {
            disable_shapefile_inputs();
        }
    };

    base_file.addListener('fileselected', function(cmp, value) {
        check_shapefile();
    });
    
    if (options.layer_name) {
        enable_shapefile_inputs();
    } else {
        disable_shapefile_inputs();
    }

    if (! options.layer_name) {
        var permissionsEditor = new GeoNode.PermissionsEditor({
            renderTo: "permissions_form",
            userLookup: options.userLookup,
            listeners: {
                updated: function(pe) {
                    permissionsField.setValue(Ext.util.JSON.encode(pe.writePermissions()));
                }
            },
            permissions: {
                anonymous: 'layer_readonly',
                authenticated: 'layer_readonly',
                users:[]
            }
        });
        permissionsEditor.fireEvent("updated", permissionsEditor);
    }

    function test_file_api() {
        var fi = document.createElement('INPUT');
        fi.type = 'file';
        return 'files' in fi;
    }

    if (test_file_api()) {
        // track dropped files separately from values of input fields
        var dropped_files = {};
        // drop handler
        var drop = function(ev) {
            ev.preventDefault();
            var dt = ev.dataTransfer, files = dt.files, i = 0, ext, key, w;
            // this is the single file drop - it may be a tiff or a shp file or a zip
            if (files.length == 1 && !dbf_file.isVisible()) {
                base_file.setValue(files[i].name);
                check_shapefile();
                dropped_files.base_file = files[i];
            } else {
                // multiple file drop
                for (; i < files.length; i++) {
                    ext = files[i].name.split('.');
                    // grab the last part to avoid .shp.xml getting sucked in
                    ext = ext[ext.length - 1];
                    if (ext == 'shp') {
                        base_file.setValue(files[i].name);
                        enable_shapefile_inputs();
                        dropped_files.base_file = files[i];
                    } else {
                        try {
                            key = ext + '_file', w = eval(key);
                            w.setValue(files[i].name);
                            dropped_files[key] = files[i];
                        } catch (ReferenceError) {}
                    }
                }
            }
        };

        // drop target w/ drag over/exit effects
        var dropPanel = new Ext.Container({
            html: "Drop Files Here",
            cls: 'x-panel-body',
            style: { borderWidth: '1px', borderStyle: 'solid', textAlign: 'center'},
            listeners: {
                render: function(p) {
                    var el = p.getEl().dom;
                    function t() {p.getEl().toggleClass('x-grid3-cell-selected');}
                    el.addEventListener("dragover", function(ev) {
                        ev.stopPropagation();
                        ev.preventDefault();
                    }, true);
                    el.addEventListener("drop", function(ev) {
                        p.getEl().removeClass('x-grid3-cell-selected');
                        drop(ev);
                    },false);
                    el.addEventListener("dragexit",t);
                    el.addEventListener("dragenter",t);
                }
            }
        });
        fp.add(dropPanel);
        fp.doLayout();
        
        function createDragFormData() {
            var data = new FormData(), id, value, fields = fp.getForm().getFieldValues(), size = 0;
            for (id in fields) {
                value = fields[id];
                if (id in dropped_files) {
                    size = size + dropped_files[id].size;
                    data.append(id,dropped_files[id],value);
                } else {
                    data.append(id,value);
                }
            }
            return data;
        }

        function upload(formData) {
            var xhr = new XMLHttpRequest();
            var progress;
            xhr.upload.addEventListener('loadstart', function(ev) {
                progress = Ext.MessageBox.progress("Please wait","Uploading your data...");
            }, false);
            xhr.upload.addEventListener('progress', function(ev) {
                if (ev.lengthComputable) {
                    // assume that 25% of the time will be actual server work, not just upload time
                    var msg = parseInt(ev.loaded / 1024) + " of " + parseInt(ev.total / 1024);
                    progress.updateProgress( (ev.loaded/ev.total)* .75, msg);
                    if (ev.loaded == ev.total) {
                        progress.updateProgress(.75,"Awaiting response");
                    }
                }
            }, false);

            function error(ev,result) {
                var error_message;
                if (typeof result != 'undefined') {
                    error_message = '<ul>';
                    for (var i = 0; i < result.errors.length; i++) {
                        error_message += '<li>' + result.errors[i] + '</li>'
                    }
                    error_message += '</ul>'
                } else {
                    error_message = "Unexpected Error:<p>" + xhr.responseText;
                }

                Ext.Msg.show({
                    title: gettext("Error"),
                    msg: error_message,
                    minWidth: 200,
                    modal: true,
                    icon: Ext.Msg.ERROR,
                    buttons: Ext.Msg.OK
                });
            }
            xhr.addEventListener('load', function(ev) {
                try {
                    var result = Ext.decode(xhr.responseText);
                    if (result.success) {
                        if (result.progress) {
                            pollProgress(result.redirect_to, result.progress, fp.getForm().el);
                        } else {
                            document.location = result.redirect_to;
                        }
                    } else {
                        error(ev, result);
                    }
                } catch (ex) {
                    console.log(ex);
                    error(ev);
                }
            }, false);
            xhr.addEventListener('error', error, false);

            xhr.open("POST",options.form_target, true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.send(formData);
        }

        var originalHandler = fp.buttons[0].handler;
        fp.buttons[0].handler = function() {
            if (!fp.getForm().isValid()) return;
            if ('base_file' in dropped_files) {
                upload(createDragFormData());
            } else {
                originalHandler();
            }
        }
    }

    var confirmDelete = true;
    var activeDelete = null;
    function deleteUpload(el) {
        var a = new Ext.Element(el);
        Ext.Ajax.request({
            url : a.getAttribute('href'),
            success : function() {
                var uip = a.parent('.uip');
                Ext.get('confirm-delete').hide().appendTo(uip.parent());
                uip.remove();
                if (Ext.select('div.uip').getCount() == 0) {
                    Ext.select('section.uip').addClass('hide');
                }
            },
            failure : function() {
                alert('Uh oh. An error occurred.')
            }
        });
        Ext.get('confirm-delete').hide();
    }
    Ext.select('#confirm-delete a').on('click',function(ev) {
        var resp = Ext.get(this).getAttribute('href');
        ev.preventDefault();
        if (/n/.test(resp)) {
            Ext.get('confirm-delete').hide();
        } else {
            if (/yy/.test(resp)) {
                confirmDelete = false;
            }
            deleteUpload(activeDelete);
        }

    });
    Ext.select('.uip .icon-trash').on('click',function(ev) {
        ev.preventDefault();
        if (confirmDelete) {
            activeDelete = this;
            Ext.get('confirm-delete').removeClass('hide').appendTo(Ext.get(this).parent('.uip')).enableDisplayMode().show();
        } else {
            deleteUpload(this);
        }
    });
}
