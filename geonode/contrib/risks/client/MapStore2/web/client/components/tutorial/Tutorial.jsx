/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Joyride = require('react-joyride').default;
const I18N = require('../I18N/I18N');

require('react-joyride/lib/react-joyride-compiled.css');
require('./style/tutorial.css');

const introStyle = {
    backgroundColor: 'transparent',
    color: '#fff',
    mainColor: '#fff',
    textAlign: 'center',
    header: {
        padding: 5,
        fontFamily: 'Georgia, serif',
        fontSize: '2.8em'
    },
    main: {
        fontSize: '1.0em',
        padding: 5
    },
    footer: {
        padding: 10
    },
    button: {
        color: '#fff',
        backgroundColor: '#078aa3'
    },
    close: {
        display: 'none'
    },
    skip: {
        color: '#fff'
    }
};

const errorStyle = {
    mainColor: '#888',
    backgroundColor: 'transparent',
    header: {
        fontFamily: 'Georgia, serif',
        fontSize: '1.5em',
        borderBottom: '1px solid #dd0733',
        backgroundColor: '#fff',
        padding: 10
    },
    main: {
        fontSize: '0.9em',
        backgroundColor: '#fff',
        padding: 10
    },
    footer: {
        backgroundColor: '#fff',
        padding: 10
    },
    button: {
        color: '#fff',
        backgroundColor: '#dd0733'
    },
    skip: {
        color: '#AAA'
    },
    close: {
        margin: 10
    }
};

