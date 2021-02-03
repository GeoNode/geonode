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

import { createAction } from 'redux-actions';
import { fetch } from '../../../utils';
import apiUrl from '../../../backend';
import { ALERT_CONFIG_SET } from '../constants';


const reset = createAction(
  ALERT_CONFIG_SET,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  ALERT_CONFIG_SET,
  () => ({ status: 'pending' })
);


const success = createAction(
  ALERT_CONFIG_SET,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  ALERT_CONFIG_SET,
  error => ({
    status: 'error',
    error,
  })
);


const set = (id, data) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/notifications/config/${id}/`;
    fetch({ url, body: data, method: 'POST' })
      .then(response => {
        dispatch(success(response));
        return response;
      })
      .catch(error => {
        dispatch(fail(error.message));
      });
  };


export default {
  reset,
  begin,
  success,
  fail,
  set,
};
