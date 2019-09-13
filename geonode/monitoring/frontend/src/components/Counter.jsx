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
import Typography from '@material-ui/core/Typography';
import CircularProgress from '@material-ui/core/CircularProgress';
import Paper from '@material-ui/core/Paper';
import useStyles from '../hooks/useStyles';
import useRequest from '../hooks/useRequest';
import ResponseError from './ResponseError';
import numeral from 'numeral';
import Tooltip from '@material-ui/core/Tooltip';

const CounterTitle = function({ label, children }) {
    const classes = useStyles();
    return (
        <Paper className={classes.paperCounter}>
            <Typography 
                variant="h6"
                component="h2"
                color="primary"
                align="center">
                {label}
            </Typography>
            {children}
        </Paper>
    );
};

const CounterValue = function({ label, count = 0, error, loading, variant = 'h4', icon, counterLabel }) {
    const classes = useStyles();
    const Icon = icon;
    return loading
        ? <CircularProgress className={classes.progress} />
        : <Fragment>
            {error
            ? <ResponseError {...error} label={<span>{label} {counterLabel}</span>}/>
            : count < 999
                ? <Tooltip
                    title={<span>{counterLabel} {count || 0}</span>}>
                    <Typography
                        variant={variant}
                        align="center">
                        {Icon && <Icon />} {numeral(count || 0).format('Oa')}
                    </Typography>
                </Tooltip>
                : <Tooltip
                    title={<span>{counterLabel} {count || 0}</span>}>
                    <Typography
                        variant={variant}
                        align="center">
                        {Icon && <Icon />} {numeral(count || 0).format('Oa')}
                    </Typography>
                </Tooltip>}
        </Fragment>;
};

export const Counter = function({ label, counterLabel, count, error, loading, variant, icon,  }) {
    return (
        <CounterTitle label={label}>
            <CounterValue
                label={counterLabel}
                count={count}
                error={error}
                loading={loading}
                variant={variant}
                icon={icon} />
        </CounterTitle>
    );
};

const RequestCount  = function({ label, icon, request, globalTimeRange, resourceType, date, timeRange, counterLabel, resourceId, eventType }) {
    const [response, loading, error] = useRequest(request,
        { timeRange: globalTimeRange ? undefined : timeRange, resourceType, resource: resourceId, eventType },
        [ timeRange, resourceType, date, resourceId, eventType ]);
    const { count } = response || {};
    return (
        <CounterValue
            label={label}
            count={count}
            error={error}
            loading={loading}
            icon={icon}
            counterLabel={counterLabel}/>);
};

export const RequestCounter = function({
    label = '',
    requests = {},
    timeRange,
    resourceType,
    date,
    resourceId,
    eventType,
    globalTimeRange
}) {
    return (
        <CounterTitle
            label={label}>
            {Object.keys(requests).map((key, idx) => {
                const { request, label: counterLabel, Icon } = requests[key] || {};
                return (
                    <RequestCount
                        key={idx}
                        globalTimeRange={globalTimeRange}
                        label={label}
                        icon={Icon}
                        request={request}
                        resourceType={resourceType}
                        date={date}
                        timeRange={timeRange}
                        counterLabel={counterLabel}
                        resourceId={resourceId}
                        eventType={eventType}/>
                );
            })}
        </CounterTitle>
    );
};

export default Counter;
