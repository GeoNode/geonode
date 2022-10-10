/*globals define: true, requirejs: true */
'use strict';

requirejs.config({
  config: {
     text: {
       useXhr: function (url, protocol, hostname, port) {
          // allow cross-domain requests
          // remote server allows CORS
          return true;
       }
     },
     waitSeconds: 5
  },
  baseUrl: staticUrl + 'lib/js',
  shim: {
    'underscore': { exports: '_'}
  },
  paths: {
    'upload': '../../geonode/js/upload',
    'templates': '../../geonode/js/templates',
    'progress': 'jquery.ajax-progress'
  }
});

define(['upload/upload',
        'upload/common',
        'upload/LayerInfo'], function (upload, common, LayerInfo) {
    'use strict';

    function isTimeSeries() {
        var is_time_series = true;
        $('input:radio').each(function(index) {
            if($('input:radio')[index].id === 'notime' &&
                  $('input:radio')[index].checked) {
                is_time_series = false;
            }
        });
        return is_time_series;
    }

    function getSelectedTimeAttribute() {
        var selected_attribute;
        $('input[id^="id_time_attribute"]').each(function(index) {
            if($('input[id^="id_time_attribute"]')[index].checked) {
                selected_attribute = $('input[id^="id_time_attribute"]')[index].value;
            }
        });
        $('input[id^="id_text_attribute"]').each(function(index) {
            if($('input[id^="id_text_attribute"]')[index].checked) {
                selected_attribute = $('input[id^="id_text_attribute"]')[index].value;
            }
        });
        $('input[id^="id_year_attribute"]').each(function(index) {
            if($('input[id^="id_year_attribute"]')[index].checked) {
                selected_attribute = $('input[id^="id_year_attribute"]')[index].value;
            }
        });
        return selected_attribute;
    }

    function isTimeAttrValid() {
        var selected_attribute = getSelectedTimeAttribute();
        var time_attr_is_valid = false;
        try {
            if(selected_attribute) {
                if(data_is_valid.hasOwnProperty(selected_attribute)){
                    time_attr_is_valid = data_is_valid[selected_attribute];
                } else {
                    time_attr_is_valid = true;
                }
            } else if(Object.keys(data_is_valid).length === 0) {
                time_attr_is_valid = true;
            }
        } catch(err) {
            time_attr_is_valid = false;
        }
        return time_attr_is_valid;
    }

    function toggleTimeDataTableValidation(toggle) {
        var data_validation_toggled = data_validation;
        if(toggle) {
            data_validation = true;
            $('input[id^="id_time_attribute"]').each(function(index) {
                if($($('input[id^="id_time_attribute"]')[index]).attr('type') == 'hidden' ||
                    $($('input[id^="id_time_attribute"]')[index]).is(":hidden")) {
                        $($('input[id^="id_time_attribute"]')[index]).show();
                }
            });
            $('input[id^="id_text_attribute"]').each(function(index) {
                if($($('input[id^="id_text_attribute"]')[index]).attr('type') == 'hidden' ||
                    $($('input[id^="id_text_attribute"]')[index]).is(":hidden")) {
                        $($('input[id^="id_text_attribute"]')[index]).show();
                }
            });
            $('input[id^="id_year_attribute"]').each(function(index) {
                if($($('input[id^="id_year_attribute"]')[index]).attr('type') == 'hidden' ||
                    $($('input[id^="id_year_attribute"]')[index]).is(":hidden")) {
                        $($('input[id^="id_year_attribute"]')[index]).show();
                }
            });
        } else {
            data_validation = false;
            $('input[id^="id_time_attribute"]').each(function(index) {
                $($('input[id^="id_time_attribute"]')[index]).hide();
            });
            $('input[id^="id_text_attribute"]').each(function(index) {
                $($('input[id^="id_text_attribute"]')[index]).hide();
            });
            $('input[id^="id_year_attribute"]').each(function(index) {
                $($('input[id^="id_year_attribute"]')[index]).hide();
            });
        }

        if(data_validation_toggled != data_validation) {
            $('#bootstrap-text-att-table').bootstrapTable('refresh');
            $('#bootstrap-text-att-table').bootstrapTable('selectPage', 1);
        }

        if(!isTimeSeries() || isTimeAttrValid()) {
            $("#next").removeAttr("disabled");
            $('#next-tooltip').text('Start Importer');
        } else {
            $("#next").attr("disabled", "disabled");
            $('#next-tooltip').html('Temporal dimension cannot be set if there are <br>errors on data.<br><br>' +
                'Please, try to select another column or <br>fix the source file and try to upload it again!');
        }
    }

    var doTime = function (event) {
        var form = $("#timeForm");

        function makeRequest(data) {
            common.make_request({
                url: data.redirect_to,
                async: false,
                failure: function (resp, status) {
                    common.logError(resp);
                    $('#next-spinner').addClass('hide');
                },
                success: function (resp, status) {
                    if (resp.status) {
                        if (resp.status === 'error') {
                            self.polling = false;
                            common.logError(resp.error_msg);
                            $('#next-spinner').addClass('hide');
                        } else if (resp.status === 'pending') {
                            setTimeout(function() {
                                makeRequest(resp);
                            }, 5000);
                            return;
                        } else if (resp.status === 'incomplete') {
                            if('redirect_to' in resp && resp.redirect_to) {
                                self.polling = false;
                                window.location = resp.redirect_to;
                            } else if ('url' in resp && resp.url) {
                                self.polling = false;
                                window.location = resp.url;
                            } else {
                                common.logError("unexpected response");
                                $('#next-spinner').addClass('hide');
                            }
                        } else if (resp.status === 'finished') {
                            self.polling = false;
                            window.location = resp.url;
                        }
                    } else {
                         if('redirect_to' in resp && resp.redirect_to) {
                             makeRequest(resp);
                         } else if ('url' in resp && resp.url) {
                             self.polling = false;
                             window.location = resp.url;
                         } else {
                             common.logError("unexpected response");
                             $('#next-spinner').addClass('hide');
                         }
                     }
                }
            });
        };

      var params = common.parseQueryString(document.location.search);
      var url = siteUrl + 'upload/time'
      if ('id' in params){
        url = updateUrl(url, 'id', params.id);
      }

      if(!isTimeSeries() ||
            (getSelectedTimeAttribute() && isTimeAttrValid())) {
          $('#next-spinner').removeClass('hide');
          $.ajax({
             type: "POST",
             url: url,
             data: form.serialize(), // serializes the form's elements.
             success: function(data)
             {
                 if (data.status) {
                     if (data.status === 'error') {
                         self.polling = false;
                         common.logError(data.error_msg);
                         $('#next-spinner').addClass('hide');
                     } else if (data.status === 'pending' ||
                              data.status === 'incomplete') {
                         makeRequest(data);
                     }
                 } else {
                      if('redirect_to' in data && data.redirect_to) {
                          makeRequest(data);
                      } else if ('url' in data && data.url) {
                          self.polling = false;
                          window.location = data.url;
                      } else {
                          common.logError("unexpected response");
                          $('#next-spinner').addClass('hide');
                      }
                  }
             },
             error: function (resp, status) {
                  common.logError(resp);
                  $('#next-spinner').addClass('hide');
             }
          });
      } else {
          $("#timeMsgBoxModalWarning").find('.modal-title').text('Warning');
          if(getSelectedTimeAttribute()) {
              $("#timeMsgBoxModalWarning").find('.modal-body').text('Data has errors. Please double check!');
          } else {
              $("#timeMsgBoxModalWarning").find('.modal-body').text('Please, select a column eligible as a valid date/time representation!');
          }
          $("#timeMsgBoxModalWarning").modal("show");
      }
      return false;
    };

    $(function () {
        $("#next").on('click', doTime);
        const settingsForm = document.getElementById("settings");

        $("#DISCRETE_INTERVAL,#CONTINUOUS_INTERVAL").on('change',function(ev) {
            $("#precision").show();
        });

        $("#LIST").on('change',function(ev) {
            $("#precision").hide().find("input").val(null);
        });

        $('#time-series-toggle-choice').on('change',function(ev) {
            // show time form and advamced options
            if (settingsForm.style.display !== "none"){
                settingsForm.style.display = "none";
            }
            else{
                settingsForm.style.display = "block";
            }
            if(ev.target.value === 'on' && ev.target.checked) {

                if($('#existing').val()) {
                    $('input:radio[id="existing"]').prop("checked", true);
                    $('#existing').trigger("click");
                } else if($('#textattribute').val()) {
                    $('input:radio[id="textattribute"]').prop("checked", true);
                    $('#textattribute').trigger("click");
                } else if($('#convertnumber').val()) {
                    $('input:radio[id="convertnumber"]').prop("checked", true);
                    $('#convertnumber').trigger("click");
                }
            } else {
                $('input:radio[id="notime"]').prop("checked", true);
                $('#notime').trigger("click");
            }
        });

        $('input:radio').click(function(event){
            var obj = event.currentTarget
            if(obj.id.includes('id_time_attribute')) {
                toggleTimeDataTableValidation(true);
                if($('#existing') && !$('#existing')[0].checked) {
                    $('#existing')[0].checked = true;
                }
            } else if(obj.id.includes('id_text_attribute')) {
                toggleTimeDataTableValidation(true);
                if($('#textattribute') && !$('#textattribute')[0].checked) {
                    $('#textattribute')[0].checked = true;
                }
            } else if(obj.id.includes('id_year_attribute')) {
                toggleTimeDataTableValidation(true);
                if($('#convertnumber') && !$('#convertnumber')[0].checked) {
                    $('#convertnumber')[0].checked = true;
                }
            } else if(obj.id === 'existing' || obj.id === 'textattribute' || obj.id === 'convertnumber') {
                toggleTimeDataTableValidation(true);
            } else if(obj.id === 'notime') {
                toggleTimeDataTableValidation(false);

                $('input[id^="id_time_attribute"]').each(function(index) {
                    if($('input[id^="id_time_attribute"]')[index].checked) {
                        $('input[id^="id_time_attribute"]')[index].checked = false;
                    }
                });
                $('input[id^="id_text_attribute"]').each(function(index) {
                    if($('input[id^="id_text_attribute"]')[index].checked) {
                        $('input[id^="id_text_attribute"]')[index].checked = false;
                    }
                });
                $('input[id^="id_year_attribute"]').each(function(index) {
                    if($('input[id^="id_year_attribute"]')[index].checked) {
                        $('input[id^="id_year_attribute"]')[index].checked = false;
                    }
                });
            }
        });
    });

});
