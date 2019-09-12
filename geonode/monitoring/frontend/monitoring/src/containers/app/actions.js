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
import { fetch } from '../../utils';
import apiUrl from '../../backend';
import SERVICES from './constants';


const reset = createAction(
  SERVICES,
  () => ({ status: 'initial' })
);


export const begin = createAction(
  SERVICES,
  () => ({ status: 'pending' })
);


const success = createAction(
  SERVICES,
  response => ({
    ...response,
    status: 'success',
  })
);


const fail = createAction(
  SERVICES,
  error => ({
    status: 'error',
    error,
  })
);


const get = () =>
  (dispatch) => {
    dispatch(begin());
    const url = `${apiUrl}/services`;
    fetch({ url })
      .then(response => {
        const result = {};
        response.services.forEach((service) => {
          if (!result[service.type]) {
            result[service.type] = [];
          }
          result[service.type].push(service);
        });
        dispatch(success(result));
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
