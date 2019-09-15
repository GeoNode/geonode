$(function() {

    var $org_type = $("#id_org_type")
    // var $org_type = $('input[name="organization_type"]');
    // var $org_type_checked = $('input[name="organization_type"]:checked');
    var $form2 = $org_type.closest('form');
    var $academe = $form2.find('fieldset.academe-fieldset');
    var $other = $form2.find('div#div_id_organization_other');

    // Initial values
    $academe.toggle(false);
    $other.toggle(false);
    if ($org_type.val().indexOf("Academe")>=0) {
      $academe.toggle(true);
    }else if ($org_type.val() == 'Other') {
      $other.toggle(true);
    }
    $org_type.change( function() {
        // if ($(this).val() == '3'){
        if ($(this).val().indexOf("Academe")>=0){
            $academe.slideDown();
        } else {
            $academe.slideUp();
        }
        if ($(this).val() == 'Other'){
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

});
