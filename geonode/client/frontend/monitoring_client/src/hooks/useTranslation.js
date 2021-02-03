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
import axios from 'axios';
import { useEffect, useState } from 'react';

export default function useTranslation() {
    const [response, setResponse] = useState({ locale: 'en', messages: {} });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(false);

    useEffect(function() {
        setResponse({ locale: 'en', messages: {} });
        setLoading(true);
        setError(null);
        let isMounted = true;
        axios.get(`${__TRANSLATION_PATH__}index.json`)
            .then(function({ data }) {
                const { supportedLocales = [] } = data || {};
                const currentLocale = 'en';
                return supportedLocales.find(locale => currentLocale === locale) || 'en';
            })
            .then((selectedLocale) => axios.get(`${__TRANSLATION_PATH__}${selectedLocale}.json`))
            .then(({ data }) => {
                if (isMounted) {
                    setLoading(false);
                    setResponse(data);
                }
            })
            .catch(() => {
                setLoading(false);
                setError(true);
            });

            return function() {
                isMounted = false;
            };
    }, []);

    return [
        response,
        loading,
        error
    ];
}
