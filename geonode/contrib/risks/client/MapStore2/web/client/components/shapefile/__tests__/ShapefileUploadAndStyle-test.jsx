const expect = require('expect');
const React = require('react');
const ReactDOM = require('react-dom');
const ShapefileUploadAndStyle = require('../ShapefileUploadAndStyle');

describe("Test the select shapefile component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates component with defaults', () => {
        const cmp = ReactDOM.render(<ShapefileUploadAndStyle/>, document.getElementById("container"));
        expect(cmp).toExist();
    });

    it('creates component loading', () => {
        const cmp = ReactDOM.render(<ShapefileUploadAndStyle loading={true} />, document.getElementById("container"));
        expect(cmp).toExist();
    });

});
