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

import React, { useEffect, useState } from 'react';
import min from 'lodash/min';
import max from 'lodash/max';
import range from 'lodash/range';
import head from 'lodash/head';
import chroma from 'chroma-js';
import axios from 'axios';
import {
    ComposableMap,
    ZoomableGroup,
    Graticule,
    Geographies,
    Geography
} from 'react-simple-maps';
import ReactTooltip from 'react-tooltip'
import { FormattedMessage } from 'react-intl';

const colorScale = chroma.scale(['#c0d8ed', '#1b4060']);

const wrapperStyles = {
    width: "100%",
    maxWidth: 980,
    margin: "0 auto",
    padding: 16
};

const getLegend = (data, classes) => {
    
    const counts = data.map(({count}) => count);
    const minValue = min(counts);
    const maxValue = max(counts);
    const delta = (maxValue - minValue) / classes;
    const legend = range(classes)
    .map((idx) => {
        return [
            minValue + idx * delta,
            minValue + (idx + 1) * delta,
            colorScale(idx / classes).hex()
        ];
    });
    return {
        legend,
        setColor: (count) =>
            head(legend.filter(([minVal, maxVal]) => count >= minVal && count <= maxVal).map(entry => entry[2]))
    };
    
};

export default function Map({ id, data }) {
    const { setColor, legend } = getLegend(data, 5);
    const [geography, setGeography] = useState(null);

    useEffect(() => {
        let isMounted = true;
        axios.get(`${__ASSETS_PATH__}world-50m.json`)
            .then(({ data }) => {
                if (isMounted) {
                    setGeography(data);
                    ReactTooltip.rebuild();
                }
            });
        return function() {
            isMounted = false;
        };
    }, [ ]);

    return (
        <div
            id={id}
            style={wrapperStyles}>
            <ComposableMap
                projectionConfig={{
                    scale: 160,
                    rotation: [0, 0, 0],
                }}
                projection="robinson"
                width={1024}
                height={512}
                style={{
                    width: "100%",
                    height: "auto",
                }}>
                <ZoomableGroup
                    center={[0, 0]}
                    disablePanning>
                    <Graticule />
                    {geography && <Geographies
                        geography={geography}>
                        {(geographies, projection) => geographies.map((geography, i) => {
                            const { count = 0 } = (data || []).find(({ name }) => geography.id === name) || {};
                            const color = count === 0 ? '#ffffff' : setColor(count);
                            return (
                                <Geography
                                    key={i}
                                    geography={geography}
                                    projection={projection}
                                    data-tip={`${geography.properties.name} ${count}`}
                                    style={{
                                        default: {
                                            fill: color,
                                            stroke: '#2c689c',
                                            strokeWidth: 0.5,
                                            outline: 'none'
                                        },
                                        hover: {
                                            fill: color,
                                            stroke: '#2c689c',
                                            strokeWidth: 0.5,
                                            outline: 'none'
                                        },
                                        pressed: {
                                            fill: color,
                                            stroke: '#2c689c',
                                            strokeWidth: 0.5,
                                            outline: 'none'
                                        }
                                    }}
                                />
                            );
                        })}
                    </Geographies>}
                </ZoomableGroup>
            </ComposableMap>
            <ReactTooltip />
            <div><FormattedMessage id="count" defaultMessage="Count"/></div>
            {legend.map(([from, to, backgroundColor], idx) => {
                return (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center' }}>
                        <div
                            style={{
                                border: `1px solid #2c689c`,
                                backgroundColor,
                                width: 10,
                                height: 10,
                                marginRight: 8
                            }}>
                        </div>
                        <div style={{ flex: 1 }}>{Math.round(from)}{' - '}{Math.round(to)}</div>
                    </div>
                );
            })}
        </div>
    );
}
