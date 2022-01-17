"use strict";

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }

var IDS_VALUT = {
  SEND_B_ID: 'id_crop_save_button',
  CANCEL_B_ID: 'id_crop_cancel_button',
  OK_B_ID: 'id_crop_ok_button',
  DISMISS_B_ID: 'id_crop_dismiss_button',
  GRAIN_WRAP_ID: 'id_crop_entry',
  FILE_INPUT_ID: 'id_crop_file',
  WORKSPACE_ID: 'id_crop_modal_workspace',
  WORKSPACE_CONTAINER_ID: 'id_crop-modal-container',
  MODAL_OVERLAY_ID: 'id_crop-modal-overlay',
  FILE_LABEL_ID: 'id_crop-file-label'
};

var ThumbnailService = /*#__PURE__*/function () {
  function ThumbnailService(document_id, get_path) {
    _classCallCheck(this, ThumbnailService);

    this.document_id = document_id;
    this.get_path = get_path;
  }

  _createClass(ThumbnailService, [{
    key: "postThumbnail",
    value: function postThumbnail(base64_url) {
      var formData = new FormData();
      formData.append("file", this._b64toBlob(base64_url), 'blob.png');
      var url = location.origin + '/api/v2/resources/' + String(this.document_id) + '/set_thumbnail';
      $.ajax({
        url: url,
        data: formData,
        type: 'PUT',
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": this._getCookie('csrftoken')
        },
        success: function success() {
          location.reload();
        },
        error: function error() {
          throw Error('Cannot upload new thumbnail');
        }
      });
    }
  }, {
    key: "_getCookie",
    value: function _getCookie(name) {
      var value = "; " + document.cookie;
      var parts = value.split("; " + name + "=");

      if (parts.length === 2) {
        return parts.pop().split(";").shift();
      }
    }
  }, {
    key: "getThumbnail",
    value: function getThumbnail(image_element) {
      var callback = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
      var url = location.origin + this.get_path + String(this.document_id);
      return $.ajax({
        url: url,
        type: 'GET',
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": this._getCookie('csrftoken')
        },
        success: function success(data) {
          if (data && data.thumbnail_url) {
            image_element.src = data.thumbnail_url;
          } else {
            image_element.src = '/static/geonode/img/missing_thumb.png';
          }

          if (callback !== null) {
            callback();
          }
        },
        error: function error() {
          image_element.src = '/static/geonode/img/missing_thumb.png';
        }
      });
    }
  }, {
    key: "_b64toBlob",
    value: function _b64toBlob(b64Data, contentType) {
      var sliceSize = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 512;
      contentType = contentType || '';
      b64Data = b64Data.split(',')[1];
      var byteCharacters = atob(b64Data);
      var byteArrays = [];

      for (var offset = 0; offset < byteCharacters.length; offset += sliceSize) {
        var slice = byteCharacters.slice(offset, offset + sliceSize);
        var byteNumbers = new Array(slice.length);

        for (var i = 0; i < slice.length; i++) {
          byteNumbers[i] = slice.charCodeAt(i);
        }

        var byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
      }

      return new Blob(byteArrays, {
        type: contentType
      });
    }
  }]);

  return ThumbnailService;
}();

var CssManager = /*#__PURE__*/function () {
  function CssManager() {
    _classCallCheck(this, CssManager);
  }

  _createClass(CssManager, [{
    key: "makeVisible",
    value: function makeVisible(dom_elem_id) {
      $('#' + dom_elem_id).removeClass('invisible');
    }
  }, {
    key: "makeImvisible",
    value: function makeImvisible(dom_elem_id) {
      $('#' + dom_elem_id).addClass('invisible');
    }
  }, {
    key: "change_modal_visibility",
    value: function change_modal_visibility() {
      if ($('#' + IDS_VALUT.FILE_INPUT_ID).val()) {
        $('#' + IDS_VALUT.WORKSPACE_CONTAINER_ID).removeClass('invisible');
        $('#' + IDS_VALUT.MODAL_OVERLAY_ID).removeClass('invisible');
      } else {
        $('#' + IDS_VALUT.WORKSPACE_CONTAINER_ID).addClass('invisible');
        $('#' + IDS_VALUT.MODAL_OVERLAY_ID).addClass('invisible');
      }
    }
  }]);

  return CssManager;
}();

