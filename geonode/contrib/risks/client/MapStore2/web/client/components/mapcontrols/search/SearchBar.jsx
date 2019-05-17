/*
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var {FormControl, FormGroup, Glyphicon, OverlayTrigger, Tooltip} = require('react-bootstrap');
var LocaleUtils = require('../../../utils/LocaleUtils');
var Spinner = require('react-spinkit');


var delay = (
    function() {
        var timer = 0;
        return function(callback, ms) {
        clearTimeout(timer);
        timer = setTimeout(callback, ms);
    };
    })();

require('./searchbar.css');

/**
 * Search Bar component. With typeAhead events
 * @memberof components.mapControls.search
 * @class
 * @prop {string} className the class to assign to the components
 * @prop {function} onSearch callback on search event
 * @prop {function} onPurgeResults triggered when the user clear
 * @prop {function} onSearchTextChange triggered when the text changes
 * @prop {function} onCancelSelectedItem triggered when the user deletes the selected item (by hitting backspace) when text is empty
 * @prop {string} placeholder string to use as placeholder when text is empty
 * @prop {string} placeholderMsgId msgId for the placeholder. Used if placeholder is not defined
 * @prop {number} delay milliseconds after trigger onSearch if typeAhead is true
 * @prop {boolean} hideOnBlur if true, it triggers onPurgeResults on blur
 * @prop {boolean} typeAhead if true, onSearch is triggered when users change the search text, after `delay` milliseconds
 * @prop {number} blurResetDelay time to wait before to trigger onPurgeResults after blur event, if `hideOnBlur` is true
 * @prop {searchText} the text to display in the component
 * @prop {object[]} selectedItems the items selected. Must have `text` property to display
 * @prop {boolean} autoFocusOnSelect if true, the comonent gets focus when items are added, or deleted but some item is still selected. Useful for continue writing after selecting an item (with nested services for instance)
 * @prop {boolean} loading if true, shows the loading tool
 * @prop {object} error if not null, an error icon will be display
 * @prop {object} style css style to apply to the component
 * @prop {object} options to pass to the search event
 *
 */
let SearchBar = React.createClass({
    propTypes: {
        className: React.PropTypes.string,
        onSearch: React.PropTypes.func,
        onSearchReset: React.PropTypes.func,
        onPurgeResults: React.PropTypes.func,
        onSearchTextChange: React.PropTypes.func,
        onCancelSelectedItem: React.PropTypes.func,
        placeholder: React.PropTypes.string,
        placeholderMsgId: React.PropTypes.string,
        delay: React.PropTypes.number,
        hideOnBlur: React.PropTypes.bool,
        blurResetDelay: React.PropTypes.number,
        typeAhead: React.PropTypes.bool,
        searchText: React.PropTypes.string,
        selectedItems: React.PropTypes.array,
        autoFocusOnSelect: React.PropTypes.bool,
        loading: React.PropTypes.bool,
        error: React.PropTypes.object,
        style: React.PropTypes.object,
        searchOptions: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            onSearch: () => {},
            onSearchReset: () => {},
            onPurgeResults: () => {},
            onSearchTextChange: () => {},
            onCancelSelectedItem: () => {},
            selectedItems: [],
            placeholderMsgId: "search.placeholder",
            delay: 1000,
            blurResetDelay: 300,
            autoFocusOnSelect: true,
            hideOnBlur: true,
            typeAhead: true,
            searchText: ""
        };
    },
    componentDidUpdate(prevProps) {
        let shouldFocus = this.props.autoFocusOnSelect && this.props.selectedItems &&
            (
                (prevProps.selectedItems && prevProps.selectedItems.length < this.props.selectedItems.length)
                || (!prevProps.selectedItems && this.props.selectedItems.length === 1)
            );
        if (shouldFocus) {
            this.focusToInput();
        }
    },
    onChange(e) {
        var text = e.target.value;
        this.props.onSearchTextChange(text);
        if (this.props.typeAhead) {
            delay(() => {this.search(); }, this.props.delay);
        }
    },
    onKeyDown(event) {
        switch (event.keyCode) {
            case 13:
                this.search();
                break;
            case 8:
                if (!this.props.searchText && this.props.selectedItems && this.props.selectedItems.length > 0) {
                    this.props.onCancelSelectedItem(this.props.selectedItems[this.props.selectedItems.length - 1]);
                }
                break;
            default:
        }
    },
    onFocus() {
        if (this.props.typeAhead ) {
            this.search();
        }
    },
    onBlur() {
        // delay this to make the click on result run anyway
        if (this.props.hideOnBlur) {
            delay(() => {this.props.onPurgeResults(); }, this.props.blurResetDelay);
        }
    },
    renderAddonBefore() {
        return this.props.selectedItems && this.props.selectedItems.map((item, index) =>
            <span key={"selected-item" + index} className="input-group-addon"><div className="selectedItem-text">{item.text}</div></span>
        );
    },
    renderAddonAfter() {
        const remove = <Glyphicon className="searchclear" glyph="remove" onClick={this.clearSearch} key="searchbar_remove_glyphicon"/>;
        var showRemove = this.props.searchText !== "" || (this.props.selectedItems && this.props.selectedItems.length > 0);
        let addonAfter = showRemove ? [remove] : [<Glyphicon glyph="search" key="searchbar_search_glyphicon"/>];
        if (this.props.loading) {
            addonAfter = [<Spinner style={{
                position: "absolute",
                right: "16px",
                top: "12px"
                }} spinnerName="pulse" noFadeIn/>, addonAfter];
        }
        if (this.props.error) {
            let tooltip = <Tooltip id="tooltip">{this.props.error && this.props.error.message || null}</Tooltip>;
            addonAfter.push(<OverlayTrigger placement="bottom" overlay={tooltip}><Glyphicon className="searcherror" glyph="warning-sign" onClick={this.clearSearch}/></OverlayTrigger>);
        }
        return <span className="input-group-addon">{addonAfter}</span>;
    },
    render() {
        //  const innerGlyphicon = <Button onClick={this.search}></Button>;
        let placeholder;
        if (!this.props.placeholder && this.context.messages) {
            let placeholderLocMessage = LocaleUtils.getMessageById(this.context.messages, this.props.placeholderMsgId);
            if (placeholderLocMessage) {
                placeholder = placeholderLocMessage;
            }
        } else {
            placeholder = this.props.placeholder;
        }

        return (
            <div id="map-search-bar" style={this.props.style} className={"MapSearchBar" + (this.props.className ? " " + this.props.className : "")}>
                <FormGroup>
                    <div className="input-group">
                        {this.renderAddonBefore()}
                        <FormControl
                        key="search-input"
                        placeholder={placeholder}
                        type="text"
                        inputRef={ref => { this.input = ref; }}
                        style={{
                            textOverflow: "ellipsis"
                        }}
                        value={this.props.searchText}
                        ref="input"
                        onKeyDown={this.onKeyDown}
                        onBlur={this.onBlur}
                        onFocus={this.onFocus}
                        onChange={this.onChange} />
                        {this.renderAddonAfter()}
                        </div>
                </FormGroup>
            </div>
        );
    },
    search() {
        var text = this.props.searchText;
        if ((text === undefined || text === "") && (!this.props.selectedItems || this.props.selectedItems.length === 0)) {
            this.props.onSearchReset();
        } else {
            this.props.onSearch(text, this.props.searchOptions);
        }

    },
    focusToInput() {
        let node = this.input;
        if (node && node.focus instanceof Function) {
            setTimeout( () => node.focus(), 200);
        }
    },
    clearSearch() {
        this.props.onSearchReset();
    }
});

module.exports = SearchBar;
