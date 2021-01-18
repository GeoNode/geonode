function get_users_data(data) {
    return data.objects.map((elem) => {
        return {value: elem.username, id: elem.id};
    });
}

function get_groups_data(data) {
    return data.objects.map((elem) => {
        return {value: elem.title, id: elem.id};
    });
}

class MessageRecipientsTags {
    constructor(input, data_extract_func, url, blacklist = []) {
        if (input.tagName !== 'INPUT' || input.type !== 'text') {
            throw Error('Base element should be <input type="text">');
        }
        this.input = input;
        this.tagify = null;
        this.data_extract_func = data_extract_func;
        this.url = url;
        this.blacklist = blacklist;
        this.request_controller = null;
    }

    init() {
        this.tagify = new Tagify(this.input, {whitelist: [], blacklist: this.blacklist});
        this.tagify.on('input', this._onInputHandler.bind(this));
        this.request_controller = new AbortController();
    }


    _onInputHandler(event) {
        const value = event.detail.value;
        this.tagify.settings.whitelist.length = 0;

        this.tagify.loading(true).dropdown.hide.call(this.tagify);
        this.request_controller.abort();
        this.request_controller = new AbortController();

        fetch(this.url + value, {signal:this.request_controller.signal}).then(response =>
            response.json()
                .then(this.data_extract_func)
                .then(res => {
                    res = res.filter(elem => {
                        if (!(this.blacklist.includes(elem.value))) {
                            return elem;
                        }
                    });
                    this.tagify.settings.whitelist.splice(0, res.length, ...res);
                    this.tagify.loading(false).dropdown.show.call(this.tagify, value);
                }));
    }

    fixOutputValue() {
        if (this.input.value !== '') {
            JSON.parse(this.input.value).filter(elem => 'id' in elem).forEach((elem) => {
                $('<input>').attr({
                    type: 'hidden',
                    id: 'foo',
                    name: this.input.name,
                    value: elem.id
                }).appendTo('form');
            });
        }
        this.input.disabled = true;
    }
}

