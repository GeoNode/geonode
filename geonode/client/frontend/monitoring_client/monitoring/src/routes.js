/*
#########################################################################
#
# Copyright (C) 2019 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
*/

import React from 'react';

// Pages

import Alerts from './pages/alerts';
import AlertConfig from './pages/alert-config';
import AlertsSettings from './pages/alerts-settings';
import ErrorDetails from './pages/error-details';
import Errors from './pages/errors';
import HWPerf from './pages/hardware-performance';
import Home from './pages/home';
import SWPerf from './pages/software-performance';

import Main from './containers/main';
import app from './containers/app';
import ErrorIcon from '@material-ui/icons/Error';
import NotificationsIcon from '@material-ui/icons/Notifications';
import MemoryIcon from '@material-ui/icons/Memory';
import DeveloperBoardIcon from '@material-ui/icons/DeveloperBoard';
import ShowChartIcon from '@material-ui/icons/ShowChart';

const App = app.component;

function wrapComponent(Component) {
    return function wrap(props) {
        return (<Main><App><Component {...props} /></App></Main>);
    };
}

export const pages = [
    {
        group: 'monitoring',
        exact: true,
        label: 'overview',
        Icon: ShowChartIcon,
        paths: ["/"],
        component: wrapComponent(Home)
    },
    {
        group: 'monitoring',
        exact: true,
        label: 'errors',
        Icon: ErrorIcon,
        paths: ["/errors"],
        component: wrapComponent(Errors)
    },
    {
        group: 'monitoring',
        exact: true,
        paths: ["/errors/:errorId"],
        component: wrapComponent(ErrorDetails)
    },
    {
        group: 'monitoring',
        exact: true,
        label: 'alerts',
        Icon: NotificationsIcon,
        paths: ["/alerts"],
        component: wrapComponent(Alerts)
    },
    {
        group: 'monitoring',
        exact: true,
        label: 'alerts-settings',
        paths: ["/alerts-settings"],
        component: wrapComponent(AlertsSettings)
    },
    {
        group: 'monitoring',
        exact: true,
        paths: ["/alerts/:alertId"],
        component: wrapComponent(AlertConfig)
    },
    {
        group: 'monitoring',
        exact: true,
        label: 'software-perf',
        Icon: DeveloperBoardIcon,
        paths: ["/performance/software"],
        component: wrapComponent(SWPerf)
    },
    {
        group: 'monitoring',
        exact: true,
        label: 'hardware-perf',
        Icon: MemoryIcon,
        paths: ["/performance/hardware"],
        component: wrapComponent(HWPerf)
    }
];
