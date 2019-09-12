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

import { makeStyles } from '@material-ui/core/styles';

const drawerWidth = 240;

export default makeStyles(theme => ({
    selectedRow: {
        borderBottom: `2px solid ${theme.palette.primary.main}`
    },
    root: {
        display: 'flex',
        flex: 1,
        position: 'relative',
        height: '100%'
    },
    toolbar: {
        paddingRight: 24
    },
    toolbarIcon: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        padding: '0 8px',
        ...theme.mixins.toolbar
    },
    appBar: {
        zIndex: theme.zIndex.drawer + 1,
        transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen
        })
    },
    appBarShift: {
        marginLeft: drawerWidth,
        width: `calc(100% - ${drawerWidth}px)`,
        transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen
        })
    },
    menuButton: {
        marginRight: 36
    },
    menuButtonHidden: {
        display: 'none'
    },
    title: {
        flexGrow: 1
    },
    drawerPaper: {
        position: 'relative',
        whiteSpace: 'nowrap',
        width: drawerWidth,
        transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen
        })
    },
    drawerPaperClose: {
        overflowX: 'hidden',
        transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen
        }),
        width: theme.spacing(7),
        [theme.breakpoints.up('sm')]: {
            width: theme.spacing(9)
        }
    },
    appBarSpacer: {
        ...theme.mixins.toolbar,
        display: 'block',
        position: 'relative',
        width: '100%'
    },
    content: {
        flexGrow: 1,
        height: '100%',
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: theme.palette.background.default
    },
    contentBodyWrapper: {
        position: 'relative',
        width: '100%',
        height: '100%',
        flex: 1,
        overflow: 'hidden'
    },
    contentBody: {
        flex: 1,
        overflow: 'auto',
        maxWidth: 'initial',
        position: 'absolute',
        width: '100%',
        height: '100%',
        overflow: 'auto'
    },
    container: {
        paddingTop: theme.spacing(4),
        paddingBottom: theme.spacing(4)
    },
    paper: {
        padding: theme.spacing(2),
        display: 'flex',
        overflow: 'auto',
        flexDirection: 'column',
        minHeight: 180
    },
    paperCounter: {
        padding: theme.spacing(2),
        display: 'flex',
        overflow: 'auto',
        flexDirection: 'column'
    },
    popoverPaper: {
        padding: theme.spacing(1)
    },
    fixedHeight: {
        height: 240
    },
    progress: {
        margin: 'auto'
    },
    timeRangeHeader: {
        paddingTop: theme.spacing(2),
        paddingBottom: theme.spacing(1)
    },
    stickyHeader: {
        position: 'sticky',
        top: 0,
        zIndex: theme.zIndex.mobileStepper,
        backgroundColor: theme.palette.background.default,
        paddingBottom: 0
    },
    chip: {
        margin: theme.spacing(1),
    }
}));