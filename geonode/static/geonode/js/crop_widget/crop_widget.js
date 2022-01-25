const IDS_VALUT = {
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
}


class ThumbnailService {

    constructor(document_id, get_path) {
        this.document_id = document_id;
        this.get_path = get_path;
    }

    postThumbnail(base64_url) {
        const formData = new FormData();
        formData.append("file", this._b64toBlob(base64_url), 'blob.png');
        const url = location.origin + '/api/v2/resources/' + String(this.document_id) + '/set_thumbnail';
        $.ajax({
            url: url,
            data: formData,
            type: 'PUT',
            contentType: false,
            processData: false,
            headers: {
                "X-CSRFToken": this._getCookie('csrftoken')
            },
            success: () => {
                location.reload();
            },
            error: () => {
                throw Error('Cannot upload new thumbnail');
            }
        });
    }

    _getCookie(name) {
        const value = "; " + document.cookie;
        const parts = value.split("; " + name + "=");
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
    }

    getThumbnail(image_element, callback = null) {
        const url = location.origin + this.get_path + String(this.document_id);
        return $.ajax({
            url: url,
            type: 'GET',
            contentType: false,
            processData: false,
            headers: {
                "X-CSRFToken": this._getCookie('csrftoken')
            },
            success: (data) => {
                if (data && data.thumbnail_url) {
                    image_element.src = data.thumbnail_url;
                } else {
                    image_element.src = '/static/geonode/img/missing_thumb.png';
                }
                if (callback !== null) {
                    callback();
                }
            },
            error: () => {
                image_element.src = '/static/geonode/img/missing_thumb.png';
            }
        });

    }

    _b64toBlob(b64Data, contentType, sliceSize = 512) {
        contentType = contentType || '';
        b64Data = b64Data.split(',')[1];

        const byteCharacters = atob(b64Data);
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            const slice = byteCharacters.slice(offset, offset + sliceSize);

            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }

            const byteArray = new Uint8Array(byteNumbers);

            byteArrays.push(byteArray);
        }

        return new Blob(byteArrays, {type: contentType});
    }
}

class CssManager {

    makeVisible(dom_elem_id) {
        $('#' + dom_elem_id).removeClass('invisible');
    }

    makeImvisible(dom_elem_id) {
        $('#' + dom_elem_id).addClass('invisible');
    }

    change_modal_visibility() {
        if ($('#' + IDS_VALUT.FILE_INPUT_ID).val()) {
            $('#' + IDS_VALUT.WORKSPACE_CONTAINER_ID).removeClass('invisible');
            $('#' + IDS_VALUT.MODAL_OVERLAY_ID).removeClass('invisible');
        } else {
            $('#' + IDS_VALUT.WORKSPACE_CONTAINER_ID).addClass('invisible');
            $('#' + IDS_VALUT.MODAL_OVERLAY_ID).addClass('invisible');
        }
    }
}

class DomBuilder {
    // class too manage building required dom to display cropper

    constructor(widget_grain) {
        this.widget_grain = widget_grain;
        $(this.widget_grain).wrap(() => `<div id=${IDS_VALUT.GRAIN_WRAP_ID} class=crop-widget></div>`);
        $(this.widget_grain).wrap(() => ``);

        this.grain_wrapper = $('#' + IDS_VALUT.GRAIN_WRAP_ID);
        this.grain_wrapper.append(`<div id=${IDS_VALUT.MODAL_OVERLAY_ID} class="crop-modal-overlay invisible"></div>`);
        this.grain_wrapper.prepend(`<div class="thumbnail-title">Thumbnail</div>`);

    }

    _create_flow_buttons() {
        this.grain_wrapper.append(`<input type=file id=${IDS_VALUT.FILE_INPUT_ID} name=files class=crop-input /> `);
        this.grain_wrapper.append(`<label id=${IDS_VALUT.FILE_LABEL_ID} for=${IDS_VALUT.FILE_INPUT_ID} class="btn btn-default crop-input-label">Choose file</label>`);
        this.grain_wrapper.append(`<button type=button id=${IDS_VALUT.SEND_B_ID} class=\"btn btn-default invisible\">Save</button><button type=button id=${IDS_VALUT.CANCEL_B_ID} class="btn btn-default invisible">Cancel</button>`);

    }

