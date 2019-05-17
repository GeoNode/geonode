/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    START_TUTORIAL,
    SETUP_TUTORIAL,
    UPDATE_TUTORIAL,
    DISABLE_TUTORIAL,
    RESET_TUTORIAL
} = require('../actions/tutorial');

const assign = require('object-assign');
const React = require('react');
const I18N = require('../components/I18N/I18N');

const initialState = {
    run: false,
    start: false,
    steps: [],
    intro: true,
    progress: false,
    disabled: false,
    skip: true,
    nextLabel: 'start',
    status: 'close'
};

function tutorial(state = initialState, action) {
    switch (action.type) {
        case START_TUTORIAL:
            return assign({}, state, {
                run: true,
                start: true,
                status: 'run'
            });
        case SETUP_TUTORIAL:
            let setup = {};
            setup.steps = assign([], action.steps);
            setup.steps = setup.steps.filter((step) => {
                return step.selector && step.selector.substring(0, 1) === '#';
            }).map((step) => {
                let title = step.title ? step.title : '';
                title = step.translation ? <I18N.Message msgId = {"tutorial." + step.translation + ".title"}/> : title;
                title = step.translationHTML ? <I18N.HTML msgId = {"tutorial." + step.translationHTML + ".title"}/> : title;
                let text = step.text ? step.text : '';
                text = step.translation ? <I18N.Message msgId = {"tutorial." + step.translation + ".text"}/> : text;
                text = step.translationHTML ? <I18N.HTML msgId = {"tutorial." + step.translationHTML + ".text"}/> : text;
                text = (step.selector === '#intro-tutorial') ? <div><div>{text}</div>{action.checkbox}</div> : text;
                let style = (step.selector === '#intro-tutorial') ? action.style : {};
                let isFixed = (step.selector === '#intro-tutorial') ? true : step.isFixed || false;
                assign(style, step.style);
                return assign({}, action.defaultStep, step, {
                    title,
                    text,
                    style,
                    isFixed
                });
            });

            let hasIntro = false;
            let isDisabled = localStorage.getItem('mapstore.plugin.tutorial.disabled');
            setup.run = false;
            setup.start = false;
            setup.intro = true;
            setup.progress = false;
            setup.skip = true;
            setup.nextLabel = 'start';
            setup.status = 'close';

            if (setup.steps.length > 1) {
                setup.steps.reduce(function(stepA, stepB) {

                    if (stepA.selector === '#intro-tutorial') {
                        hasIntro = true;
                    }
                    return stepB;
                });
            }else if (setup.steps.length === 1) {
                if (setup.steps[0].selector === '#intro-tutorial') {
                    hasIntro = true;
                }
            }

            if (isDisabled === 'true' || !hasIntro || setup.steps.length === 0) {
                setup.steps = setup.steps.filter((step) => {
                    return step.selector !== '#intro-tutorial';
                });

                setup.intro = false;
                setup.progress = true;
                setup.skip = false;
                setup.nextLabel = 'next';
            } else {
                setup.status = 'run';
                setup.run = true;
                setup.start = true;
            }

            return assign({}, state, setup);
        case UPDATE_TUTORIAL:
            let update = {};
            update.steps = assign([], action.steps);
            update.run = true;
            update.start = true;
            update.status = 'run';
            if (action.tour) {
                if (action.tour.action !== 'start' && state.intro) {
                    update.intro = false;
                    update.progress = true;
                    update.skip = false;
                    update.nextLabel = 'next';
                    if (action.tour.action !== 'next') {
                        update.run = false;
                        update.start = false;
                        update.status = 'close';
                    }
                    update.steps = update.steps.filter((step) => {
                        return step.selector !== '#intro-tutorial';
                    });
                } else if (action.tour.action === 'close' || action.tour.type === 'finished') {
                    update.run = false;
                    update.start = false;
                    update.steps = update.steps.filter((step) => {
                        return step.selector !== '#error-tutorial' && step.selector !== '#intro-tutorial';
                    });
                    update.status = 'close';
                } else if (action.tour.type === 'error:target_not_found') {
                    let errorStep = update.steps[action.tour.index];
                    let text = action.error && action.error.text || '';
                    let style = action.error && action.error.style || {};

                    update.steps = update.steps.filter((step) => {
                        return step.selector !== '#error-tutorial' && step.selector !== '#intro-tutorial';
                    });

                    let newErrorStep = assign({}, errorStep, {
                        selector: '#error-tutorial',
                        text: text,
                        position: 'top',
                        style: style
                    });
                    let index = update.steps.indexOf(errorStep);
                    if (index > 0) {
                        update.steps.splice(index, 1);
                        update.steps.unshift(newErrorStep);
                    } else {
                        update.steps[0] = newErrorStep;
                    }
                    update.status = 'error';
                }
            }
            return assign({}, state, update);
        case DISABLE_TUTORIAL:
            let disabled = !state.disabled;
            localStorage.setItem('mapstore.plugin.tutorial.disabled', disabled);
            return assign({}, state, {
                disabled
            });
        case RESET_TUTORIAL:
            return assign({}, state, {
                steps: [],
                intro: true,
                progress: false,
                skip: true,
                nextLabel: 'start',
                run: false,
                start: false,
                status: 'close'
            });
        default:
            return state;
    }
}

module.exports = tutorial;
