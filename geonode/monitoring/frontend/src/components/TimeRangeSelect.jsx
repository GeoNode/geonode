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
import Button from '@material-ui/core/Button';
import { ranges } from '../utils/TimeRangeUtils';
import Paper from '@material-ui/core/Paper';
import ArrowLeftIcon from '@material-ui/icons/ArrowLeft';
import ArrowRightIcon from '@material-ui/icons/ArrowRight';
import { FormattedMessage } from 'react-intl';

export default function TimeRangeSelect({
    timeRange = 'year',
    onChange = () => {},
    readOnly,
    label,
    nextDate,
    previousDate,
    children
}) {
    return (
        <Fragment>
            {!readOnly && Object.keys(ranges).map((key) =>
            <Button
                key={key}
                size="small"
                variant={key === timeRange ? 'contained' : undefined}
                color={key === timeRange ? 'primary' : undefined}
                onClick={key === timeRange ? undefined : () => onChange(key)}>
                <FormattedMessage id={ranges[key].label} defaultMessage={ranges[key].label}/>
            </Button>)}
            <Paper style={{display: 'flex', flexDirection: 'row', marginTop: 8 }}>
                {!readOnly &&
                <Button
                    disabled={!previousDate}
                    onClick={() => onChange(timeRange, previousDate)}>
                    <ArrowLeftIcon />
                </Button>}
                <Typography
                    variant="h6"
                    component="p"
                    align="center"
                    gutterBottom
                    style={{ flex: 1, margin: '16px 0' }}>
                    {label}
                </Typography>
                {!readOnly &&
                <Button
                    disabled={!nextDate}
                    onClick={() => onChange(timeRange, nextDate)}>
                    <ArrowRightIcon />
                </Button>}
            </Paper>
            {children}
        </Fragment>
    );
}