var DomBuilder = /*#__PURE__*/function () {
  // class too manage building required dom to display cropper
  function DomBuilder(widget_grain) {
    _classCallCheck(this, DomBuilder);

    this.widget_grain = widget_grain;
    $(this.widget_grain).wrap(function () {
      return "<div id=".concat(IDS_VALUT.GRAIN_WRAP_ID, " class=crop-widget></div>");
    });
    $(this.widget_grain).wrap(function () {
      return "";
    });
    this.grain_wrapper = $('#' + IDS_VALUT.GRAIN_WRAP_ID);
    this.grain_wrapper.append("<div id=".concat(IDS_VALUT.MODAL_OVERLAY_ID, " class=\"crop-modal-overlay invisible\"></div>"));
    this.grain_wrapper.prepend("<div class=\"thumbnail-title\">Thumbnail</div>");
  }

  _createClass(DomBuilder, [{
    key: "_create_flow_buttons",
    value: function _create_flow_buttons() {
      this.grain_wrapper.append("<input type=file id=".concat(IDS_VALUT.FILE_INPUT_ID, " name=files class=crop-input /> "));
      this.grain_wrapper.append("<label id=".concat(IDS_VALUT.FILE_LABEL_ID, " for=").concat(IDS_VALUT.FILE_INPUT_ID, " class=\"btn btn-default crop-input-label\">Choose file</label>"));
      this.grain_wrapper.append("<button type=button id=".concat(IDS_VALUT.SEND_B_ID, " class=\"btn btn-default invisible\">Save</button><button type=button id=").concat(IDS_VALUT.CANCEL_B_ID, " class=\"btn btn-default invisible\">Cancel</button>"));
    }
  }, {
    key: "create_workspace",
    value: function create_workspace() {
      var workspace_html = "\n                              <div id=".concat(IDS_VALUT.WORKSPACE_CONTAINER_ID, " class=\"crop-modal-container invisible\">                                  \n                                  <img id=").concat(IDS_VALUT.WORKSPACE_ID, " class=\"crop-modal-workspace\">                                      \n                                  <button type=button id=").concat(IDS_VALUT.OK_B_ID, " class=\"btn btn-default\">OK</button><button type=button id=").concat(IDS_VALUT.DISMISS_B_ID, " class=\"btn btn-default\">Dismiss</button>                                      \n                              </div>");
      $(document.body).append(workspace_html);

      this._create_flow_buttons();
    }
  }]);

  return DomBuilder;
}();

