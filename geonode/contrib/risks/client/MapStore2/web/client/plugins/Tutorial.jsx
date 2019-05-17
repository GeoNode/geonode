/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');
const {bindActionCreators} = require('redux');
const {setupTutorial, startTutorial, updateTutorial, disableTutorial, resetTutorial} = require('../actions/tutorial');
const {toggleControl, setControlProperty} = require('../actions/controls');
const presetList = require('./tutorial/preset');
const assign = require('object-assign');
const I18N = require('../components/I18N/I18N');
const {Glyphicon} = require('react-bootstrap');

/*
    //////////////////////////
    // TUTORIAL CONFIGURATION
    //////////////////////////

    PRESET AND RAW STEPS
    steps of the tutorial can be added as preset or rawSteps.
    Preset is a new .js file in the folder client/plugins/tutorial/preset while
    rawSteps is a cfg property of Tutorial in localConfig.json.
    Both are an array of "step object" * that represent the tutorial sequence.

    Preset must be required in the preset.js file (client/plugins/tutorial/preset.js)
    and declared in the cfg of Tutorial in localConfig.json (e.g. "preset": "NameOfThePresetFile").
    If not declared the default preset is "map".

    ! rawSteps overrides the preset file.

    * example array of "step object"
    [
        {
            translation: 'myIntroTranslation', //title and text of popup
            selector: '#intro-tutorial' //dom target id
        },
        {
            translation: 'myFirstStepTranslation',
            selector: '#first-selector'
        },
        {
            title: 'mySecondStepTitle',
            text: 'mySecondStepText',
            selector: '#second-selector',
            position: 'left' // popup position
        },
        ...
    ]

    AUTOSTART INTRODUCTION
    to show the tutorial with introduction and autostart
    the first step of the array, in the preset file or rawSteps property,
    must be an object with selector equal to '#intro-tutorial'.
    After the first run the tutorial can be activated again from the burger menu.

    custom preset file example
    module.exports = [
        {
            translation: 'myIntroTranslation',
            selector: '#intro-tutorial'
        },
        {
            translation: 'myFirstStepTranslation',
            selector: '#first-selector'
        },
        ...
    ];

    ACTIVATE MENU WITHOUT AUTOSTART
    to show the tutorial without introduction/autostart
    and to activate it from burger menu
    every selector must be different from '#intro-tutorial'

    custom preset file example
    module.exports = [
        {
            translation: 'myFirstStepTranslation',
            selector: '#first-selector'
        },
        {
            translation: 'mySecondStepTranslation',
            selector: '#second-selector'
        },
        ...
    ];

    SHOW CHECKBOX PROPERTY
    the showCheckbox property can be added to localConfig.json in the cfg of Tutorial section
    to display the checkbox that disable the autostart of tutorial
    value -> true/false
    default true

    ! works only whit introduction/autostart

    //////////////////////////
    // STEP PROPERTIES
    //////////////////////////

    SELECTORS
    every selector must be unique, start with # and different from '#error-tutorial'.

    TRANSLATION - TRANSLATION HTML
    to add the title and text of the step with property translation
    insert a new object in the translation file at the tutorial section
    with title and text properties

    steps example
    [
        {
            translation: 'myIntroTranslation',
            selector: '#intro-tutorial'
        },
        {
            translation: 'myFirstStepTranslation',
            selector: '#first-selector'
        },
        {
            translation: 'mySecondStepTranslation',
            selector: '#second-selector'
        },
        {
            translationHTML: 'myHTMLStepTranslation',
            selector: '#html-translation-selector'
        }
    ]

    translation file example
    ...
    "tutorial": {
        ...
        "myIntroTranslation": {
            "title": "My intro title",
            "text": "My intro description"
        },
        "myFirstStepTranslation": {
            "title": "My first step title",
            "text": "My first step description"
        },
        "mySecondStepTranslation": {
            "title": "My second step title",
            "text": "My second step description"
        },
        "myHTMLStepTranslation": {
            "title": "<div style="color:blue;">My html step title</div>",
            "text": "<div style="color:red;">My html step description</div>"
        }
        ...
    }
    ...

    TITLE AND TEXT PROPERTIES
    title and text can be added directly
    to the step object

    ! they override the translation property

    step example
    {
        title: 'My title',
        text: 'My description',
        selector: '#my-selector'
    }

    OTHER JOYRIDE STANDARD STEP PROPERTIES
    position: Relative position of you beacon and tooltip. It can be one of these:top, top-left, top-right, bottom, bottom-left, bottom-right, right and left. This defaults to bottom.
    type: The event type that trigger the tooltip: click or hover. Defaults to click
    isFixed: If true, the tooltip will remain in a fixed position within the viewport. Defaults to false.
    allowClicksThruHole: Set to true to allow pointer-events (hover, clicks, etc) or touch events within overlay hole. If true, the hole:click callback will not be sent. Defaults to false. Takes precedence over a allowClicksThruHole prop provided to <Joyride />
    style: An object with stylesheet options.
*/

const Tutorial = connect((state) => {
    return {
        toggle: state.controls && state.controls.tutorial && state.controls.tutorial.enabled,
        intro: state.tutorial && state.tutorial.intro,
        steps: state.tutorial && state.tutorial.steps,
        run: state.tutorial && state.tutorial.run,
        autoStart: state.tutorial && state.tutorial.start,
        showStepsProgress: state.tutorial && state.tutorial.progress,
        showSkipButton: state.tutorial && state.tutorial.skip,
        nextLabel: state.tutorial && state.tutorial.nextLabel,
        status: state.tutorial && state.tutorial.status,
        presetList
    };
}, (dispatch) => {
    return {
        actions: bindActionCreators({
            onSetup: setupTutorial,
            onStart: startTutorial,
            onUpdate: updateTutorial,
            onDisable: disableTutorial,
            onReset: resetTutorial,
            onClose: setControlProperty.bind(null, 'tutorial', 'enabled', false)
        }, dispatch)
    };
})(require('../components/tutorial/Tutorial'));

module.exports = {
    TutorialPlugin: assign(Tutorial, {
        BurgerMenu: {
            name: 'tutorial',
            position: 1000,
            text: <I18N.Message msgId="tutorial.title"/>,
            icon: <Glyphicon glyph="book"/>,
            action: toggleControl.bind(null, 'tutorial', null),
            priority: 2,
            doNotHide: true
        }
    }),
    reducers: {
        tutorial: require('../reducers/tutorial')
    }
};
