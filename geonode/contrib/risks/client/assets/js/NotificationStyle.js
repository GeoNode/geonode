/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const colors = {
  info: '#2c689c',
  success: '#2c9c51',
  warning: '#9c952c',
  error: '#9c2c2c'
};

module.exports = {
    NotificationItem: {
        DefaultStyle: {
            backgroundColor: '#fff',
            borderTop: '2px solid #2c689c',
            borderBottom: '2px solid #2c689c',
            WebkitBoxShadow: '0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23)',
            MozBoxShadow: '0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23)',
            boxShadow: '0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23)'
        },
        info: {
            borderColor: colors.info
        },
        success: {
            borderColor: colors.success
        },
        warning: {
            borderColor: colors.warning
        },
        error: {
            borderColor: colors.error
        }
    },
    Dismiss: {
        DefaultStyle: {
            fontFamily: 'Arial',
            fontSize: '17px',
            position: 'absolute',
            top: '4px',
            right: '5px',
            lineHeight: '15px',
            backgroundColor: '#ffffff',
            color: '#2c689c',
            borderRadius: '0',
            width: '14px',
            height: '14px',
            fontWeight: 'bold',
            textAlign: 'center'
        },
        info: {
            color: colors.info
        },
        success: {
            color: colors.success
        },
        warning: {
            color: colors.warning
        },
        error: {
            color: colors.error
        }
    }
};
