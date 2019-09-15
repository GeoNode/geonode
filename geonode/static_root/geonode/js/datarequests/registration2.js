$(function() {
    var $intended_use = $("#id_intended_use_of_dataset");
    var $form = $intended_use.closest('form');
    var $noncommercial = $form.find('fieldset.noncommercial-fieldset');
    

        // Data Set
    var $data_set = $("#id_data_set");
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
    
    //Data Class
    var $data_class_selector = $('#id_data_class_requested');
    var $data_class_other = $('#div_id_data_class_other');
    
    if ($('#id_data_class_requested option[value=OTHER]:selected').length > 0){
        $data_class_other.toggle(true);
    }else {
        $data_class_other.toggle(false);
    }
    
    //Initial values
    $data_class_selector.click(function(){
        //selected = $data_class_selector.selectedOptions
        if ($('#id_data_class_requested option[value=OTHER]:selected').length > 0){
            console.log()
            $data_class_other.slideDown();
            $data_class_other.find('input').focus();
        }else {
            $data_class_other.slideUp();
        }
    });
    
});
