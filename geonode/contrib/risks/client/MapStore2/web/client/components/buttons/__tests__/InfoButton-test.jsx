/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var InfoButton = require('../InfoButton');
var expect = require('expect');

describe('This test for InfoButton', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    // test DEFAULTS
    it('creates the component with defaults', () => {
        const about = ReactDOM.render(<InfoButton/>, document.getElementById("container"));
        expect(about).toExist();

        const aboutDom = ReactDOM.findDOMNode(about);
        expect(aboutDom).toExist();
        expect(aboutDom.id).toExist();

        const btnList = aboutDom.getElementsByTagName('button');
        expect(btnList.length).toBe(1);

        const btn = btnList.item(0);
        expect(btn.className).toBe("btn btn-md btn-info");
        expect(btn.innerText).toBe("Info");
    });

    it('checks if a click on button shows a modal window', () => {
        const about = ReactDOM.render(<InfoButton modalOptions={{animation: false}}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);
        btn.click();

        const modalDivList = document.getElementsByClassName("modal-content");
        expect(modalDivList.length).toBe(1);

    });

    it('checks if a click on window button hides the window itself', () => {
        const about = ReactDOM.render(<InfoButton modalOptions={{animation: false}}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);
        btn.click();

        const modalDivList = document.getElementsByClassName("modal-content");
        const closeBtnList = modalDivList.item(0).getElementsByTagName('button');
        expect(closeBtnList.length).toBe(1);

        const closeBtn = closeBtnList.item(0);
        closeBtn.click();

        expect(document.getElementsByClassName('fade in modal').length).toBe(0);
    });

    it('checks the default content of the modal window', () => {
        const about = ReactDOM.render(<InfoButton modalOptions={{animation: false}}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);
        btn.click();

        const modalDivList = document.getElementsByClassName("modal-content");
        const modalDiv = modalDivList.item(0);

        const headerList = modalDiv.getElementsByClassName("modal-header");
        expect(headerList.length).toBe(1);

        const titleList = headerList.item(0).getElementsByClassName("modal-title");
        expect(titleList.length).toBe(1);
        expect(titleList.item(0).innerHTML).toBe("Info");

        const bodyList = modalDiv.getElementsByClassName("modal-body");
        expect(bodyList.length).toBe(1);
        expect(bodyList.item(0).innerHTML).toBe("");
    });

    // test CUSTOM
    it('checks the custom id', () => {
        const customID = 'id-test';
        const about = ReactDOM.render(<InfoButton id={customID}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        expect(aboutDom.id).toBe(customID);
    });

    it('checks the custom button text', () => {
        const customText = 'btnText';
        const about = ReactDOM.render(<InfoButton text={customText}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);

        expect(btn.innerText).toBe(customText);
    });

    it('checks the button icon', () => {
        const icon = 'info-sign';
        const about = ReactDOM.render(<InfoButton glyphicon={icon}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);
        const btnItems = btn.getElementsByTagName("span");
        expect(btnItems.length).toBe(1);
        expect(btnItems.item(0).className).toBe("glyphicon glyphicon-" + icon);
        expect(btn.innerText.indexOf("Info") !== -1).toBe(true);
    });

    it('checks if the button contains only icon', () => {
        const icon = 'info-sign';
        const about = ReactDOM.render(<InfoButton glyphicon={icon} hiddenText/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);
        const btnItems = btn.getElementsByTagName("span");
        expect(btnItems.length).toBe(1);
        expect(btnItems.item(0).className).toBe("glyphicon glyphicon-" + icon);
        expect(btn.innerText).toBe("");
    });

    it('checks if the button contains at least the default text', () => {
        const about = ReactDOM.render(<InfoButton hiddenText/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);

        expect(btn.innerText).toBe("Info");
    });

    it('checks if the button contains at least the custom text', () => {
        const customText = "testText";
        const about = ReactDOM.render(<InfoButton hiddenText text={customText}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);

        expect(btn.innerText).toBe(customText);
    });

    it('checks the custom title for the window', () => {
        const customTitle = "testTitle";
        const about = ReactDOM.render(<InfoButton modalOptions={{animation: false}} title={customTitle}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);
        btn.click();

        const modalDiv = document.getElementsByClassName("modal-content").item(0);
        const headerList = modalDiv.getElementsByClassName("modal-header");
        const titleDom = headerList.item(0).getElementsByClassName("modal-title").item(0);

        expect(titleDom.innerHTML).toBe(customTitle);
    });

    it('checks the custom body for the window', () => {
        const customBody = "customBody";
        const about = ReactDOM.render(<InfoButton modalOptions={{animation: false}} body={customBody}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        const btn = aboutDom.getElementsByTagName('button').item(0);
        btn.click();

        const modalDiv = document.getElementsByClassName("modal-content").item(0);

        const bodyList = modalDiv.getElementsByClassName("modal-body");
        expect(bodyList.item(0).innerHTML).toBe(customBody);
    });

    it('checks the custom style', () => {
        const customStyle = {
            position: 'absolute',
            top: '5px',
            left: '1px'
        };
        const about = ReactDOM.render(<InfoButton style={customStyle}/>, document.getElementById("container"));
        const aboutDom = ReactDOM.findDOMNode(about);
        for (let p in customStyle) {
            if (customStyle.hasOwnProperty(p)) {
                expect(aboutDom.style[p]).toBe(customStyle[p]);
            }
        }
    });

    it('creates the component with a ImageButton', () => {
        const about = ReactDOM.render(<InfoButton btnType="image"/>, document.getElementById("container"));
        expect(about).toExist();
        const aboutDom = ReactDOM.findDOMNode(about);
        expect(aboutDom.getElementsByTagName('button').length).toBe(0);
        expect(aboutDom.getElementsByTagName('img').length).toBe(1);
    });
});
