/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var React = require('react');
var ReactDOM = require('react-dom');
var SearchBar = require('../SearchBar');

const TestUtils = require('react-addons-test-utils');

describe("test the SearchBar", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('test component creation', () => {
        const tb = ReactDOM.render(<SearchBar/>, document.getElementById("container"));
        expect(tb).toExist();
    });

    it('test search and reset on enter', () => {
        const renderSearchBar = (testHandlers, text) => {
            return ReactDOM.render(<SearchBar searchText={text} delay={0} typeAhead={false} onSearch={testHandlers.onSearchHandler} onSearchReset={testHandlers.onSearchResetHandler} onSearchTextChange={testHandlers.onSearchTextChangeHandler}/>, document.getElementById("container"));
        };

        var tb;
        const testHandlers = {
            onSearchHandler: (text) => { return text; },
            onSearchResetHandler: () => {}
        };
        testHandlers.onSearchTextChangeHandler = renderSearchBar.bind(null, testHandlers);

        const spy = expect.spyOn(testHandlers, 'onSearchHandler');
        const spyReset = expect.spyOn(testHandlers, 'onSearchResetHandler');
        tb = renderSearchBar(testHandlers);
        let input = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithTag(tb, "input")[0]);

        expect(input).toExist();
        input.value = "test";
        TestUtils.Simulate.change(input);
        TestUtils.Simulate.keyDown(input, {key: "Enter", keyCode: 13, which: 13});
        expect(spy.calls.length).toEqual(1);
        input.value = "";
        TestUtils.Simulate.change(input);
        TestUtils.Simulate.keyDown(input, {key: "Enter", keyCode: 13, which: 13});
        expect(spyReset.calls.length).toEqual(1);
    });

    it('test search and reset buttons', () => {
        var tb;

        const renderSearchBar = (testHandlers, text) => {
            return ReactDOM.render(<SearchBar searchText={text} delay={0} typeAhead={false} onSearch={testHandlers.onSearchHandler} onSearchReset={testHandlers.onSearchResetHandler} onSearchTextChange={testHandlers.onSearchTextChangeHandler}/>, document.getElementById("container"));
        };

        const testHandlers = {
            onSearchHandler: (text) => { return text; }
        };
        testHandlers.onSearchResetHandler = renderSearchBar.bind(null, testHandlers, '');
        testHandlers.onSearchTextChangeHandler = renderSearchBar.bind(null, testHandlers);

        const spyReset = expect.spyOn(testHandlers, 'onSearchResetHandler');
        spyReset.andCallThrough();
        tb = renderSearchBar(testHandlers);
        let input = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithTag(tb, "input")[0]);
        // test reset button
        expect(input).toExist();
        input.value = "test";
        TestUtils.Simulate.change(input);
        let reset = TestUtils.findRenderedDOMComponentWithClass(tb, "searchclear");
        expect(reset).toExist();
        TestUtils.Simulate.click(reset);
        expect(spyReset.calls.length).toEqual(1);
        expect(input.value).toEqual("");

    });

    it('test typeahead', (done) => {
        var tb;

        const renderSearchBar = (testHandlers, text) => {
            return ReactDOM.render(<SearchBar searchText={text} delay={0} typeAhead={true} onSearch={testHandlers.onSearchHandler} onSearchReset={testHandlers.onSearchResetHandler} onSearchTextChange={testHandlers.onSearchTextChangeHandler}/>, document.getElementById("container"));
        };

        const testHandlers = {
            onSearchHandler: (text) => { return text; }
        };
        testHandlers.onSearchTextChangeHandler = renderSearchBar.bind(null, testHandlers);

        const spy = expect.spyOn(testHandlers, 'onSearchHandler');
        tb = renderSearchBar(testHandlers);
        let input = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithTag(tb, "input")[0]);

        expect(input).toExist();
        input.value = "test";
        TestUtils.Simulate.change(input);
        setTimeout(() => {expect(spy.calls.length).toEqual(1); done(); }, 50);
    });

    it('test focus and blur events', (done) => {
        const testHandlers = {
            onSearchHandler: (text) => {return text; },
            onPurgeResultsHandler: () => {}
        };

        const spy = expect.spyOn(testHandlers, 'onSearchHandler');
        const spyReset = expect.spyOn(testHandlers, 'onPurgeResultsHandler');
        let tb = ReactDOM.render(<SearchBar searchText="test" delay={0} typeAhead={true} blurResetDelay={0} onSearch={testHandlers.onSearchHandler} onPurgeResults={testHandlers.onPurgeResultsHandler}/>, document.getElementById("container"));
        let input = TestUtils.scryRenderedDOMComponentsWithTag(tb, "input")[0];
        expect(input).toExist();
        input = ReactDOM.findDOMNode(input);
        input.value = "test";

        TestUtils.Simulate.click(input);
        TestUtils.Simulate.focus(input);
        TestUtils.Simulate.blur(input);
        setTimeout(() => {
            expect(spy.calls.length).toEqual(1);
            expect(spyReset.calls.length).toEqual(1);
            done();
        }, 50);
    });
    it('test autofocus on selected items', (done) => {
        let tb = ReactDOM.render(<SearchBar searchText="test" delay={0} typeAhead={true} blurResetDelay={0} />, document.getElementById("container"));
        let input = TestUtils.scryRenderedDOMComponentsWithTag(tb, "input")[0];
        expect(input).toExist();
        let spyOnFocus = expect.spyOn(input, 'focus');
        input = ReactDOM.findDOMNode(input);
        input.value = "test";
        TestUtils.Simulate.blur(input);
        ReactDOM.render(<SearchBar searchText="test" delay={0} typeAhead={true} blurResetDelay={0} selectedItems={[{text: "TEST"}]}/>, document.getElementById("container"));
        setTimeout(() => {
            expect(spyOnFocus.calls.length).toEqual(1);
            done();
        }, 210);
    });

    it('test that options are passed to search action', () => {
        var tb;
        let searchOptions = {displaycrs: "EPSG:3857"};

        const renderSearchBar = (testHandlers, text) => {
            return ReactDOM.render(<SearchBar searchOptions={searchOptions} searchText={text} delay={0} typeAhead={false} onSearch={testHandlers.onSearchHandler} onSearchReset={testHandlers.onSearchResetHandler} onSearchTextChange={testHandlers.onSearchTextChangeHandler}/>, document.getElementById("container"));
        };

        const testHandlers = {
            onSearchHandler: (text, options) => { return [text, options]; }
        };
        testHandlers.onSearchTextChangeHandler = renderSearchBar.bind(null, testHandlers);

        const spy = expect.spyOn(testHandlers, 'onSearchHandler');
        tb = renderSearchBar(testHandlers);
        let input = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithTag(tb, "input")[0]);

        expect(input).toExist();
        input.value = "test";
        TestUtils.Simulate.change(input);
        TestUtils.Simulate.keyDown(input, {key: "Enter", keyCode: 13, which: 13});
        expect(spy.calls.length).toEqual(1);
        expect(spy).toHaveBeenCalledWith('test', searchOptions);
    });
    it('test error and loading status', () => {
        const tb = ReactDOM.render(<SearchBar loading={true} error={{message: "TEST_ERROR"}}/>, document.getElementById("container"));
        expect(tb).toExist();
        let error = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithClass(tb, "searcherror")[0]);
        expect(error).toExist();
    });

    it('test cancel items', (done) => {
        const testHandlers = {
            onCancelSelectedItem: () => {}
        };

        const spy = expect.spyOn(testHandlers, 'onCancelSelectedItem');
        let tb = ReactDOM.render(<SearchBar searchText="test" delay={0} typeAhead={true} blurResetDelay={0} onCancelSelectedItem={testHandlers.onCancelSelectedItem} />, document.getElementById("container"));
        let input = TestUtils.scryRenderedDOMComponentsWithTag(tb, "input")[0];
        expect(input).toExist();
        input = ReactDOM.findDOMNode(input);

        // backspace with empty searchText causes trigger of onCancelSelectedItem
        ReactDOM.render(<SearchBar searchText="" delay={0} typeAhead={true} blurResetDelay={0} onCancelSelectedItem={testHandlers.onCancelSelectedItem} selectedItems={[{text: "TEST"}]}/>, document.getElementById("container"));
        TestUtils.Simulate.keyDown(input, {key: "Backspace", keyCode: 8, which: 8});
        setTimeout(() => {
            expect(spy.calls.length).toEqual(1);
            done();
        }, 10);
    });
});
