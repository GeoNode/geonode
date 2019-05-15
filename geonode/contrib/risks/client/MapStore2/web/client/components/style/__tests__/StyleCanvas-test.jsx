const expect = require('expect');
const React = require('react');
const ReactDOM = require('react-dom');
const StyleCanvas = require('../StyleCanvas');

let shapeStyle = {
    color: { r: 0, g: 0, b: 255, a: 1 },
    width: 3,
    fill: { r: 0, g: 0, b: 255, a: 0.1 },
    radius: 10,
    marker: false
};

describe("Test the StyleCanvas style component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });
    it('test component drawing polygon', () => {
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={shapeStyle} geomType="Polygon"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('test component drawing line', () => {
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={shapeStyle} geomType="Polyline"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });

    it('test component drawing point', () => {
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={shapeStyle} geomType="Point"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('test component drawing marker', () => {
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={shapeStyle} geomType="Marker"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('test component drawing point with circle mark', () => {
        let style = {...shapeStyle, markName: "circle"};
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={style} geomType="Point"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('test component drawing point with square mark', () => {
        let style = {...shapeStyle, markName: "square"};
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={style} geomType="Point"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('test component drawing point with triangle mark', () => {
        let style = {...shapeStyle, markName: "triangle"};
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={style} geomType="Point"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('test component drawing point with star mark', () => {
        let style = {...shapeStyle, markName: "star"};
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={style} geomType="Point"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('test component drawing point with cross mark', () => {
        let style = {...shapeStyle, markName: "cross"};
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={style} geomType="Point"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('test component drawing point with X mark', () => {
        let style = {...shapeStyle, markName: "x"};
        const cmp = ReactDOM.render(<StyleCanvas shapeStyle={style} geomType="Point"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
});
