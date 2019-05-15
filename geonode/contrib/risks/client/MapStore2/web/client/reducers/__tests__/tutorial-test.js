/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */


const expect = require('expect');
const tutorial = require('../tutorial');
const React = require('react');
const I18N = require('../../components/I18N/I18N');

const {
    START_TUTORIAL,
    SETUP_TUTORIAL,
    UPDATE_TUTORIAL,
    DISABLE_TUTORIAL,
    RESET_TUTORIAL
} = require('../../actions/tutorial');

describe('Test the tutorial reducer', () => {

    it('default states tutorial', () => {
        const state = tutorial(undefined, {type: 'default'});
        expect(state.steps).toEqual([]);
        expect(state.run).toBe(false);
        expect(state.start).toBe(false);
        expect(state.intro).toBe(true);
        expect(state.progress).toBe(false);
        expect(state.skip).toBe(true);
        expect(state.nextLabel).toBe('start');
        expect(state.status).toBe('close');
        expect(state.disabled).toBe(false);
    });

    it('start the tutorial', () => {
        const state = tutorial({}, {
            type: START_TUTORIAL
        });
        expect(state.run).toBe(true);
        expect(state.start).toBe(true);
        expect(state.status).toBe('run');
    });

    it('setup the tutorial with empty steps', () => {
        const state = tutorial({}, {
            type: SETUP_TUTORIAL,
            steps: [],
            style: {},
            checkbox: 'checkbox',
            defaultStep: {}
        });

        expect(state.steps).toEqual([]);
        expect(state.run).toBe(false);
        expect(state.start).toBe(false);
        expect(state.intro).toBe(false);
        expect(state.progress).toBe(true);
        expect(state.skip).toBe(false);
        expect(state.nextLabel).toBe('next');
        expect(state.status).toBe('close');
    });

    it('setup the tutorial with one step', () => {
        const state = tutorial({}, {
            type: SETUP_TUTORIAL,
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#selector'
            }],
            style: {defaultStyle: {}, introStyle: {}},
            checkbox: 'checkbox',
            defaultStep: {}
        });

        expect(state.steps).toEqual([
            {
                title: 'test',
                text: 'test',
                selector: '#selector',
                style: {},
                isFixed: false
            }
        ]);
        expect(state.run).toBe(false);
        expect(state.start).toBe(false);
        expect(state.intro).toBe(false);
        expect(state.progress).toBe(true);
        expect(state.skip).toBe(false);
        expect(state.nextLabel).toBe('next');
        expect(state.status).toBe('close');
    });

    it('setup the tutorial with one intro step', () => {
        const state = tutorial({}, {
            type: SETUP_TUTORIAL,
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#intro-tutorial'
            }],
            style: {},
            checkbox: 'checkbox',
            defaultStep: {}
        });

        expect(state.steps).toEqual([
            {
                title: 'test',
                text: <div><div>{'test'}</div>{'checkbox'}</div>,
                selector: '#intro-tutorial',
                style: {},
                isFixed: true
            }
        ]);
        expect(state.run).toBe(true);
        expect(state.start).toBe(true);
        expect(state.intro).toBe(true);
        expect(state.progress).toBe(false);
        expect(state.skip).toBe(true);
        expect(state.nextLabel).toBe('start');
        expect(state.status).toBe('run');
    });

    it('setup the tutorial with intro, no selector, no title, no text and translation', () => {
        const state = tutorial({}, {
            type: SETUP_TUTORIAL,
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#intro-tutorial'
            },
            {
                title: 'test',
                text: 'test',
                selector: '#selector',
                isFixed: true
            },
            {
                title: 'test',
                text: 'test',
                selector: 'error'
            },
            {
                selector: '#selector'
            },
            {
                translation: 'test',
                selector: '#selector'
            }
            ],
            style: {},
            checkbox: 'checkbox',
            defaultStep: {}
        });

        expect(state.steps).toEqual([
            {
                title: 'test',
                text: <div><div>{'test'}</div>{'checkbox'}</div>,
                selector: '#intro-tutorial',
                style: {},
                isFixed: true
            },
            {
                title: 'test',
                text: 'test',
                selector: '#selector',
                style: {},
                isFixed: true
            },
            {
                title: '',
                text: '',
                selector: '#selector',
                style: {},
                isFixed: false
            },
            {
                title: <I18N.Message msgId = {"tutorial." + "test" + ".title"}/>,
                text: <I18N.Message msgId = {"tutorial." + "test" + ".text"}/>,
                selector: '#selector',
                style: {},
                isFixed: false,
                translation: 'test'
            }
        ]);
        expect(state.run).toBe(true);
        expect(state.start).toBe(true);
        expect(state.intro).toBe(true);
        expect(state.progress).toBe(false);
        expect(state.skip).toBe(true);
        expect(state.nextLabel).toBe('start');
        expect(state.status).toBe('run');
    });

    it('update the tutorial with tour undefined', () => {
        const state = tutorial({
            intro: true
        },
        {
            type: UPDATE_TUTORIAL,
            steps: [],
            error: {
                style: {},
                text: 'error'
            }
        });
        expect(state.run).toBe(true);
        expect(state.start).toBe(true);
        expect(state.status).toBe('run');
    });

    it('update the tutorial with different type', () => {
        const state = tutorial({
            intro: false
        },
        {
            type: UPDATE_TUTORIAL,
            tour: {
                action: 'skip',
                type: 'test'
            },
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#intro-tutorial'
            }],
            error: {
                style: {},
                text: 'error'
            }
        });
        expect(state.run).toBe(true);
        expect(state.start).toBe(true);
        expect(state.status).toBe('run');
    });


    it('update the tutorial with intro and tour close', () => {
        const state = tutorial({
            intro: true
        },
        {
            type: UPDATE_TUTORIAL,
            tour: {
                action: 'close',
                type: 'test'
            },
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#intro-tutorial'
            }],
            error: {
                style: {},
                text: 'error'
            }
        });

        expect(state.steps).toEqual([]);
        expect(state.run).toBe(false);
        expect(state.start).toBe(false);
        expect(state.intro).toBe(false);
        expect(state.progress).toBe(true);
        expect(state.skip).toBe(false);
        expect(state.nextLabel).toBe('next');
        expect(state.status).toBe('close');

    });

    it('update the tutorial with intro and tour next', () => {
        const state = tutorial({
            intro: true
        },
        {
            type: UPDATE_TUTORIAL,
            tour: {
                action: 'next',
                type: 'test'
            },
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#intro-tutorial'
            }],
            error: {
                style: {},
                text: 'error'
            }
        });

        expect(state.steps).toEqual([]);
        expect(state.run).toBe(true);
        expect(state.start).toBe(true);
        expect(state.intro).toBe(false);
        expect(state.progress).toBe(true);
        expect(state.skip).toBe(false);
        expect(state.nextLabel).toBe('next');
        expect(state.status).toBe('run');

    });

    it('update the tutorial with tour close', () => {
        const state = tutorial({
            intro: false
        },
        {
            type: UPDATE_TUTORIAL,
            tour: {
                action: 'close',
                type: 'test'
            },
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#intro-tutorial'
            }],
            error: {
                style: {},
                text: 'error'
            }
        });

        expect(state.steps).toEqual([]);
        expect(state.run).toBe(false);
        expect(state.start).toBe(false);
        expect(state.status).toBe('close');
    });

    it('update the tutorial with tour error', () => {
        const state = tutorial({
            intro: false
        },
        {
            type: UPDATE_TUTORIAL,
            tour: {
                action: 'next',
                type: 'error:target_not_found',
                index: 2
            },
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#intro-tutorial'
            },
            {
                title: 'test',
                text: 'test',
                selector: '#error-tutorial'
            },
            {
                title: 'test',
                text: 'test',
                selector: '#error'
            }],
            error: {
                style: {},
                text: 'error'
            }
        });

        expect(state.steps).toEqual([{
            title: 'test',
            text: 'error',
            selector: '#error-tutorial',
            position: 'top',
            style: {}
        }]);
        expect(state.run).toBe(true);
        expect(state.start).toBe(true);
        expect(state.status).toBe('error');
    });

    it('update the tutorial with tour error and no action error', () => {
        const state = tutorial({
            intro: false
        },
        {
            type: UPDATE_TUTORIAL,
            tour: {
                action: 'next',
                type: 'error:target_not_found',
                index: 3
            },
            steps: [{
                title: 'test',
                text: 'test',
                selector: '#intro-tutorial'
            },
            {
                title: 'test',
                text: 'test',
                selector: '#selector'
            },
            {
                title: 'test',
                text: 'test',
                selector: '#error-tutorial'
            },
            {
                title: 'test',
                text: 'test',
                selector: '#error'
            }]
        });

        expect(state.steps).toEqual([{
            title: 'test',
            text: '',
            selector: '#error-tutorial',
            position: 'top',
            style: {}
        },
        {
            title: 'test',
            text: 'test',
            selector: '#selector'
        }]);
        expect(state.run).toBe(true);
        expect(state.start).toBe(true);
        expect(state.status).toBe('error');
    });

    it('disable the tutorial', () => {
        const state = tutorial({
            disabled: true
        }, {
            type: DISABLE_TUTORIAL
        });
        expect(state.disabled).toBe(false);
    });

    it('reset the tutorial', () => {
        const state = tutorial({}, {
            type: RESET_TUTORIAL
        });
        expect(state.steps).toEqual([]);
        expect(state.run).toBe(false);
        expect(state.start).toBe(false);
        expect(state.intro).toBe(true);
        expect(state.progress).toBe(false);
        expect(state.skip).toBe(true);
        expect(state.nextLabel).toBe('start');
        expect(state.status).toBe('close');
    });

});
