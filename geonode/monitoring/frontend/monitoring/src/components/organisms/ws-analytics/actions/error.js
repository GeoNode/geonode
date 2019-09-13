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
import { fetch, sequenceInterval } from '../../../../utils';
import apiUrl from '../../../../backend';
import { WS_ERROR_SEQUENCE } from '../constants';


const reset = createAction(
  WS_ERROR_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  WS_ERROR_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  WS_ERROR_SEQUENCE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  WS_ERROR_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (service, argInterval) =>
  (dispatch) => {
    dispatch(begin());
    const interval = sequenceInterval(argInterval);
    let url = `${apiUrl}/metric_data/response.error.count/?event_type=${service}`;
    url += `&last=${argInterval}&interval=${interval}`;
    fetch({ url })
      .then(response => {
        dispatch(success(response));
        return response;
      })
      .catch(error => {
        dispatch(fail(error.message));
      });
  };

const actions = {
  reset,
  begin,
  success,
  fail,
  get,
};

export default actions;
