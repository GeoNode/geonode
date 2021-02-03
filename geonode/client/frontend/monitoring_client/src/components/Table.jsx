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

import React, { useState, useEffect, Fragment } from 'react';
import Paper from '@material-ui/core/Paper';
import useStyles from '../hooks/useStyles';
import TableMUI from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Typography from '@material-ui/core/Typography';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import CircularProgress from '@material-ui/core/CircularProgress';
import useRequest from '../hooks/useRequest';
import ResponseError from './ResponseError';
import Button from '@material-ui/core/Button';
import Tooltip from '@material-ui/core/Tooltip';
import TextField from '@material-ui/core/TextField';
import InputAdornment from '@material-ui/core/InputAdornment';
import CloseIcon from '@material-ui/icons/Close';
import IconButton from '@material-ui/core/IconButton';
import LinkIcon from '@material-ui/icons/Link';
import Link from '@material-ui/core/Link';
import { FormattedMessage } from 'react-intl';
import isFunction from 'lodash/isFunction';

const Row = function({ id, type, title, name, href, label, count, flagIconClassName, showType, onSelect, selectedId, showLink }) {
    const classes = useStyles();
    return (
        <TableRow
            key={name}
            hover={!!onSelect}
            selected={selectedId !== undefined && id === selectedId}
            onClick={() => onSelect && onSelect({id, type, name})}
            classes={{
                selected: classes.selectedRow
            }}>
            <TableCell component="th" scope="row">
                {showLink && (
                    href
                    ? <Link
                        href={href}
                        color="textPrimary"
                        target="_blank"
                        onClick={event => event.stopPropagation()}>
                        <LinkIcon/>
                    </Link>
                    : <CloseIcon color="error"/>
                )}
                {flagIconClassName && <span className={flagIconClassName} style={{ marginRight: 8 }}/>}
                {showType && type ? <span style={{fontStyle: 'italic'}}>{`${type} - `}</span> : ''}
                {label || title || name || `Identifier: ${id}`}
            </TableCell>
            <TableCell align="right">{count}</TableCell>
        </TableRow>
    );
};

const Table = function({ showLink, title = '', top, header, loading, items, showType, onSelect, footer, error, columnLabel, selectedId, onUpdateSelected, itemsFormatter }) {
    const classes = useStyles();
    const [formattedItems, setFormatedItems] = useState(items);

    useEffect(function() {
        setFormatedItems(items && itemsFormatter ? itemsFormatter(items) : items);
    }, [ items.length ]);

    const selectedItem= (formattedItems || []).find(item => selectedId && item.id === selectedId);

    useEffect(function() {
        if (onUpdateSelected) onUpdateSelected(selectedItem);
    }, [ selectedId, formattedItems.length ]);

    return (
        <Paper className={classes.paper}>
            {top}
            <Typography
                component="h2"
                variant="h6"
                color={error ? 'error' : 'primary'}
                gutterBottom
                align="center"
                style={{ marginTop: 16 }}>
                {title}
            </Typography>
            {header}
            {loading
            ? <CircularProgress className={classes.progress} />
            : error
                ? <ResponseError {...error}/>
                : <div className="scroll-table">
                    <TableMUI size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell><FormattedMessage id="name" defaultMessage="Name"/></TableCell>
                            <TableCell align="right">{columnLabel || <FormattedMessage id="count" defaultMessage="Count"/>}</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {selectedItem && <Row
                            {...selectedItem}
                            showLink={showLink}
                            showType={showType}
                            onSelect={onSelect}
                            selectedId={selectedId}/>}
                        {formattedItems
                            .filter(({ id }) => !selectedId || id !== selectedId)
                            .map(({ id, type, title: rowTitle, name, href, label, count, flagIconClassName }) => (
                            <Row
                                key={name}
                                title={rowTitle}
                                id={id}
                                type={type}
                                name={name}
                                href={href}
                                label={label}
                                count={count}
                                flagIconClassName={flagIconClassName}

                                showLink={showLink}
                                showType={showType}
                                onSelect={onSelect}
                                selectedId={selectedId}/>
                        ))}
                    </TableBody>
                </TableMUI>
                </div>}
            {footer}
        </Paper>
    );
};

export default Table;

export const RequestTable = function({ showLink, selectedId, onUpdateSelected, label, showType, header, maxCount = 10, timeRange, globalTimeRange, requests = {}, onSelect, resourceType, resourceId, date, eventType, itemsFormatter  }) {
    const [textFilter, onFilter] = useState('');
    const keys = Object.keys(requests);
    const [view, setView] = useState(keys[0]);
    const { request, label: columnLabel } = requests[view];
    const [response, loading, error] = useRequest(request, { timeRange: globalTimeRange ? undefined : timeRange, resourceType, resource: resourceId, eventType }, [ timeRange, resourceType, view, resourceId, date, eventType ]);
    const { items = [] } = response || {};
    const [showAll, onShowAll] = useState();

    const itemsTextFilter = items.filter(({ name }) => !textFilter || name && name.toLowerCase().indexOf(textFilter.toLowerCase()) !== -1);
    const filteredItems = showAll ? itemsTextFilter : itemsTextFilter.filter((item, idx) => idx < maxCount);
    const itemsCount = filteredItems.length < maxCount ? filteredItems.length : maxCount;

    const Header = header;

    return (
        <Table
            showLink={showLink}
            showType={showType}
            onUpdateSelected={onUpdateSelected}
            selectedId={selectedId}
            itemsFormatter={itemsFormatter}
            top={
                keys.length > 1 && <Tabs
                    value={view}
                    onChange={(event, value) => setView(value)}
                    indicatorColor="primary"
                    textColor="primary"
                    variant="fullWidth">
                    {keys.map((key) => {
                        const { Icon, label: columnLabel } = requests[key];
                        return (
                            <Tab
                                key={key}
                                value={key}
                                label={
                                    <Tooltip
                                        title={columnLabel}
                                        placement="top">
                                        {Icon ? <Icon style={{verticalAlign: 'middle'}}/> : columnLabel}
                                    </Tooltip>
                                }/>
                        );
                    })}
                </Tabs>
            }
            title={isFunction(label)
                ? showAll || itemsCount <= 1 || textFilter ? label() : label(itemsCount)
                : label}
            loading={loading}
            columnLabel={columnLabel}
            header={ !(error || loading) &&
                <Fragment>
                    {Header && <Header items={items}/>}
                    <TextField
                        id="filter"
                        label={<FormattedMessage id="filterRecords" defaultMessage="Filter records..."/>}
                        margin="normal"
                        value={textFilter}
                        onChange={(event) => onFilter(event.target.value)}
                        style={{marginTop: 0}}
                        InputProps={{
                            endAdornment:
                            textFilter && <InputAdornment
                                position="end"
                                onClick={() => onFilter('')}>
                                <IconButton size="small"><CloseIcon /></IconButton>
                            </InputAdornment>
                        }}/>
                </Fragment>}
            error={error}
            items={filteredItems}
            footer={
                <Fragment>
                    {itemsTextFilter.length > maxCount &&
                    <Button
                        onClick={() => onShowAll(!showAll)}>
                        {showAll
                            ? <FormattedMessage id="hide" defaultMessage="Hide"/>
                            : <FormattedMessage id="showAll" defaultMessage="Show All"/>}
                    </Button>}
                    {!(loading || error) &&
                    <Typography
                        align="right"
                        component="div"
                        variant="caption">
                        {showAll ? filteredItems.length : itemsCount} of {itemsTextFilter.length}
                    </Typography>}
                </Fragment>
                
            }
            onSelect={onSelect}/>
    );
};

