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

import React, { useContext } from 'react';

import Container from '@material-ui/core/Container';
import Grid from '@material-ui/core/Grid';
import useStyles from '../hooks/useStyles';
import Typography from '@material-ui/core/Typography';
import PersonIcon from '@material-ui/icons/Person';
import PersonOutlinedIcon from '@material-ui/icons/PersonOutlined';
import VisibilityIcon from '@material-ui/icons/Visibility';
import Divider from '@material-ui/core/Divider';

import {
    getUserAgentFamilyCount,
    getCountriesCount,
    getUserAgentCount,
    getUsersCount,
    getLayersCount,
    getMapsCount,
    getDocumentsCount,
    getRequestHitsCount,
    getRequestVisitorsCount,
    getResourcesHitsList,
    getResourcesVisitorsList,
    getRequestAnonymousCount,
    getResourcesAnonymousList,
    getEventsDates
} from '../api';

import { ranges, setTimeRangeProperties } from '../utils/TimeRangeUtils';

import TimeRangeSelect from '../components/TimeRangeSelect';
import Map from '../components/Map';
import Calendar from '../components/Calendar';
import { RequestCounter } from '../components/Counter';
import { RequestTable } from '../components/Table';
import { RequestChart } from '../components/Chart';
import { getDetailsPath } from '../utils/RouteUtils';
import AnalyticsContext from '../context';
import { FormattedMessage } from 'react-intl';

