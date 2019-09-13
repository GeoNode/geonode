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

import { WS_RESPONSE_SEQUENCE } from './constants';
import { WS_THROUGHPUT_SEQUENCE } from './constants';
import { WS_ERROR_SEQUENCE } from './constants';


export function wsResponseSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_RESPONSE_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}


export function wsThroughputSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_THROUGHPUT_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}


export function wsErrorSequence(
  state = { status: 'initial' },
  action,
) {
  switch (action.type) {
    case WS_ERROR_SEQUENCE:
      return action.payload;
    default:
      return state;
  }
}