    create_workspace() {
        const workspace_html = `
                              <div id=${IDS_VALUT.WORKSPACE_CONTAINER_ID} class="crop-modal-container invisible">                                  
                                  <img id=${IDS_VALUT.WORKSPACE_ID} class="crop-modal-workspace">                                      
                                  <button type=button id=${IDS_VALUT.OK_B_ID} class="btn btn-default">OK</button><button type=button id=${IDS_VALUT.DISMISS_B_ID} class="btn btn-default">Dismiss</button>                                      
                              </div>`;


        $(document.body).append(workspace_html);
        this._create_flow_buttons();

    }

}

class CropTask {

    constructor(dom_builder, css_manager, data_service) {
        this.dom_builder = dom_builder;
        this.css_manager = css_manager;
        this.previous_image = null;
        this.data_service = data_service;
    }

    init_cropper() {
        this.cropper = new Cropper($('#' + IDS_VALUT.WORKSPACE_ID)[0], {
            aspectRatio: 4 / 3,
            crop(event) {
            },
        });
    }

    set_previous_image(image_src) {
        this.previous_image = image_src;
    }

    init() {
        this.dom_builder.create_workspace();
        $('#' + IDS_VALUT.FILE_INPUT_ID).on('change', this.load_start_image.bind(this));
        $('#' + IDS_VALUT.DISMISS_B_ID).on('click', this.dismiss_current_image.bind(this));
        $('#' + IDS_VALUT.OK_B_ID).on('click', this.apply_current_image.bind(this));

        $('#' + IDS_VALUT.CANCEL_B_ID).on('click', this.cancel_cropping.bind(this));
        $('#' + IDS_VALUT.SEND_B_ID).on('click', this.send_cropped_image.bind(this));
        this.previous_image = this.dom_builder.widget_grain.src;
    }

    load_start_image(file_event) {
        if (window.File && window.FileReader && window.FileList && window.Blob) {

            if (file_event.target.files.length) {
                const file = file_event.target.files[0];
                const fr = new FileReader();

                fr.onload = (e) => {
                    if (this.cropper) {
                        this.cropper.destroy();
                    }
                    $('#' + IDS_VALUT.WORKSPACE_ID).attr('src', e.target.result);

                }
                fr.onloadend = (e) => {
                    this.init_cropper();
                    this.css_manager.change_modal_visibility();
                };
                fr.readAsDataURL(file);


            }
        } else {
            throw Error('FileAPI is not supported');
        }
    }

    _clear_input() {
        $('#' + IDS_VALUT.FILE_INPUT_ID).val('');
    }

    dismiss_current_image() {
        this._clear_input();
        this.cropper.destroy();
        this.css_manager.change_modal_visibility();

    }

    apply_current_image() {
        const h = this.dom_builder.widget_grain.height;
        const w = this.dom_builder.widget_grain.width;
        $(this.dom_builder.widget_grain).attr('src', this.cropper.getCroppedCanvas({
            width: 400,
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

    cancel_cropping() {
        $(this.dom_builder.widget_grain).attr('src', this.previous_image);
        this._clear_input();
        this.css_manager.makeImvisible(IDS_VALUT.CANCEL_B_ID);
        this.css_manager.makeImvisible(IDS_VALUT.SEND_B_ID);
        this.css_manager.makeVisible(IDS_VALUT.FILE_INPUT_ID);
        this.css_manager.makeVisible(IDS_VALUT.FILE_LABEL_ID);
    }

    send_cropped_image() {
        this.set_previous_image(this.dom_builder.widget_grain.src);
        this.data_service.postThumbnail(this.previous_image)
        this.css_manager.makeVisible(IDS_VALUT.FILE_INPUT_ID);
        this.css_manager.makeImvisible(IDS_VALUT.SEND_B_ID);
        this.css_manager.makeImvisible(IDS_VALUT.CANCEL_B_ID);
    }


}


class CropWidget {

    /**
     *
     * @param element: img html DOM element, widget grain and final destination
     * @param document_id id of resource. is used to build get and post requests
     * @param get_path: api endpoint path to get current thumbnail
     * @param prefetch_image: in case current/previous thumbnail is not API accessible provide its static url
     *
     */
    constructor(element, document_id, get_path, prefetch_image = null) {
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

    init() {
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
}


