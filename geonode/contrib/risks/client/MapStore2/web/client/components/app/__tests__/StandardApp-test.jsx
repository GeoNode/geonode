/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');
const React = require('react');
const ReactDOM = require('react-dom');

const StandardApp = require('../StandardApp');

const ConfigUtils = require('../../../utils/ConfigUtils');

const mycomponent = React.createClass({
    propTypes: {
        plugins: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            plugins: {}
        };
    },
    renderPlugins() {
        return Object.keys(this.props.plugins).map((plugin) => <div className={plugin}/>);
    },
    render() {
        return (<div className="mycomponent">
                {this.renderPlugins()}
                </div>);
    }
});

describe('StandardApp', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        ConfigUtils.setLocalConfigurationFile('base/web/client/test-resources/localConfig.json');
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        ConfigUtils.setLocalConfigurationFile('localConfig.json');
        setTimeout(done);
    });

    it('creates a default app', () => {
        const app = ReactDOM.render(<StandardApp/>, document.getElementById("container"));
        expect(app).toExist();
    });

    it('creates a default app with the given store creator', () => {
        let dispatched = 0;
        const store = () => ({
            dispatch() {
                dispatched++;
            }
        });


        const app = ReactDOM.render(<StandardApp appStore={store}/>, document.getElementById("container"));
        expect(app).toExist();

        expect(dispatched > 0).toBe(true);
    });

    it('creates a default app and runs the initial actions', (done) => {
        const myaction = (param) => {
            return param;
        };
        const store = () => ({
            dispatch(value) {
                if (value === 10) {
                    done();
                }
            }
        });


        const app = ReactDOM.render(<StandardApp appStore={store} initialActions={[myaction.bind(null, 10)]}/>, document.getElementById("container"));
        expect(app).toExist();
    });

    it('creates a default app and renders the given component', () => {
        const store = () => ({
            dispatch: () => {},
            subscribe: () => {},
            getState: () => ({})
        });


        const app = ReactDOM.render(<StandardApp appStore={store} appComponent={mycomponent}/>, document.getElementById("container"));
        expect(app).toExist();

        const dom = ReactDOM.findDOMNode(app);

        expect(dom.className).toBe('mycomponent');
    });

    it('creates a default app and configures plugins', () => {
        const pluginsDef = {
            plugins: {
                MyPlugin: {
                    MyPlugin: {},
                    reducers: {}
                }
            },
            requires: {}
        };

        const store = () => ({
            dispatch: () => {},
            subscribe: () => {},
            getState: () => ({})
        });

        const app = ReactDOM.render(<StandardApp appStore={store} appComponent={mycomponent} pluginsDef={pluginsDef}/>, document.getElementById("container"));
        expect(app).toExist();

        const dom = ReactDOM.findDOMNode(app);

        expect(dom.getElementsByClassName('MyPlugin').length).toBe(1);
    });
});
