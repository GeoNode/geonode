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

/* Component from https://material-ui.com/components/autocomplete/#react-select */

import React from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';
import Select from 'react-select';
import { emphasize, makeStyles, useTheme } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import NoSsr from '@material-ui/core/NoSsr';
import TextField from '@material-ui/core/TextField';
import Paper from '@material-ui/core/Paper';
import Chip from '@material-ui/core/Chip';
import MenuItem from '@material-ui/core/MenuItem';
import CancelIcon from '@material-ui/icons/Cancel';

const useStyles = makeStyles(theme => ({
    root: {
        flexGrow: 1,
        height: 250,
        minWidth: 290,
    },
    input: {
        display: 'flex',
        padding: 0,
        height: 'auto',
    },
    valueContainer: {
        display: 'flex',
        flexWrap: 'wrap',
        flex: 1,
        alignItems: 'center',
        overflow: 'hidden',
    },
    chip: {
        margin: theme.spacing(0.5, 0.25),
    },
    chipFocused: {
        backgroundColor: emphasize(
            theme.palette.type === 'light' ? theme.palette.grey[300] : theme.palette.grey[700],
            0.08,
        ),
    },
    noOptionsMessage: {
        padding: theme.spacing(1, 2),
    },
    singleValue: {
        fontSize: 16,
    },
    placeholder: {
        position: 'absolute',
        left: 2,
        bottom: 6,
        fontSize: 16,
    },
    paper: {
        position: 'absolute',
        zIndex: 1,
        marginTop: theme.spacing(1),
        left: 0,
        right: 0
    },
    divider: {
        height: theme.spacing(2),
    },
    autocomplete: {
        // marginBottom: theme.spacing(2),
    }
}));

function NoOptionsMessage(props) {
    return (
        <Typography
            color="textSecondary"
            className={props.selectProps.classes.noOptionsMessage}
            {...props.innerProps}
        >
            {props.children}
        </Typography>
    );
}

NoOptionsMessage.propTypes = {
    /**
     * The children to be rendered.
     */
    children: PropTypes.node,
    /**
     * Props to be passed on to the wrapper.
     */
    innerProps: PropTypes.object.isRequired,
    selectProps: PropTypes.object.isRequired,
};

function inputComponent({ inputRef, ...props }) {
    return <div ref={inputRef} {...props} />;
}

inputComponent.propTypes = {
    inputRef: PropTypes.oneOfType([
        PropTypes.func,
        PropTypes.shape({
            current: PropTypes.any.isRequired,
        }),
    ]),
};

function Control(props) {
    const {
        children,
        innerProps,
        innerRef,
        selectProps: { classes, TextFieldProps },
    } = props;

    return (
        <TextField
            fullWidth
            InputProps={{
                inputComponent,
                inputProps: {
                    className: classes.input,
                    ref: innerRef,
                    children,
                    ...innerProps,
                },
            }}
            {...TextFieldProps}
        />
    );
}

Control.propTypes = {
    /**
     * Children to render.
     */
    children: PropTypes.node,
    /**
     * The mouse down event and the innerRef to pass down to the controller element.
     */
    innerProps: PropTypes.shape({
        onMouseDown: PropTypes.func.isRequired,
    }).isRequired,
    innerRef: PropTypes.oneOfType([
        PropTypes.oneOf([null]),
        PropTypes.func,
        PropTypes.shape({
            current: PropTypes.any.isRequired,
        }),
    ]).isRequired,
    selectProps: PropTypes.object.isRequired,
};

function Option(props) {
    return (
        <MenuItem
            ref={props.innerRef}
            selected={props.isFocused}
            component="div"
            style={{
                fontWeight: props.isSelected ? 500 : 400,
            }}
            {...props.innerProps}
        >
            {props.children}
        </MenuItem>
    );
}

