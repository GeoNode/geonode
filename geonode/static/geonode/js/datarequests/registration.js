$(function() {

    var $intended_use = $("#id_intended_use_of_dataset");
    var $org_type = $("#id_organization_type")
    var $form = $intended_use.closest('form');
    var $form2 = $org_type.closest('form');
    var $noncommercial = $form.find('fieldset.noncommercial-fieldset');
    var $academe = $form2.find('fieldset.academe-fieldset');

    // Initial values

    if ($org_type.val() != '3') {
        $academe.toggle(false);
    } else {
        $academe.toggle(true);
    }
    $org_type.on('change', function() {

        if ($(this).val() == '3'){
            $academe.slideDown();
        } else {
            $academe.slideUp();
        }
    });

    // Data Set
    var $data_set = $("#id_data_set")
    var $data_set_other = $form.find('#div_id_data_set_other').parent();

    // Initial values
    if ($data_set.val() == 'other'){
        $data_set_other.toggle(true);
    } else {
        $data_set_other.toggle(false);
    }
    $form.on('change', '#id_data_set', function() {
        if ($(this).val() == 'other'){
            $data_set_other.slideDown();
            $data_set_other.find('input').focus();
        } else {
            $data_set_other.slideUp();
        }
    });

    // Purpose
    var $purpose = $("#id_purpose")
    var $purpose_other = $form.find('#div_id_purpose_other').parent();

    // Initial values
    if ($purpose.val() == 'other'){
        $purpose_other.toggle(true);
    } else {
        $purpose_other.toggle(false);
    }
    $form.on('change', '#id_purpose', function() {
        if ($(this).val() == 'other'){
            $purpose_other.slideDown();
            $purpose_other.find('input').focus();
        } else {
            $purpose_other.slideUp();
        }
    });

});
