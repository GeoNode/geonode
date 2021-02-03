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

import React, { Fragment } from 'react';
import clsx from 'clsx';
import { Bar, BarChart, XAxis, YAxis, Label, ResponsiveContainer, Tooltip } from 'recharts';
import moment from 'moment';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import useStyles from '../hooks/useStyles';
import Typography from '@material-ui/core/Typography';
import PersonIcon from '@material-ui/icons/Person';
import PersonOutlinedIcon from '@material-ui/icons/PersonOutlined';
import VisibilityIcon from '@material-ui/icons/Visibility';
import CircularProgress from '@material-ui/core/CircularProgress';
import {
    getResourcesHitsInterval,
    getResourcesVisitorsInterval,
    getResourcesAnonymousInterval
} from '../api';
import useRequest from '../hooks/useRequest';
import ResponseError from './ResponseError';
import { FormattedMessage } from 'react-intl';
import numeral from 'numeral';

export const RequestChart = function ({ label, timeRange, globalTimeRange, resourceType, resourceId, date, eventType }) {
    const classes = useStyles();
    const fixedHeightPaper = clsx(classes.paper, classes.fixedHeight);
    const [response, loading, hitsError] = useRequest(getResourcesHitsInterval, { timeRange: globalTimeRange ? undefined : timeRange,  resourceType, resource: resourceId, eventType }, [ timeRange, resourceId, resourceType, date, eventType ]);
    const { items = [], count: hitsCount, format } = response || {};
    const [userResponse, userLoading, userError] = useRequest(getResourcesVisitorsInterval, { timeRange: globalTimeRange ? undefined : timeRange,  resourceType, resource: resourceId, eventType }, [ timeRange, resourceId, resourceType, date, eventType ]);
    const { items: visitors, count: visitorsCount } = userResponse;

    const [anonymousResponse, anonymousLoading, anonymousError] = useRequest(getResourcesAnonymousInterval, { timeRange: globalTimeRange ? undefined : timeRange,  resourceType, resource: resourceId, eventType }, [ timeRange, resourceId, resourceType, date, eventType ]);
    const { items: anonymous, count: anonymousCount } = anonymousResponse;

    
    return (
        <Fragment>
            <Paper className={fixedHeightPaper}>
                <Typography
                    variant="h6"
                    color="primary"
                    gutterBottom>
                    {label}
            </Typography>
                {loading || userLoading || anonymousLoading
                    ? <CircularProgress className={classes.progress} />
                    : !(userError && hitsError) && <ResponsiveContainer
                        width="99%"
                        height="100%">
                        <BarChart
                            data={items.map((item, idx) => ({
                                ...item,
                                'Hits': item.val || 0,
                                'Unique Visitors': visitors && visitors[idx] && visitors[idx].val || 0,
                                'Anonymous Sessions': anonymous && anonymous[idx] && anonymous[idx].val || 0,
                            }))}
                            margin={{
                                top: 16,
                                right: 16,
                                bottom: 35,
                                left: 24
                            }}>
                            <XAxis
                                dataKey="from"
                                tickFormatter={(value) => moment.utc(value).format(format)}
                                interval={0}
                                angle={-45}
                                tickMargin={20}
                                textAnchor="end"
                                fontSize="11">
                                <Label position="end"  style={{ textAnchor: 'middle', fontSize: 10 }}>
                                    Time UTC
                                </Label>
                            </XAxis>
                            <YAxis
                                fontSize="11"
                                allowDecimals={false}
                                tickFormatter={(value) => numeral(value).format('Oa')}>
                                <Label position="left" style={{ textAnchor: 'middle', fontSize: 10 }} >
                                    Count
                                </Label>
                            </YAxis>
                            <Tooltip
                                labelFormatter={(value) => `Date ${moment.utc(value).format(format)}`} />
                            <Bar type="monotone" dataKey="Hits" fill="#2c689c" />
                            <Bar type="monotone" dataKey="Unique Visitors" fill="#ff8f31" />
                            <Bar type="monotone" dataKey="Anonymous Sessions" fill="#333333" />
                        </BarChart>
                    </ResponsiveContainer>}
            </Paper>
            <Paper>
                <Grid container spacing={2}>
                    <Grid item xs={12} md={4}>
                        {!hitsError
                            ? <Typography
                                component="h2"
                                variant="h6"
                                color="primary"
                                align="center"
                                gutterBottom>
                                <VisibilityIcon style={{ verticalAlign: 'middle' }} /> <FormattedMessage id="hits" defaultMessage="Hits"/> {hitsCount}
                            </Typography>
                            : <ResponseError
                                {...hitsError}
                                label={<FormattedMessage id="hits" defaultMessage="Hits"/>}
                                typography={{
                                    component: 'h2',
                                    variant: 'h6'
                                }} />}
                    </Grid>
                    <Grid item xs={12} md={4}>
                        {!userError
                            ? <Typography
                                component="h2"
                                variant="h6"
                                color="primary"
                                align="center"
                                gutterBottom>
                                <PersonIcon style={{ verticalAlign: 'middle' }} /> <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/> {visitorsCount}

                            </Typography>
                            : <ResponseError
                                {...userError}
                                label={<FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>}
                                typography={{
                                    component: 'h2',
                                    variant: 'h6'
                                }} />}
                    </Grid>
                    <Grid item xs={12} md={4}>
                        {!userError
                            ? <Typography
                                component="h2"
                                variant="h6"
                                color="primary"
                                align="center"
                                gutterBottom>
                                <PersonOutlinedIcon style={{ verticalAlign: 'middle' }} /> <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/> {anonymousCount}

                            </Typography>
                            : <ResponseError
                                {...anonymousError}
                                label={<FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>}
                                typography={{
                                    component: 'h2',
                                    variant: 'h6'
                                }} />}
                    </Grid>
                </Grid>
            </Paper>
        </Fragment>
    )
};