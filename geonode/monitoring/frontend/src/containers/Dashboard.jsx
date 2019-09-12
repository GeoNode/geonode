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

import React, { useState, Fragment } from 'react';
import clsx from 'clsx';
import { matchPath } from "react-router-dom";

import CssBaseline from '@material-ui/core/CssBaseline';
import Drawer from '@material-ui/core/Drawer';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import List from '@material-ui/core/List';
import Typography from '@material-ui/core/Typography';
import Divider from '@material-ui/core/Divider';
import IconButton from '@material-ui/core/IconButton';
import MenuIcon from '@material-ui/icons/Menu';
import ChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import ListSubheader from '@material-ui/core/ListSubheader';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import LinearProgress from '@material-ui/core/LinearProgress';
import { FormattedMessage } from 'react-intl';
import useStyles from '../hooks/useStyles';
import { pages } from '../routes';

const groups = pages.reduce(function(acc, { group, ...page }) {
    if (acc[group]) {
        return  {
            ...acc,
            [group]: [ ...acc[group], page ]
        };
    }
    return {
        ...acc,
        [group]: [ page ]
    };
}, {});

export default function Dashboard({ children, history, location, loading }) {

    const classes = useStyles();
    const [open, setOpen] = useState(true);
    const pathname = location && location.pathname || '';
    const checkPath = paths => paths.find(path => matchPath(pathname, { path, exact: true, strict: false }));
    const { label: selectedLabel } = pages.find(({ paths }) => checkPath(paths)) || {};

    return (
        <div className={classes.root}>
            <CssBaseline />
            <AppBar position="absolute" className={clsx(classes.appBar, open && classes.appBarShift)}>
                <Toolbar className={classes.toolbar}>
                    <IconButton
                        edge="start"
                        color="inherit"
                        aria-label="open drawer"
                        onClick={() => setOpen(true)}
                        className={clsx(classes.menuButton, open && classes.menuButtonHidden)}>
                        <MenuIcon />
                    </IconButton>
                    <Typography component="h1" variant="h6" color="inherit" noWrap className={classes.title}>
                        {!loading && selectedLabel && <FormattedMessage id={selectedLabel} defaultMessage={selectedLabel}/>}
                    </Typography>
                </Toolbar>
            </AppBar>
            <Drawer
                variant="permanent"
                color="primary"
                open={open}
                classes={{ paper: clsx(classes.drawerPaper, !open && classes.drawerPaperClose) }}>
                <div className={classes.toolbarIcon}>
                    <IconButton onClick={() => setOpen(false)}>
                        <ChevronLeftIcon />
                    </IconButton>
                </div>
                <Divider />
                {!loading && Object.keys(groups).map(groupName => {
                    const groupPages = groups[groupName] || [];
                    return (
                        <Fragment key={groupName}>
                            <List
                                subheader={
                                    <ListSubheader>
                                        {open ? <FormattedMessage id={groupName} defaultMessage={groupName}/> : ''}
                                    </ListSubheader>
                                }>
                                {groupPages.filter(({ Icon }) => Icon).map(tab => {
                                    const { label, paths, Icon } = tab || {};
                                    return (
                                        <ListItem
                                            key={paths[0]}
                                            selected={!!checkPath(paths)}
                                            button
                                            onClick={() => history.push(paths[0])}>
                                            <ListItemIcon>
                                                <Icon />
                                            </ListItemIcon>
                                            <ListItemText
                                                primary={<FormattedMessage id={label} defaultMessage={label}/>}/>
                                        </ListItem>
                                    );
                                })}
                            </List>
                            <Divider />
                        </Fragment>
                    );
                })}
            </Drawer>
            <div className={classes.content} style={{flex: 1}}>
                <div className={classes.appBarSpacer} />
                <div className={classes.contentBodyWrapper}>
                    <div
                        className={classes.contentBody}
                        style={{ position: 'absolute', width: '100%', height: '100%', overflow: 'auto' }}>
                        {loading ? <LinearProgress/> : children}
                    </div>
                </div>
            </div>
        </div>
    );
}