Option.propTypes = {
    /**
     * The children to be rendered.
     */
    children: PropTypes.node,
    /**
     * props passed to the wrapping element for the group.
     */
    innerProps: PropTypes.shape({
        id: PropTypes.string.isRequired,
        key: PropTypes.string.isRequired,
        onClick: PropTypes.func.isRequired,
        onMouseMove: PropTypes.func.isRequired,
        onMouseOver: PropTypes.func.isRequired,
        tabIndex: PropTypes.number.isRequired,
    }).isRequired,
    /**
     * Inner ref to DOM Node
     */
    innerRef: PropTypes.oneOfType([
        PropTypes.oneOf([null]),
        PropTypes.func,
        PropTypes.shape({
            current: PropTypes.any.isRequired,
        }),
    ]).isRequired,
    /**
     * Whether the option is focused.
     */
    isFocused: PropTypes.bool.isRequired,
    /**
     * Whether the option is selected.
     */
    isSelected: PropTypes.bool.isRequired,
};

function Placeholder(props) {
    const { selectProps, innerProps = {}, children } = props;
    return (
        <Typography color="textSecondary" className={selectProps.classes.placeholder} {...innerProps}>
            {children}
        </Typography>
    );
}

Placeholder.propTypes = {
    /**
     * The children to be rendered.
     */
    children: PropTypes.node,
    /**
     * props passed to the wrapping element for the group.
     */
    innerProps: PropTypes.object,
    selectProps: PropTypes.object.isRequired,
};

function SingleValue(props) {
    return (
        <Typography className={props.selectProps.classes.singleValue} {...props.innerProps}>
            {props.children}
        </Typography>
    );
}

SingleValue.propTypes = {
    /**
     * The children to be rendered.
     */
    children: PropTypes.node,
    /**
     * Props passed to the wrapping element for the group.
     */
    innerProps: PropTypes.any.isRequired,
    selectProps: PropTypes.object.isRequired,
};

function ValueContainer(props) {
    return <div className={props.selectProps.classes.valueContainer}>{props.children}</div>;
}

ValueContainer.propTypes = {
    /**
     * The children to be rendered.
     */
    children: PropTypes.node,
    selectProps: PropTypes.object.isRequired,
};

function MultiValue(props) {
    return (
        <Chip
            tabIndex={-1}
            label={props.children}
            className={clsx(props.selectProps.classes.chip, {
                [props.selectProps.classes.chipFocused]: props.isFocused,
            })}
            onDelete={props.removeProps.onClick}
            deleteIcon={<CancelIcon {...props.removeProps} />}
        />
    );
}

MultiValue.propTypes = {
    children: PropTypes.node,
    isFocused: PropTypes.bool.isRequired,
    removeProps: PropTypes.shape({
        onClick: PropTypes.func.isRequired,
        onMouseDown: PropTypes.func.isRequired,
        onTouchEnd: PropTypes.func.isRequired,
    }).isRequired,
    selectProps: PropTypes.object.isRequired,
};

function Menu(props) {
    return (
        <Paper square className={props.selectProps.classes.paper} {...props.innerProps}>
            {props.children}
        </Paper>
    );
}

Menu.propTypes = {
    /**
     * The children to be rendered.
     */
    children: PropTypes.element.isRequired,
    /**
     * Props to be passed to the menu wrapper.
     */
    innerProps: PropTypes.object.isRequired,
    selectProps: PropTypes.object.isRequired,
};

const components = {
    Control,
    Menu,
    MultiValue,
    NoOptionsMessage,
    Option,
    Placeholder,
    SingleValue,
    ValueContainer,
};

export default function Autocomplete({
    suggestions = [],
    value = '',
    label = '',
    placeholder = '',
    onChange = () => { }
}) {

    const classes = useStyles();
    const theme = useTheme();

    const selectStyles = {
        input: base => ({
            ...base,
            color: theme.palette.text.primary,
            '& input': {
                font: 'inherit',
            },
        }),
    };

    return (
        <div className={classes.autocomplete}>
            <NoSsr>
                <Select
                    classes={classes}
                    styles={selectStyles}
                    inputId="react-select-single"
                    TextFieldProps={{
                        label,
                        InputLabelProps: {
                            htmlFor: 'react-select-single',
                            shrink: true,
                        },
                    }}
                    placeholder={placeholder}
                    options={suggestions}
                    components={components}
                    value={value}
                    onChange={(value) => onChange(value)} />
            </NoSsr>
        </div>
    );
}