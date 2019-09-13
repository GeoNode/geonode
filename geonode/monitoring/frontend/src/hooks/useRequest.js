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

import { useEffect, useState } from 'react';

export default function useRequest (request, params, update = []) {
    const [response, setResponse] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(false);
    useEffect(() => {
        setResponse({});
        setLoading(true);
        setError(null);
        let isMounted = true;
        request(params)
            .then(([err, res]) => {
                if (isMounted) {
                    setResponse(res || {});
                    setLoading(false);
                    setError(err);
                }
            });
        return function() {
            isMounted = false;
        }
    }, update);
    return [
        response,
        loading,
        error
    ];
}
