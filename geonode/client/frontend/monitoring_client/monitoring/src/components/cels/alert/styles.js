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

export default {
  content: {
    width: '100%',
    padding: 10,
    marginTop: 10,
  },

  date: {
    fontWeight: 'bold',
    marginBottom: 5,
  },

  short: {
    color: '#ffa031',
    marginBottom: 5,
  },

  hiddenDetail: {
    maxHeight: 0,
    overflow: 'hidden',
    transition: 'max-height 0.5s ease-out',
  },

  shownDetail: {
    maxHeight: 50,
    overflow: 'hidden',
    transition: 'max-height 0.5s ease-in',
  },
};
