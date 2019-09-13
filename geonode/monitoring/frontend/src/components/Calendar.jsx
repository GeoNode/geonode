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

import React, { useState } from 'react';
import Paper from '@material-ui/core/Paper';
import useStyles from '../hooks/useStyles';
import Typography from '@material-ui/core/Typography';
import CircularProgress from '@material-ui/core/CircularProgress';
import useRequest from '../hooks/useRequest';
import ReactTooltip from 'react-tooltip';
import CalendarHeatmap from 'react-calendar-heatmap';
import ResponseError from './ResponseError';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import { FormattedMessage } from 'react-intl';
import LinkIcon from '@material-ui/icons/Link';
import CloseIcon from '@material-ui/icons/Close';
import Link from '@material-ui/core/Link';

export default function Calendar({ globalTimeRange, label = '', tooltip = () => 'tooltip', eventType, resourceType = 'layers', timeRange, request, date }) {
    const [selected, setSelected] = useState(null);
    const [response, loading, error] = useRequest(request, { resourceType, eventType, timeRange: globalTimeRange ? undefined : timeRange }, [ resourceType, eventType, timeRange, date ]);
    const { items = [], maxCount, startDate, endDate } = response || {};
    const classes = useStyles();
    return (
        <Paper className={classes.paper}>
            <Typography
                component="h2"
                variant="h6"
                color="primary"
                gutterBottom
                align="center">
                {label}
            </Typography>
            {loading
            ? <CircularProgress className={classes.progress} />
            : error
                ? <ResponseError {...error} label={label}/>
                : <div className="calendar-heatmap-container">
                    <CalendarHeatmap
                        values={items}
                        startDate={startDate}
                        endDate={endDate}
                        onClick={(properties) => setSelected(properties)}
                        tooltipDataAttrs={(properties = {}) =>
                            ({ 'data-tip': tooltip({count: properties.count || 0}) })}
                        classForValue={(properties) => {
                            if (!properties) return 'color-empty';
                            const colorClassName = `color-scale-${maxCount < 7 ? properties.count : Math.floor(properties.count / maxCount * 6) + 1}`;
                            return `${colorClassName}${selected && properties.date ===  selected.date ? ' selected-day' : ''}`;
                        }}/>
                    <ReactTooltip/>
                </div>}
            {selected &&
            <div className="scroll-table flex-cell">
                <Typography
                    component="h4"
                    variant="body1"
                    gutterBottom
                    align="center">
                    {selected.formatDate}
                </Typography>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell><FormattedMessage id="name" defaultMessage="Name"/></TableCell>
                            <TableCell align="right"><FormattedMessage id="link" defaultMessage="Link"/></TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {(selected.items || []).map(({ id, title, name, href }) => (
                            <TableRow
                                key={name}>
                                <TableCell component="th" scope="row">
                                    {title || name || `Identifier: ${id}`}
                                </TableCell>
                                <TableCell align="right">
                                {href
                                ? <Link
                                    href={href}
                                    color="textPrimary"
                                    target="_blank"
                                    onClick={event => event.stopPropagation()}>
                                    <LinkIcon/>
                                </Link>
                                : <CloseIcon color="error"/>}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>}
        </Paper>
    );
}
