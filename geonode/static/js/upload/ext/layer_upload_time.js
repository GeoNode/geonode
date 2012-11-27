Ext.onReady(function() {
    Ext.QuickTips.init(); 
    var precision = Ext.get('precision'), 
        format = Ext.get('format_input'),
        presentation = Ext.get('presentation');
    presentation.hide();
    precision.hide();
    if (format) format.hide();

    // time type selected - either by radio click or select
    function timeTypeSelected(select) {
        if (!Ext.get("notime").dom.checked) {
            if (! presentation.isVisible()) {
                presentation.fadeIn();
            }
        } else {
            presentation.hide();
        }
        Ext.select("#timeForm select").each(function(e,i) {
            if (e.dom != select) {
                e.dom.value = "";
            }
        });
        if (select && !select.value) {
            select.value = select.options[1].value;
        }
    }

    // show presentation section if needed and select first attribute
    Ext.get(Ext.query("input[name=timetype]")).on('click',function() {
        var select = Ext.fly(this).next('select');
        if (select) timeTypeSelected(select.dom);
    });

    // only show the precision section if needed
    Ext.get(Ext.query("input[name=presentation_strategy]")).on('click',function() {
        if (!Ext.query("input[value=LIST]")[0].checked) {
            if (!precision.isVisible()) {
                precision.fadeIn();
            }
        } else{
            precision.hide();
        }
    });

    // sync radio button selection with attribute selectors
    Ext.select("#id_text_attribute, #id_time_attribute, #id_year_attribute").on('change',function() {
        if (this.id == 'format_select') return;
        if (this.value != "") {
            Ext.get(this).parent(".formSection").first().dom.checked = true;
            timeTypeSelected(this);
        } else {
            Ext.get("notime").dom.click();
        }
    });

    // show custom format field if needed
    if (format) {
        Ext.get('format_select').on('change',function() {
            var input = Ext.get("id_text_attribute_format");
            if (this.getAttribute('value') == '0') {
                format.hide();
                input.dom.value = '';
            } else {
                format.fadeIn();
                input.focus();
            }
        });
    }
    
});