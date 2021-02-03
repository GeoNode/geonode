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

import AnalyticsOverview from './pages/AnalyticsOverview';
import AnalyticsDetails from './pages/AnalyticsDetails';
import BarChartIcon from '@material-ui/icons/BarChart';
import InfoOutlinedIcon from '@material-ui/icons/InfoOutlined';

import { pages as monitoringPages } from '../monitoring/src/routes';

export const pages = [
    ...monitoringPages,
    {
        group: 'analytics',
        exact: true,
        label: 'overview',
        paths: ['/analytics'],
        Icon: BarChartIcon,
        component: AnalyticsOverview
    },
    {
        group: 'analytics',
        exact: true,
        label: 'details',
        paths: [
            '/analytics/details',
            '/analytics/details/:resourceType',
            '/analytics/details/:resourceType/:resourceId',
            '/analytics/details/:resourceType/time-range/:timeRange',
            '/analytics/details/:resourceType/time-range/:timeRange/:resourceId',
            '/analytics/details/:resourceType/time-range/:timeRange/date/:date',
            '/analytics/details/:resourceType/time-range/:timeRange/date/:date/:resourceId',
            '/analytics/details/:resourceType/time-range/:timeRange/event/:eventType',
            '/analytics/details/:resourceType/time-range/:timeRange/event/:eventType/:resourceId',
            '/analytics/details/:resourceType/time-range/:timeRange/date/:date/event/:eventType',
            '/analytics/details/:resourceType/time-range/:timeRange/date/:date/event/:eventType/:resourceId'
        ],
        Icon: InfoOutlinedIcon,
        component: AnalyticsDetails
    }
];

const routes = pages
    .reduce(function(acc, { paths, ...page }) {
        return [
            ...acc,
            ...paths.map(path => ({ ...page, path }))
        ];
    }, []);

export default routes;