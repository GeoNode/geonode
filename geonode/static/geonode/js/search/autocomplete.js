
/**
 * Function used to add autocomplete to input fields.
 * The new version of autocomplete light seems to have built in support for select using select2
 * but does not support regular input autocomplete.
 * @param {object} options Options object for autocomplete including DOM selectors and url
 */
var Autocomplete = function(options) {

    // Multiple selelectors to make this reusable 
    this.form_btn = options.form_btn
    this.form_submit = options.form_submit
    this.form_selector = options.form_selector
    this.input_selector = options.input_selector
    this.container_selector = options.container_selector

    // Custom url for autocomplete can be set otherwise the constant will be used set in search_scripts.html
    this.url = options.url || AUTOCOMPLETE_URL_RESOURCEBASE

    // Minimum input length which autocomplete will activate
    this.minimum_length = parseInt(options.minimum_length || 1)

    // DOM elements
    this.form_elem = null
    this.query_box = null
  }

  Autocomplete.prototype.setup = function() {
    var self = this

    // Gets input box for getting input text and container to add the autocomplete element to
    this.form_elem = $(this.form_selector);
    this.query_box = this.form_elem.find($(this.input_selector));
    this.query_container = this.form_elem.find($(this.container_selector));

    // Watch the input box.
    this.query_box.on('keyup', function() {
      
      // Gets the input text from the search field
      var query = self.query_box.val()

      if(query.length < self.minimum_length) {
        $('.ac-results').remove() // Remove autocomplete when no input
        return false
      }
    
      self.fetch(query)
    })

    // On selecting a result, populate the search field.
    this.form_elem.on('click', '.ac-result', function(ev) {
      self.query_box.val($(this).text())
      $('.ac-results').remove()
      if (typeof self.form_btn !== 'undefined') {
        $(self.form_btn).click();
      }
      if (typeof self.form_submit !== 'undefined') {
        $(self.form_submit).submit();
      }
      return false
    })
  }

  Autocomplete.prototype.fetch = function(query) {
    var self = this

    // Fetching the autocomplete data from the autocomplete light urls set up on backend
    // Filtered based on the current input
    $.ajax({
      url: this.url
    , data: {
        'q': query
      }
    , success: function(data) {
        self.show_results(data)
      }
    })
  }

  Autocomplete.prototype.show_results = function(data) {
    // Remove any existing results.
    $('.ac-results').remove()

    // Mapping to the item text and limiting results shown to 10 only rather
    // than scrolling. Set removes any duplicates.
    var results = [...new Set(data.results.map(item => item.text).slice(0, 10))] || []
    var results_wrapper = $('<div class="ac-results"></div>')
    var base_elem = $('<div class="result-wrapper"><a href="#" class="ac-result"></a></div>')

    if(results.length > 0) {
      for(var res_offset in results) {
        var elem = base_elem.clone()
        // Adding each query result to the autocomplete element
        // This should use some form of templating instead.
        elem.find('.ac-result').text(results[res_offset])
        results_wrapper.append(elem)
      }
    }

    this.query_box.after(results_wrapper)
  }

  Autocomplete.prototype.fixPosition = function(html) {
    this.input.parents().filter(function() {
        return $(this).css('overflow') === 'hidden';
    }).first().css('overflow', 'visible');
    if(this.input.attr('name') !== 'resource-keywords'){
      this.box.insertAfter(this.input).css({top: 0, left: 0});
    }else{
      var pos = $.extend({}, this.input.position(), {
        height: this.input.outerHeight()
      });
      this.box.insertAfter(this.input).css({top: pos.top + pos.height, left: pos.left});
    }
  }
