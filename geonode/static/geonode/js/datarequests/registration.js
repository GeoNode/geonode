$(function() {

    var $intended_use = $("#id_intended_use_of_dataset");
    var $org_type = $("#id_org_type")
    // var $org_type = $('input[name="organization_type"]');
    // var $org_type_checked = $('input[name="organization_type"]:checked');
    var $form = $intended_use.closest('form');
    var $form2 = $org_type.closest('form');
    var $noncommercial = $form.find('fieldset.noncommercial-fieldset');
    var $academe = $form2.find('fieldset.academe-fieldset');
    var $other = $form2.find('div#div_id_organization_other');

    // Initial values
    $academe.toggle(false);
    $other.toggle(false);
    if ($org_type.val().indexOf("Academe")>=0) {
      $academe.toggle(true);
    }else if ($org_type.val() == 'Others') {
      $other.toggle(true);
    }
    $org_type.change( function() {
        // if ($(this).val() == '3'){
        if ($(this).val().indexOf("Academe")>=0){
            $academe.slideDown();
        } else {
            $academe.slideUp();
        }
        if ($(this).val() == 'Others'){
            $other.slideDown();
        } else {
            $other.slideUp();
        }
    });
    // Radio button
    // if ($org_type_checked.val() == '3') {
    //   $academe.toggle(true);
    // }else if ($org_type_checked.val() == '7') {
    //   $other.toggle(true);
    // }
    // // $org_type.on('change', function() {
    // $org_type.change( function() {
    //     // if ($(this).val() == '3'){
    //     if ($(this).is(':checked') && $(this).val() == '3'){
    //         $academe.slideDown();
    //     } else {
    //         $academe.slideUp();
    //     }
    //     if ($(this).is(':checked') && $(this).val() == '7'){
    //         $other.slideDown();
    //     } else {
    //         $other.slideUp();
    //     }
    // });

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
