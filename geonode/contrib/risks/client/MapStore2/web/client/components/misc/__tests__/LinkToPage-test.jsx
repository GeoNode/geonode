var expect = require('expect');
var React = require('react');
var ReactDOM = require('react-dom');
var LinkToPage = require('../LinkToPage');

describe("This test for LinkToPage component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates componet with defaults', () => {
        const cmp = ReactDOM.render(<LinkToPage/>, document.getElementById("container"));
        expect(cmp).toExist();
    });

    it('creates empty componet with url and params', () => {
        const cmp = ReactDOM.render(<LinkToPage url="testUrl" params={{a: "testA", b: "testB"}}/>, document.getElementById("container"));
        expect(cmp).toExist();
        let url = cmp.buildUrl();
        expect(url).toBe("testUrl" + encodeURI("?a=testA&b=testB&"));
    });
});
