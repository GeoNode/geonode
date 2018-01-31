var ajax = {
    crossDomainAjax: function (url, successCallback, errorCallback) {

        // IE8 & 9 only Cross domain JSON GET request
        if ('XDomainRequest' in window && window.XDomainRequest !== null) {

            var xdr = new XDomainRequest(); // Use Microsoft XDR
            xdr.open('get', url);
            xdr.onload = function () {
                var dom = new ActiveXObject('Microsoft.XMLDOM'),
                    JSON = $.parseJSON(xdr.responseText);

                dom.async = false;

                if (JSON == null || typeof (JSON) == 'undefined') {
                    JSON = $.parseJSON(data.firstChild.textContent);
                }

                successCallback(JSON); // internal function
            };

            xdr.onerror = function (data) {
                errorCallback(data);
            };

            xdr.send();
        }    // IE7 and lower can't do cross domain
        else if (navigator.userAgent.indexOf('MSIE') != -1 &&
            parseInt(navigator.userAgent.match(/MSIE ([\d.]+)/)[1], 10) < 8) {
            return false;
        }

            // Do normal jQuery AJAX for everything else          
        else {
            $.ajax({
                url: url,
                cache: false,
                dataType: 'json',
                type: 'GET',
                //async: false, // must be set to false
                success: function (data, success) {
                    successCallback(data);
                },
                error: function (data) {
                    errorCallback(data);
                }
            });
        }
    }
}