export default function Analytics({ maxCount = 10, timeRange = 'year', history }) {
    const classes = useStyles();
    const { getRange } = ranges[timeRange];
    const timeRangeProperties = getRange();
    const { timeRangeLabel } = timeRangeProperties;
    setTimeRangeProperties(timeRangeProperties);

    const handleUpdate = (params = {}) => {
        history.push(
            getDetailsPath({
                timeRange,
                ...params
            })
        );
    };

    const { homeUrl = {}, layersUrl = {} } = useContext(AnalyticsContext);

    return (
        <Container
            maxWidth="lg"
            className={classes.container}>
            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <Typography
                        component="h1"
                        variant="h6">
                        <FormattedMessage id="currentNumberOfResources" defaultMessage="Current Number of Resources"/>
                    </Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                    <RequestCounter
                        timeRange={timeRange}
                        globalTimeRange
                        label={<FormattedMessage id="layers" defaultMessage="Layers"/>}
                        requests={{
                            count: {
                                label: <FormattedMessage id="count" defaultMessage="Count"/>,
                                request: getLayersCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={3}>
                    <RequestCounter
                        timeRange={timeRange}
                        globalTimeRange
                        label={<FormattedMessage id="maps" defaultMessage="Maps"/>}
                        requests={{
                            count: {
                                label: <FormattedMessage id="count" defaultMessage="Count"/>,
                                request: getMapsCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={3}>
                    <RequestCounter
                        timeRange={timeRange}
                        globalTimeRange
                        label={<FormattedMessage id="documents" defaultMessage="Documents"/>}
                        requests={{
                            count: {
                                label: <FormattedMessage id="count" defaultMessage="Count"/>,
                                request: getDocumentsCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={3}>
                    <RequestCounter
                        timeRange={timeRange}
                        globalTimeRange
                        label={<FormattedMessage id="users" defaultMessage="Users"/>}
                        requests={{
                            count: {
                                label: <FormattedMessage id="count" defaultMessage="Count"/>,
                                request: getUsersCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12}>
                    <Divider />
                </Grid>
                <Grid item xs={12} className={classes.stickyHeader} style={{ paddingBottom: 0 }}>
                    <TimeRangeSelect
                        timeRange={timeRange}
                        readOnly
                        label={timeRangeLabel}/>
                </Grid>
                <Grid item xs={12}>
                    <RequestChart
                        label={<FormattedMessage id="allRequestsCount" defaultMessage="All Requests Count"/>}/>
                </Grid>
                <Grid item xs={12}>
                    <Divider />
                </Grid>

                <Grid item xs={12}>
                    <Typography
                        component="h1"
                        variant="h6">
                        <FormattedMessage id="totalRequestsNumberByResource" defaultMessage="Total Number of Requests by Resource"/>
                    </Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                    <RequestCounter
                        label={<FormattedMessage id="layers" defaultMessage="Layers"/>}
                        resourceType="layer"
                        globalTimeRange
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getRequestHitsCount
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getRequestVisitorsCount
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getRequestAnonymousCount
                            }
                        }}/>
                </Grid>
                <Grid item xs={12} md={3}>
                    <RequestCounter
                        label={<FormattedMessage id="maps" defaultMessage="Maps"/>}
                        resourceType="map"
                        globalTimeRange
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getRequestHitsCount
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getRequestVisitorsCount
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getRequestAnonymousCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={3}>
                    <RequestCounter
                        label={<FormattedMessage id="documents" defaultMessage="Documents"/>}
                        resourceType="document"
                        globalTimeRange
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getRequestHitsCount
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getRequestVisitorsCount
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getRequestAnonymousCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={3}>
                    <RequestCounter
                        label={homeUrl.id === undefined ? layersUrl.name : <FormattedMessage id="homepage" defaultMessage="Homepage"/>}
                        resourceType="url"
                        resourceId={homeUrl.id || layersUrl.id}
                        globalTimeRange
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getRequestHitsCount
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getRequestVisitorsCount
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getRequestAnonymousCount
                            }
                        }}  />
                </Grid>
                <Grid item xs={12}>
                    <Divider />
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                    <RequestTable
                        maxCount={maxCount}
                        showLink
                        label={(count) => <FormattedMessage id="mostFrequentlyAccessedResources10" defaultMessage="{count} Most Frequently Accessed Resources" values={{ count }}/>}
                        onSelect={(resource) => 
                            handleUpdate({
                                resourceType: resource.type,
                                resourceId: resource.id
                            })}
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getResourcesHitsList
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getResourcesVisitorsList
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getResourcesAnonymousList
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                    <RequestTable
                        maxCount={maxCount}
                        header={({ items }) => items && items.length > 0 && <Map id="map-overview" data={items} />}
                        label={(count) => <FormattedMessage id="mostActiveCountries10" defaultMessage="{count} Most Active Countries" values={{ count }}/>}
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                request: getCountriesCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                    <RequestTable
                        maxCount={maxCount}
                        label={(count) => <FormattedMessage id="mostFrequentlyUsedUserAgentsFamily10" defaultMessage="{count} Most Frequently Used User Agents Family" values={{ count }}/>}
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                request: getUserAgentFamilyCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                    <RequestTable
                        maxCount={maxCount}
                        label={(count) => <FormattedMessage id="mostFrequentlyUsedUserAgents10" defaultMessage="{count} Most Frequently Used User Agents" values={{ count }}/>}
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                request: getUserAgentCount
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                    <RequestTable
                        maxCount={maxCount}
                        showLink
                        label={(count) => <FormattedMessage id="mostFrequentlyAccessedLayers10" defaultMessage="{count} Most Frequently Accessed Layers" values={{ count }}/>}
                        resourceType="layer"
                        onSelect={(resource) => 
                            handleUpdate({
                                resourceType: resource.type,
                                resourceId: resource.id
                            })}
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getResourcesHitsList
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getResourcesVisitorsList
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getResourcesAnonymousList
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                    <RequestTable
                        maxCount={maxCount}
                        showLink
                        label={(count) => <FormattedMessage id="mostFrequentlyAccessedMaps10" defaultMessage="{count} Most Frequently Accessed Maps" values={{ count }}/>}
                        resourceType="map"
                        onSelect={(resource) => 
                            handleUpdate({
                                resourceType: resource.type,
                                resourceId: resource.id
                            })}
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getResourcesHitsList
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getResourcesVisitorsList
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getResourcesAnonymousList
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                    <RequestTable
                        maxCount={maxCount}
                        showLink
                        label={(count) => <FormattedMessage id="mostFrequentlyAccessedDocuments10" defaultMessage="{count} Most Frequently Accessed Documents" values={{ count }}/>}
                        resourceType="document"
                        onSelect={(resource) => 
                            handleUpdate({
                                resourceType: resource.type,
                                resourceId: resource.id
                            })}
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getResourcesHitsList
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getResourcesVisitorsList
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getResourcesAnonymousList
                            }
                        }} />
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                    <RequestTable
                        maxCount={maxCount}
                        showLink
                        label={(count) => <FormattedMessage id="mostFrequentlyAccessedUrls10" defaultMessage="{count} Most Frequently Accessed Urls" values={{ count }}/>}
                        resourceType="url"
                        onSelect={(resource) => 
                            handleUpdate({
                                resourceType: resource.type,
                                resourceId: resource.id
                            })}
                        requests={{
                            hits: {
                                label: <FormattedMessage id="hits" defaultMessage="Hits"/>,
                                Icon: VisibilityIcon,
                                request: getResourcesHitsList
                            },
                            visitors: {
                                label: <FormattedMessage id="uniqueVisitors" defaultMessage="Unique Visitors"/>,
                                Icon: PersonIcon,
                                request: getResourcesVisitorsList
                            },
                            anonymous: {
                                label: <FormattedMessage id="anonymousSessions" defaultMessage="Anonymous Sessions"/>,
                                Icon: PersonOutlinedIcon,
                                request: getResourcesAnonymousList
                            }
                        }} />
                </Grid>
                <Grid item xs={12}>
                    <Calendar
                        label={<FormattedMessage id="layersPublication" defaultMessage="Layers Publication"/>}
                        resourceType="layer"
                        eventType="upload"
                        globalTimeRange
                        timeRange={timeRange}
                        request={getEventsDates}
                        tooltip={({ count = 0 }) => `${count} ${count === 1 ? 'publication' : 'publications'}`}/>
                </Grid>
                <Grid item xs={12}>
                    <Calendar
                        label={<FormattedMessage id="documentsPublication" defaultMessage="Documents Publication"/>}
                        resourceType="document"
                        eventType="upload"
                        globalTimeRange
                        timeRange={timeRange}
                        request={getEventsDates}
                        tooltip={({ count = 0 }) => `${count} ${count === 1 ? 'publication' : 'publications'}`}/>
                </Grid>
                <Grid item xs={12}>
                    <Calendar
                        label={<FormattedMessage id="mapsPublication" defaultMessage="Maps Publication"/>}
                        resourceType="map"
                        eventType="create"
                        globalTimeRange
                        timeRange={timeRange}
                        request={getEventsDates}
                        tooltip={({ count = 0 }) => `${count} ${count === 1 ? 'publication' : 'publications'}`} />
                </Grid>
            </Grid>
        </Container>
    );
}