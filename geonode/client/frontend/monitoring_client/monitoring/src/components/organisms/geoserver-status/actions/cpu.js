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
import { GEOSERVER_CPU_SEQUENCE } from '../constants';


const reset = createAction(
  GEOSERVER_CPU_SEQUENCE,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  GEOSERVER_CPU_SEQUENCE,
  () => ({ status: 'pending' })
);


const success = createAction(
  GEOSERVER_CPU_SEQUENCE,
  response => ({
    response,
    status: 'success',
  })
);


const fail = createAction(
  GEOSERVER_CPU_SEQUENCE,
  error => ({
    status: 'error',
    error,
  })
);


const get = (host, argInterval) =>
  (dispatch) => {
    dispatch(begin());
    const interval = sequenceInterval(argInterval);
    let url = `${apiUrl}/metric_data/cpu.usage.percent/?last=${argInterval}&interval=${interval}`;
    url += `&service=${host}`;
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
