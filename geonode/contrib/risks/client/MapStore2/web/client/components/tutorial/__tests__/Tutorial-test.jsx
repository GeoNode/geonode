/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const React = require('react');
const ReactDOM = require('react-dom');
const Tutorial = require('../Tutorial');
const I18N = require('../../I18N/I18N');

const rawSteps = [
    {
        title: 'raw',
        text: 'test',
        selector: '#intro-tutorial'
    }
];

const presetList = {
    test: [
        {
            title: 'test',
            text: 'test',
            selector: '#intro-tutorial'
        }
    ]
};

const actions = {
    onSetup: () => {
        return true;
    },
    onStart: () => {
        return true;
    },
    onUpdate: () => {
        return true;
    },
    onDisable: () => {
        return true;
    },
    onReset: () => {
        return true;
    },
    onClose: () => {
        return true;
    }
};

describe("Test the Tutorial component", () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        expect.restoreSpies();
        setTimeout(done);
    });

    it('test component default actions', () => {
        const cmp = ReactDOM.render(<Tutorial/>, document.getElementById("container"));
        expect(cmp).toExist();

        cmp.props.actions.onSetup();
        cmp.props.actions.onStart();
        cmp.props.actions.onUpdate();
        cmp.props.actions.onDisable();
        cmp.props.actions.onReset();
        cmp.props.actions.onClose();
    });

    it('test component with no steps', () => {
        const spySetup = expect.spyOn(actions, 'onSetup');
        const spyClose = expect.spyOn(actions, 'onClose');
        const spyStart = expect.spyOn(actions, 'onStart');
        const spyUpdate = expect.spyOn(actions, 'onUpdate');

        const cmp = ReactDOM.render(<Tutorial introStyle={{}} defaultStep={{}} showCheckbox={false} actions={actions}/>, document.getElementById("container"));
        expect(cmp).toExist();

        expect(spySetup).toHaveBeenCalled();
        expect(spySetup).toHaveBeenCalledWith([], {}, <div id="tutorial-intro-checkbox-container"/>, {});

        const domNode = ReactDOM.findDOMNode(cmp);
        expect(domNode).toExist();
        expect(domNode.children.length).toBe(3);

        const joyridePlaceholder = domNode.getElementsByClassName('tutorial-joyride-placeholder');
        expect(joyridePlaceholder).toExist();
        expect(joyridePlaceholder.length).toBe(1);

        const introError = domNode.getElementsByClassName('tutorial-presentation-position');
        expect(introError).toExist();
        expect(introError.length).toBe(2);

        cmp.componentWillUpdate();
        expect(spyClose).toNotHaveBeenCalled();
        expect(spyStart).toNotHaveBeenCalled();

        cmp.onTour();
        expect(spyUpdate).toNotHaveBeenCalled();
    });

    it('test component with preset steps', () => {
        const spySetup = expect.spyOn(actions, 'onSetup');
        const spyClose = expect.spyOn(actions, 'onClose');
        const spyStart = expect.spyOn(actions, 'onStart');
        const spyUpdate = expect.spyOn(actions, 'onUpdate');
        const spyReset = expect.spyOn(actions, 'onReset');

        const cmp = ReactDOM.render(<Tutorial introStyle={{}} error={{}} steps={presetList.test} preset={'test'} presetList={presetList} defaultStep={{}} showCheckbox={true} actions={actions}/>, document.getElementById("container"));
        expect(cmp).toExist();

        expect(spySetup).toHaveBeenCalled();
        expect(spySetup).toHaveBeenCalledWith(presetList.test, {}, <div id="tutorial-intro-checkbox-container"><input type="checkbox" id="tutorial-intro-checkbox" className="tutorial-tooltip-intro-checkbox" onChange={cmp.props.actions.onDisable}/><span><I18N.Message msgId={"tutorial.checkbox"}/></span></div>, {});

        const domNode = ReactDOM.findDOMNode(cmp);
        expect(domNode).toExist();
        expect(domNode.children.length).toBe(3);

        const joyride = domNode.getElementsByClassName('joyride');
        expect(joyride).toExist();
        expect(joyride.length).toBe(1);

        const introError = domNode.getElementsByClassName('tutorial-presentation-position');
        expect(introError).toExist();
        expect(introError.length).toBe(2);

        cmp.componentWillUpdate({toggle: true});
        expect(spyStart).toHaveBeenCalled();

        cmp.componentWillUpdate({status: 'close'});
        expect(spyClose).toHaveBeenCalled();

        cmp.onTour({type: 'step:next'});
        expect(spyUpdate).toHaveBeenCalled();
        expect(spyUpdate).toHaveBeenCalledWith({type: 'step:next'}, presetList.test, {});

        cmp.componentWillUnmount();
        expect(spyReset).toHaveBeenCalled();
    });

    it('test component with raw steps', () => {
        const spySetup = expect.spyOn(actions, 'onSetup');
        const spyClose = expect.spyOn(actions, 'onClose');
        const spyStart = expect.spyOn(actions, 'onStart');
        const spyUpdate = expect.spyOn(actions, 'onUpdate');

        const cmp = ReactDOM.render(<Tutorial introStyle={{}} rawSteps={rawSteps} error={{}} steps={rawSteps} preset={'test'} presetList={presetList} defaultStep={{}} showCheckbox={false} actions={actions}/>, document.getElementById("container"));
        expect(cmp).toExist();

        expect(spySetup).toHaveBeenCalled();
        expect(spySetup).toHaveBeenCalledWith(rawSteps, {}, <div id="tutorial-intro-checkbox-container"/>, {});

        const domNode = ReactDOM.findDOMNode(cmp);
        expect(domNode).toExist();
        expect(domNode.children.length).toBe(3);

        const joyride = domNode.getElementsByClassName('joyride');
        expect(joyride).toExist();
        expect(joyride.length).toBe(1);

        const introError = domNode.getElementsByClassName('tutorial-presentation-position');
        expect(introError).toExist();
        expect(introError.length).toBe(2);

        cmp.componentWillUpdate({status: 'error'});
        expect(spyStart).toHaveBeenCalled();

        cmp.componentWillUpdate({status: 'run'});
        expect(spyClose).toNotHaveBeenCalled();

        cmp.onTour({type: 'step:next'});
        expect(spyUpdate).toHaveBeenCalled();
        expect(spyUpdate).toHaveBeenCalledWith({type: 'step:next'}, rawSteps, {});
    });

    it('test component with error on update', () => {
        const spyClose = expect.spyOn(actions, 'onClose');
        const spyStart = expect.spyOn(actions, 'onStart');

        const cmp = ReactDOM.render(<Tutorial status={'error'} error={{}} steps={presetList.test} preset={'test'} presetList={presetList} defaultStep={{}} showCheckbox={true} actions={actions}/>, document.getElementById("container"));
        expect(cmp).toExist();

        cmp.componentWillUpdate({status: 'error'});

        expect(spyStart).toHaveBeenCalled();
        expect(spyClose).toNotHaveBeenCalled();
    });

    it('test component with no data on update', () => {
        const spyClose = expect.spyOn(actions, 'onClose');
        const spyStart = expect.spyOn(actions, 'onStart');

        const cmp = ReactDOM.render(<Tutorial steps={presetList.test} preset={'test'} presetList={presetList} defaultStep={{}} showCheckbox={true} actions={actions}/>, document.getElementById("container"));
        expect(cmp).toExist();

        cmp.componentWillUpdate({});

        expect(spyStart).toNotHaveBeenCalled();
        expect(spyClose).toNotHaveBeenCalled();
    });
});
