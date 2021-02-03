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
import useStyles from '../hooks/useStyles';
import Typography from '@material-ui/core/Typography';
import Button from '@material-ui/core/Button';
import ReportProblemIcon from '@material-ui/icons/ReportProblem';
import Divider from '@material-ui/core/Divider';
import Popover from '@material-ui/core/Popover';
import { FormattedMessage } from 'react-intl';

export default function ResponseError({ label = '', status, statusText, messages = [], typography = {} }) {
    const [anchorEl, setAnchorEl] = useState(null);
    const classes = useStyles();
    return (
        <Fragment>
            <Typography
                align="center"
                {...typography}>
                <Button
                    fullWidth
                    onClick={(event) => setAnchorEl(event.currentTarget)}
                    style={{ textTransform: 'none' }}>
                    <Typography
                        color="error">
                        <ReportProblemIcon style={{verticalAlign: 'middle'}}/>
                    </Typography>
                </Button>
            </Typography>
            <Popover
                id="response-popover"
                classes={{
                    paper: classes.popoverPaper
                }}
                open={!!anchorEl}
                anchorEl={anchorEl}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'center'
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'center'
                }}
                onClose={() => setAnchorEl(null)}
                disableRestoreFocus>
                <Typography color="error">{label} <FormattedMessage id="requestError" defaultMessage="Request Error"/></Typography>
                {Object.keys(messages || {}).map(key =>
                <Fragment key={key}>
                <Typography variant="caption" display="block"><strong>{key}</strong>:</Typography>
                {messages[key].map((text, idx) =>
                    <Typography variant="caption" key={idx} display="block">{text}</Typography>
                )}
                </Fragment>)}
                <Divider />
                <Typography variant="caption">{statusText} {status}</Typography>
            </Popover>
        </Fragment>
    )
}