const Tutorial = React.createClass({
    propTypes: {
        toggle: React.PropTypes.bool,
        status: React.PropTypes.string,
        preset: React.PropTypes.string,
        presetList: React.PropTypes.object,
        intro: React.PropTypes.bool,
        introPosition: React.PropTypes.number,
        rawSteps: React.PropTypes.array,
        nextLabel: React.PropTypes.string,
        showCheckbox: React.PropTypes.bool,
        defaultStep: React.PropTypes.object,
        introStyle: React.PropTypes.object,
        error: React.PropTypes.object,

        steps: React.PropTypes.array,
        stepIndex: React.PropTypes.number,
        run: React.PropTypes.bool,
        autoStart: React.PropTypes.bool,
        keyboardNavigation: React.PropTypes.bool,
        resizeDebounce: React.PropTypes.bool,
        resizeDebounceDelay: React.PropTypes.number,
        holePadding: React.PropTypes.number,
        scrollOffset: React.PropTypes.number,
        scrollToSteps: React.PropTypes.bool,
        scrollToFirstStep: React.PropTypes.bool,
        showBackButton: React.PropTypes.bool,
        showOverlay: React.PropTypes.bool,
        allowClicksThruHole: React.PropTypes.bool,
        showSkipButton: React.PropTypes.bool,
        showStepsProgress: React.PropTypes.bool,
        tooltipOffset: React.PropTypes.number,
        type: React.PropTypes.string,
        disableOverlay: React.PropTypes.bool,
        debug: React.PropTypes.bool,

        actions: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            toggle: false,
            status: 'run',
            preset: 'map',
            presetList: {},
            intro: true,
            introPosition: (window.innerHeight - 348) / 2,
            rawSteps: [],
            nextLabel: 'next',
            showCheckbox: true,
            defaultStep: {
                title: '',
                text: '',
                position: 'bottom',
                type: 'click',
                allowClicksThruHole: true
            },
            introStyle: introStyle,
            error: {
                style: errorStyle,
                text: <I18N.Message msgId="tutorial.error"/>
            },

            steps: [],
            stepIndex: 0,
            run: true,
            autoStart: true,
            keyboardNavigation: true,
            resizeDebounce: false,
            resizeDebounceDelay: 200,
            holePadding: 0,
            scrollOffset: 20,
            scrollToSteps: true,
            scrollToFirstStep: true,
            showBackButton: true,
            showOverlay: true,
            allowClicksThruHole: false,
            showSkipButton: false,
            showStepsProgress: true,
            tooltipOffset: 10,
            type: 'continuous',
            disableOverlay: false,
            debug: false,

            actions: {
                onSetup: () => {},
                onStart: () => {},
                onUpdate: () => {},
                onDisable: () => {},
                onReset: () => {},
                onClose: () => {}
            }
        };
    },
    componentWillMount() {
        let rawSteps = this.props.rawSteps.length > 0 ? this.props.rawSteps : this.props.presetList[this.props.preset] || [];
        let checkbox = this.props.showCheckbox ? <div id="tutorial-intro-checkbox-container"><input type="checkbox" id="tutorial-intro-checkbox" className="tutorial-tooltip-intro-checkbox" onChange={this.props.actions.onDisable}/><span><I18N.Message msgId={"tutorial.checkbox"}/></span></div> : <div id="tutorial-intro-checkbox-container"/>;
        this.props.actions.onSetup(rawSteps, this.props.introStyle, checkbox, this.props.defaultStep);
    },
    componentWillUpdate(newProps) {
        if (this.props.steps.length > 0) {
            if (!this.props.toggle && newProps.toggle
            || this.props.intro && !newProps.intro && newProps.status === 'run'
            || this.props.status === 'run' && newProps.status === 'error'
            || this.props.status === 'error' && newProps.status === 'error') {
                this.props.actions.onStart();
                this.joyride.reset(true);
            } else if (this.props.status === 'run' && newProps.status === 'close') {
                this.props.actions.onClose();
            }
        }
    },
    componentWillUnmount() {
        this.props.actions.onClose();
        this.props.actions.onReset();
    },
    onTour(tour) {
        if (this.props.steps.length > 0 && tour && tour.type && tour.type.split(':')[1] !== 'before') {
            this.props.actions.onUpdate(tour, this.props.steps, this.props.error);
        }
    },
    render() {
        let joy;
        if (this.props.steps.length > 0) {
            joy = (
                <Joyride
                    ref={c => (this.joyride = c)}
                    steps={this.props.steps}
                    stepIndex={this.props.stepIndex}
                    run={this.props.run}
                    autoStart={this.props.autoStart}
                    keyboardNavigation={this.props.keyboardNavigation}
                    locale={{
                        back: <I18N.Message msgId="tutorial.back"/>,
                        close: <I18N.Message msgId="tutorial.close"/>,
                        last: <I18N.Message msgId="tutorial.last"/>,
                        next: <I18N.Message msgId={'tutorial.' + this.props.nextLabel}/>,
                        skip: <I18N.Message msgId="tutorial.skip"/>
                    }}
                    resizeDebounce={this.props.resizeDebounce}
                    resizeDebounceDelay={this.props.resizeDebounceDelay}
                    holePadding={this.props.holePadding}
                    scrollOffset={this.props.scrollOffset}
                    scrollToSteps={this.props.scrollToSteps}
                    scrollToFirstStep={this.props.scrollToFirstStep}
                    showBackButton={this.props.showBackButton}
                    showOverlay={this.props.showOverlay}
                    allowClicksThruHole={this.props.allowClicksThruHole}
                    showSkipButton={this.props.showSkipButton}
                    showStepsProgress={this.props.showStepsProgress}
                    tooltipOffset={this.props.tooltipOffset}
                    type={this.props.type}
                    disableOverlay={this.props.disableOverlay}
                    debug={this.props.debug}
                    callback={this.onTour}
                />
            );
        } else {
            joy = (<div className="tutorial-joyride-placeholder"></div>);
        }
        return (
            <div>
                {joy}
                <div id="intro-tutorial" className="tutorial-presentation-position" style={{top: this.props.introPosition}}></div>
                <div id="error-tutorial" className="tutorial-presentation-position" style={{top: this.props.introPosition + 200}}></div>
            </div>

        );
    }
});

module.exports = Tutorial;
