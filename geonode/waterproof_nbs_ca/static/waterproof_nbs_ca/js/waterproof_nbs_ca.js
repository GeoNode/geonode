/**
 * @file Manages front logic for NBS forms
 * @author Luis Saltron
 * @version 1.0
*/
$(function () {
    initialize = function () {
        console.log('init event loaded');
        submitFormEvent();
        changeFileEvent();
    };
    submitFormEvent = function () {
        console.log('submit event loaded');
        var formData = new FormData();
        $('#submit').on('click', function () {
            formData.append('title', $('#title').val());
            formData.append('description', $('#description').val());
            formData.append('shapefile', $('#shapefile')[0].files[0]);
            formData.append('action', 'create-nbs');
            formData.append('csrfmiddlewaretoken', token);

            $.ajax({
                type: 'POST',
                url: '/waterproof_nbs_ca/create/',
                data: formData,
                cache: false,
                processData: false,
                contentType: false,
                enctype: 'multipart/form-data',
                success: function () {
                    alert('The post has been created!')
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ":" + xhr.responseText)
                }
            })
        });
    };
    changeFileEvent = function () {
        $('#shapefile').change(function (evt) {
            var file = evt.currentTarget.files[0];
            var extension = validExtension(file);
            // Validate file's extension
            if (extension.valid) { //Valid
                console.log('Extension valid!');
                // Validate file's extension
                if (extension.extension == 'geojson') {
                    var readerGeoJson = new FileReader();
                    readerGeoJson.onload = function (evt) {
                        var contents = evt.target.result;
                        geojson = JSON.parse(contents);
                        loadFile(geojson, file.name);
                    }
                    readerGeoJson.readAsText(file);
                }
                else {
                    
                }
            }
            else { //Invalid

            }
        });
    };
    checkEmptyFile = function () {

    };

    /** 
     * Get if file has a valid shape or GeoJSON extension 
     * @param {StriFileng} file   zip or GeoJSON file
     *
     * @return {Object} extension Object contain extension and is valid
     */
    validExtension = function (file) {
        var fileExtension = {};
        if (file.name.lastIndexOf(".") > 0) {
            var extension = file.name.substring(file.name.lastIndexOf(".") + 1, file.name.length);
            fileExtension.extension = extension;
        }
        if (file.type == 'application/x-zip-compressed' || file.type == 'application/zip') {
            fileExtension.valid = true;
        } else if (file.type == 'application/geo+json') {
            fileExtension.valid = true;
        }
        else {
            fileExtension.valid = false;
        }
        return fileExtension;
    };
    loadFile = function (file, name) {
        console.log('Start loading file function!');
    };
    // Init 
    initialize();
});
/*
  $.ajax({
      type: 'POST',
      url: '{% url "create-post" %}',
      data: formData,
      cache: false,
      processData: false,
      contentType: false,
      enctype: 'multipart/form-data',
      success: function (){
          alert('The post has been created!')
      },
      error: function(xhr, errmsg, err) {
          console.log(xhr.status + ":" + xhr.responseText)
      }
  })


$('#id_added_by').val(userId).change();
$('#id_added_by').hide();
$('label[for="id_added_by"]').hide();
$('#id_rios_transformations').empty();
$('#id_transformations_available').empty();*/
$('#update_costs').click(function () {
    var country_id = $('#id_country').val();
    var url = $('#nbscaForm').attr('data-countries-url');
    var currency_id = $('#id_currency').val();
    var urlCurrency = $('#nbscaForm').attr('data-currency-url');
    country_id == "" ? country_id = 1 : country_id = country_id;
    /** 
         * Get filtered activities by transition id 
         * @param {String} url   transformation URL 
         * @param {Object} data  activity id  
         *
         * @return {String} activities in HTML option format
         */
    $.ajax({
        url: url,
        data: {
            'country': country_id
        },
        success: function (data) {
            data = JSON.parse(data);
            factorCountry = data[0].fields.factor;
            $.ajax({
                url: urlCurrency,
                data: {
                    'currency': currency_id
                },
                success: function (data) {
                    data = JSON.parse(data);
                    factorCurrency = data[0].fields.factor;
                    let check = $('#id_global_costs')[0].checked
                    if (check) {
                        let id_unit_oportunity_cost = 35000;
                        let oportunityCost = id_unit_oportunity_cost * factorCountry * factorCurrency
                        $('#id_unit_oportunity_cost').val(oportunityCost);
                    }
                    else {
                        let id_unit_oportunity_cost = $('#id_unit_oportunity_cost').val();
                        let oportunityCost = id_unit_oportunity_cost * factorCountry * factorCurrency
                        $('#id_unit_oportunity_cost').val(oportunityCost);
                    }
                }
            });
        }
    });
});
$('#id_transformations_available').change(function (evt) {
    var optionsSelectedAvailable = [];
    var optionsTransformations = [];
    $.each($("#id_transformations_available option:selected"), function () {
        var option = {};
        option.value = $(this).val();
        option.text = $(this).html();
        optionsSelectedAvailable.push(option);
    });
    console.log(optionsSelectedAvailable);
    $("#id_rios_transformations").each(function (index, opt) {
        var option = {};
        if (opt.options.length > 0) {
            option.text = opt.options[index].text;
            option.value = opt.options[index].value;
        }
        optionsTransformations.push(option);
    });
    console.log(optionsTransformations);
    var onlyInA = optionsSelectedAvailable.filter(comparer(optionsTransformations));
    if (onlyInA.length > 0)
        $.each(onlyInA, function () {
            $('#waterproof_nbs_ca').append('<label for="">Cargar shapefile </label>');
            $('#waterproof_nbs_ca').append('<input type="file" name="">');
            $("#id_rios_transformations").append('<option value=' + this.value + ' selected>' + this.text + '</option>');
        });
});
$('#id_currency').change(function () {
    var urlCurrency = $('#nbscaForm').attr('data-currency-url');
    var currency_id = $('#id_currency').val();
    $.ajax({
        url: urlCurrency,
        data: {
            'currency': currency_id
        },
        success: function (data) {
            data = JSON.parse(data);
            let currencyCode = data[0].fields.code;
            let currencySymbol = data[0].fields.symbol;
            $('label[for="id_unit_maintenance_cost"]').html("Unit maintenance cost (" + currencyCode + " " + currencySymbol + "/ha)");
            $('label[for="id_unit_oportunity_cost"]').html("Unit oportunity costs (" + currencyCode + " " + currencySymbol + "/ha)");
            $('label[for="id_unit_implementation_cost"]').html("Unit implementation costs  (" + currencyCode + " " + currencySymbol + "/ha)");
        }
    });

});
$('#id_global_costs').change(function () {
    if (this.checked) {
        $('#id_unit_maintenance_cost').hide();
        $('label[for="id_unit_maintenance_cost"]').hide();

        $('#id_unit_implementation_cost').hide();
        $('label[for="id_unit_implementation_cost"]').hide();

        $('#id_periodicity_maitenance').hide();
        $('label[for="id_periodicity_maitenance"]').hide();
    }
    else {
        $('#id_unit_maintenance_cost').show();
        $('label[for="id_unit_maintenance_cost"]').show();

        $('#id_unit_implementation_cost').show();
        $('label[for="id_unit_implementation_cost"]').show();

        $('#id_periodicity_maitenance').show();
        $('label[for="id_periodicity_maitenance"]').show();
    }
});
// Rios transitions dropdown listener
$('#id_rios_transitions').change(function () {
    // Get load activities from urls Django parameter
    var url = $('#nbscaForm').attr('data-activities-url');
    var transition_id = $(this).val();

    /** 
    * Get filtered activities by transition id 
    * @param {String} url   activities URL 
    * @param {Object} data  transition id  
    *
    * @return {String} activities in HTML option format
    */
    $.ajax({
        url: url,
        data: {
            'transition': transition_id
        },
        success: function (data) {
            $('#id_rios_activities').empty().html(data);
            $('#id_rios_activities').change();
        }
    });
});

// Rios activities dropdown listener
$('#id_rios_activities').change(function () {
    // Get load transformations from urls Django parameter
    var url = $('#nbscaForm').attr('data-transformations-url');
    var activity_id = $(this).val();

    /** 
    * Get filtered activities by transition id 
    * @param {String} url   transformation URL 
    * @param {Object} data  activity id  
    *
    * @return {String} activities in HTML option format
    */
    $.ajax({
        url: url,
        data: {
            'transition': activity_id
        },
        success: function (data) {
            $('#id_transformations_available').empty().html(data);
        }
    });
});

function comparer(otherArray) {
    return function (current) {
        return otherArray.filter(function (other) {
            return other.value == current.value && other.display == current.display
        }).length == 0;
    }
}