var CropTask = /*#__PURE__*/function () {
  function CropTask(dom_builder, css_manager, data_service) {
    _classCallCheck(this, CropTask);

    this.dom_builder = dom_builder;
    this.css_manager = css_manager;
    this.previous_image = null;
    this.data_service = data_service;
  }

  _createClass(CropTask, [{
    key: "init_cropper",
    value: function init_cropper() {
      this.cropper = new Cropper($('#' + IDS_VALUT.WORKSPACE_ID)[0], {
        aspectRatio: 4 / 3,
        crop: function crop(event) {}
      });
    }
  }, {
    key: "set_previous_image",
    value: function set_previous_image(image_src) {
      this.previous_image = image_src;
    }
  }, {
    key: "init",
    value: function init() {
      this.dom_builder.create_workspace();
      $('#' + IDS_VALUT.FILE_INPUT_ID).on('change', this.load_start_image.bind(this));
      $('#' + IDS_VALUT.DISMISS_B_ID).on('click', this.dismiss_current_image.bind(this));
      $('#' + IDS_VALUT.OK_B_ID).on('click', this.apply_current_image.bind(this));
      $('#' + IDS_VALUT.CANCEL_B_ID).on('click', this.cancel_cropping.bind(this));
      $('#' + IDS_VALUT.SEND_B_ID).on('click', this.send_cropped_image.bind(this));
      this.previous_image = this.dom_builder.widget_grain.src;
    }
  }, {
    key: "load_start_image",
    value: function load_start_image(file_event) {
      var _this = this;

      if (window.File && window.FileReader && window.FileList && window.Blob) {
        if (file_event.target.files.length) {
          var file = file_event.target.files[0];
          var fr = new FileReader();

          fr.onload = function (e) {
            if (_this.cropper) {
              _this.cropper.destroy();
            }

            $('#' + IDS_VALUT.WORKSPACE_ID).attr('src', e.target.result);
          };

          fr.onloadend = function (e) {
            _this.init_cropper();

            _this.css_manager.change_modal_visibility();
          };

          fr.readAsDataURL(file);
        }
      } else {
        throw Error('FileAPI is not supported');
      }
    }
  }, {
    key: "_clear_input",
    value: function _clear_input() {
      $('#' + IDS_VALUT.FILE_INPUT_ID).val('');
    }
  }, {
    key: "dismiss_current_image",
    value: function dismiss_current_image() {
      this._clear_input();

      this.cropper.destroy();
      this.css_manager.change_modal_visibility();
    }
  }, {
    key: "apply_current_image",
    value: function apply_current_image() {
      var h = this.dom_builder.widget_grain.height;
      var w = this.dom_builder.widget_grain.width;
      $(this.dom_builder.widget_grain).attr('src', this.cropper.getCroppedCanvas({
        width: 400
      }).toDataURL());
      $(this.dom_builder.widget_grain).attr('height', h);
      $(this.dom_builder.widget_grain).attr('width', w);
      this.css_manager.makeImvisible(IDS_VALUT.FILE_LABEL_ID);
      this.css_manager.makeImvisible(IDS_VALUT.FILE_INPUT_ID);
      this.css_manager.makeVisible(IDS_VALUT.SEND_B_ID);
      this.css_manager.makeVisible(IDS_VALUT.CANCEL_B_ID);
      this.cropper.destroy();

      this._clear_input();

      this.css_manager.change_modal_visibility();
    }
  }, {
    key: "cancel_cropping",
    value: function cancel_cropping() {
      $(this.dom_builder.widget_grain).attr('src', this.previous_image);

      this._clear_input();

      this.css_manager.makeImvisible(IDS_VALUT.CANCEL_B_ID);
      this.css_manager.makeImvisible(IDS_VALUT.SEND_B_ID);
      this.css_manager.makeVisible(IDS_VALUT.FILE_INPUT_ID);
      this.css_manager.makeVisible(IDS_VALUT.FILE_LABEL_ID);
    }
  }, {
    key: "send_cropped_image",
    value: function send_cropped_image() {
      this.set_previous_image(this.dom_builder.widget_grain.src);
      this.data_service.postThumbnail(this.previous_image);
      this.css_manager.makeVisible(IDS_VALUT.FILE_INPUT_ID);
      this.css_manager.makeImvisible(IDS_VALUT.SEND_B_ID);
      this.css_manager.makeImvisible(IDS_VALUT.CANCEL_B_ID);
    }
  }]);

  return CropTask;
}();

var CropWidget = /*#__PURE__*/function () {
  /**
   *
   * @param element: img html DOM element, widget grain and final destination
   * @param document_id id of resource. is used to build get and post requests
   * @param get_path: api endpoint path to get current thumbnail
   * @param prefetch_image: in case current/previous thumbnail is not API accessible provide its static url
   *
   */
  function CropWidget(element, document_id, get_path) {
    var prefetch_image = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : null;

    _classCallCheck(this, CropWidget);

    this.element = element;

    if (this.element.tagName !== 'IMG') {
      throw Error('Base element should be <img>');
    }

    this.dom_builder = new DomBuilder(this.element);
    this.css_manager = new CssManager();
    this.service = new ThumbnailService(document_id, get_path);
    this.crop = null;
    this.prefetch_image = prefetch_image;
  }

  _createClass(CropWidget, [{
    key: "init",
    value: function init() {
      this.crop = new CropTask(this.dom_builder, this.css_manager, this.service);

      if (this.prefetch_image === '') {
        this.element.src = '/static/geonode/img/missing_thumb.png';
        this.crop.init();
      } else if (this.prefetch_image === null || this.prefetch_image === undefined) {
        this.service.getThumbnail(this.element, this.crop.init.bind(this.crop));
      } else {
        this.element.src = this.prefetch_image;
        this.crop.init();
      }
    }
  }]);

  return CropWidget;
}();
//# sourceMappingURL=crop_widget_es5.js.map
