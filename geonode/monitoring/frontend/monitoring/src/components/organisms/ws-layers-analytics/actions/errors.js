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
import { fetch } from '../../../../utils';
import apiUrl from '../../../../backend';
import { WS_LAYER_ERROR } from '../constants';


const reset = createAction(
  WS_LAYER_ERROR,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  WS_LAYER_ERROR,
  () => ({ status: 'pending' })
);


const success = createAction(
  WS_LAYER_ERROR,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  WS_LAYER_ERROR,
  error => ({
    status: 'error',
    error,
  })
);


const get = (interval, layer, eventType) =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/metric_data/response.error.count/?last=${interval}&interval=${interval}`;
    fetch({ url: `${url}&resource=${layer}&event_type=${eventType}` })
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
  get,
};
