# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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
from __future__ import print_function

from datetime import datetime, timedelta

from xml.etree.ElementTree import fromstring
import json
import xmljson
from decimal import Decimal
from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core import mail

from geonode.contrib.monitoring.models import (RequestEvent, Host, Service, ServiceType,
                                               populate, ExceptionEvent, MetricNotificationCheck,
                                               MetricValue, NotificationCheck, Metric, OWSService,
                                               MonitoredResource, MetricLabel,
                                               NotificationMetricDefinition,)
from geonode.contrib.monitoring.models import do_autoconfigure

from geonode.contrib.monitoring.collector import CollectorAPI
from geonode.contrib.monitoring.utils import generate_periods, align_period_start
from geonode.base.populate_test_data import create_models
from geonode.layers.models import Layer

req_err_xml = """<org.geoserver.monitor.RequestData>
  <internalid>1825</internalid>
  <id>1825</id>
  <status>FAILED</status>
  <category>OWS</category>
  <path>/wms</path>
  <queryString>SERVICE=WMS&amp;VERSION=1.3.0&amp;REQUEST=GetMap&amp;FORMAT=image/png8&amp;TRANSPARENT=true&amp;LAYERS=unesco:Unesco_point&amp;STYLES=&amp;SRS=EPSG:3857&amp;CRS=EPSG:900913&amp;TILED=false&amp;WIDTH=256&amp;HEIGHT=256&amp;BBOX=-6261721.357121639,1252344.271424327,-5009377.085697311,2504688.542848655</queryString>
  <body></body>
  <bodyContentLength>0</bodyContentLength>
  <httpMethod>GET</httpMethod>
  <startTime>2017-06-20 11:33:22.336 UTC</startTime>
  <endTime>2017-06-20 11:33:22.344 UTC</endTime>
  <totalTime>8</totalTime>
  <remoteAddr>217.110.187.74</remoteAddr>
  <remoteHost>217.110.187.74</remoteHost>
  <remoteUser>anonymous</remoteUser>
  <remoteUserAgent>Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36</remoteUserAgent>
  <remoteLat>0.0</remoteLat>
  <remoteLon>0.0</remoteLon>
  <host>demo.geo-solutions.it</host>
  <internalHost>ks390295.kimsufi.com</internalHost>
  <service>WMS</service>
  <operation>GetMap</operation>
  <owsVersion>1.3.0</owsVersion>
  <resources>
    <string>unesco:Unesco_point</string>
  </resources>
  <responseLength>447</responseLength>
  <responseContentType>text/xml;charset=UTF-8</responseContentType>
  <errorMessage>Rendering process failed</errorMessage>
  <error class="org.geoserver.platform.ServiceException">
    <detailMessage>Rendering process failed</detailMessage>
    <cause class="java.lang.Exception">
      <detailMessage>Error transforming bbox</detailMessage>
      <cause class="java.lang.IndexOutOfBoundsException">
        <detailMessage>Index: 0</detailMessage>
        <stackTrace>
          <trace>java.util.Collections$EmptyList.get(Collections.java:4454)</trace>
          <trace>org.geotools.renderer.lite.StreamingRenderer.createBBoxFilters(StreamingRenderer.java:1666)</trace>
          <trace>org.geotools.renderer.lite.StreamingRenderer.getStyleQuery(StreamingRenderer.java:1040)</trace>
          <trace>org.geotools.renderer.lite.StreamingRenderer.getFeatures(StreamingRenderer.java:1948)</trace>
          <trace>org.geotools.renderer.lite.StreamingRenderer.processStylers(StreamingRenderer.java:1916)</trace>
          <trace>org.geotools.renderer.lite.StreamingRenderer.paint(StreamingRenderer.java:829)</trace>
          <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:553)</trace>
          <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:276)</trace>
          <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:139)</trace>
          <trace>org.geoserver.wms.GetMap.executeInternal(GetMap.java:623)</trace>
          <trace>org.geoserver.wms.GetMap.run(GetMap.java:279)</trace>
          <trace>org.geoserver.wms.GetMap.run(GetMap.java:125)</trace>
          <trace>org.geoserver.wms.DefaultWebMapService.getMap(DefaultWebMapService.java:320)</trace>
          <trace>sun.reflect.GeneratedMethodAccessor496.invoke(Unknown Source)</trace>
          <trace>sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)</trace>
          <trace>java.lang.reflect.Method.invoke(Method.java:498)</trace>
          <trace>org.springframework.aop.support.AopUtils.invokeJoinpointUsingReflection(AopUtils.java:302)</trace>
          <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.invokeJoinpoint(ReflectiveMethodInvocation.java:190)</trace>
          <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:157)</trace>
          <trace>org.geoserver.kml.WebMapServiceKmlInterceptor.invoke(WebMapServiceKmlInterceptor.java:34)</trace>
          <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
          <trace>org.geoserver.gwc.wms.CacheSeedingWebMapService.invoke(CacheSeedingWebMapService.java:62)</trace>
          <trace>org.geoserver.gwc.wms.CacheSeedingWebMapService.invoke(CacheSeedingWebMapService.java:36)</trace>
          <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
          <trace>org.geoserver.gwc.wms.CachingWebMapService.invoke(CachingWebMapService.java:80)</trace>
          <trace>org.geoserver.gwc.wms.CachingWebMapService.invoke(CachingWebMapService.java:55)</trace>
          <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
          <trace>org.geoserver.ows.util.RequestObjectLogger.invoke(RequestObjectLogger.java:55)</trace>
          <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
          <trace>org.springframework.aop.framework.JdkDynamicAopProxy.invoke(JdkDynamicAopProxy.java:208)</trace>
          <trace>com.sun.proxy.$Proxy127.getMap(Unknown Source)</trace>
          <trace>sun.reflect.GeneratedMethodAccessor508.invoke(Unknown Source)</trace>
          <trace>sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)</trace>
          <trace>java.lang.reflect.Method.invoke(Method.java:498)</trace>
          <trace>org.geoserver.ows.Dispatcher.execute(Dispatcher.java:857)</trace>
          <trace>org.geoserver.ows.Dispatcher.handleRequestInternal(Dispatcher.java:268)</trace>
          <trace>org.springframework.web.servlet.mvc.AbstractController.handleRequest(AbstractController.java:147)</trace>
          <trace>org.springframework.web.servlet.mvc.SimpleControllerHandlerAdapter.handle(SimpleControllerHandlerAdapter.java:50)</trace>
          <trace>org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:959)</trace>
          <trace>org.springframework.web.servlet.DispatcherServlet.doService(DispatcherServlet.java:893)</trace>
          <trace>org.springframework.web.servlet.FrameworkServlet.processRequest(FrameworkServlet.java:968)</trace>
          <trace>org.springframework.web.servlet.FrameworkServlet.doGet(FrameworkServlet.java:859)</trace>
          <trace>javax.servlet.http.HttpServlet.service(HttpServlet.java:621)</trace>
          <trace>org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:844)</trace>
          <trace>javax.servlet.http.HttpServlet.service(HttpServlet.java:722)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:305)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.geoserver.filters.ThreadLocalsCleanupFilter.doFilter(ThreadLocalsCleanupFilter.java:28)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:75)</trace>
          <trace>org.geoserver.wms.animate.AnimatorFilter.doFilter(AnimatorFilter.java:71)</trace>
          <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
          <trace>org.geoserver.monitor.MonitorFilter.doFilter(MonitorFilter.java:144)</trace>
          <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
          <trace>org.geoserver.gwc.web.blob.SqliteMultipartFilter.doFilterInternal(SqliteMultipartFilter.java:20)</trace>
          <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
          <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
          <trace>org.geoserver.flow.controller.IpBlacklistFilter.doFilter(IpBlacklistFilter.java:94)</trace>
          <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
          <trace>org.geoserver.filters.SpringDelegatingFilter.doFilter(SpringDelegatingFilter.java:46)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.geoserver.platform.AdvancedDispatchFilter.doFilter(AdvancedDispatchFilter.java:50)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:316)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
          <trace>org.springframework.security.web.access.intercept.FilterSecurityInterceptor.invoke(FilterSecurityInterceptor.java:126)</trace>
          <trace>org.springframework.security.web.access.intercept.FilterSecurityInterceptor.doFilter(FilterSecurityInterceptor.java:90)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
          <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
          <trace>org.springframework.security.web.access.ExceptionTranslationFilter.doFilter(ExceptionTranslationFilter.java:114)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
          <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
          <trace>org.geoserver.security.filter.GeoServerAnonymousAuthenticationFilter.doFilter(GeoServerAnonymousAuthenticationFilter.java:54)</trace>
          <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
          <trace>org.springframework.security.web.authentication.www.BasicAuthenticationFilter.doFilterInternal(BasicAuthenticationFilter.java:158)</trace>
          <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
          <trace>org.geoserver.security.filter.GeoServerBasicAuthenticationFilter.doFilter(GeoServerBasicAuthenticationFilter.java:84)</trace>
          <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
          <trace>org.springframework.security.web.context.SecurityContextPersistenceFilter.doFilter(SecurityContextPersistenceFilter.java:91)</trace>
          <trace>org.geoserver.security.filter.GeoServerSecurityContextPersistenceFilter$1.doFilter(GeoServerSecurityContextPersistenceFilter.java:53)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
          <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
          <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
          <trace>org.springframework.security.web.FilterChainProxy.doFilterInternal(FilterChainProxy.java:213)</trace>
          <trace>org.springframework.security.web.FilterChainProxy.doFilter(FilterChainProxy.java:176)</trace>
          <trace>org.geoserver.security.GeoServerSecurityFilterChainProxy.doFilter(GeoServerSecurityFilterChainProxy.java:152)</trace>
          <trace>org.springframework.web.filter.DelegatingFilterProxy.invokeDelegate(DelegatingFilterProxy.java:346)</trace>
          <trace>org.springframework.web.filter.DelegatingFilterProxy.doFilter(DelegatingFilterProxy.java:262)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.geoserver.filters.LoggingFilter.doFilter(LoggingFilter.java:87)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.geoserver.filters.XFrameOptionsFilter.doFilter(XFrameOptionsFilter.java:89)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.geoserver.filters.GZIPFilter.doFilter(GZIPFilter.java:42)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.geoserver.filters.SessionDebugFilter.doFilter(SessionDebugFilter.java:48)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.geoserver.filters.FlushSafeFilter.doFilter(FlushSafeFilter.java:44)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.springframework.web.filter.CharacterEncodingFilter.doFilterInternal(CharacterEncodingFilter.java:121)</trace>
          <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
          <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
          <trace>org.apache.catalina.core.StandardWrapperValve.invoke(StandardWrapperValve.java:224)</trace>
          <trace>org.apache.catalina.core.StandardContextValve.invoke(StandardContextValve.java:169)</trace>
          <trace>org.apache.catalina.authenticator.AuthenticatorBase.invoke(AuthenticatorBase.java:472)</trace>
          <trace>org.apache.catalina.core.StandardHostValve.invoke(StandardHostValve.java:168)</trace>
          <trace>org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:98)</trace>
          <trace>org.apache.catalina.valves.AccessLogValve.invoke(AccessLogValve.java:927)</trace>
          <trace>org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:118)</trace>
          <trace>org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:407)</trace>
          <trace>org.apache.coyote.ajp.AjpProcessor.process(AjpProcessor.java:200)</trace>
          <trace>org.apache.coyote.AbstractProtocol$AbstractConnectionHandler.process(AbstractProtocol.java:579)</trace>
          <trace>org.apache.tomcat.util.net.JIoEndpoint$SocketProcessor.run(JIoEndpoint.java:307)</trace>
          <trace>java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)</trace>
          <trace>java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)</trace>
          <trace>java.lang.Thread.run(Thread.java:745)</trace>
        </stackTrace>
        <suppressedExceptions class="java.util.Collections$UnmodifiableRandomAccessList" resolves-to="java.util.Collections$UnmodifiableList">
          <c class="list"/>
          <list reference="../c"/>
        </suppressedExceptions>
      </cause>
      <stackTrace>
        <trace>org.geotools.renderer.lite.StreamingRenderer.getStyleQuery(StreamingRenderer.java:1050)</trace>
        <trace>org.geotools.renderer.lite.StreamingRenderer.getFeatures(StreamingRenderer.java:1948)</trace>
        <trace>org.geotools.renderer.lite.StreamingRenderer.processStylers(StreamingRenderer.java:1916)</trace>
        <trace>org.geotools.renderer.lite.StreamingRenderer.paint(StreamingRenderer.java:829)</trace>
        <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:553)</trace>
        <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:276)</trace>
        <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:139)</trace>
        <trace>org.geoserver.wms.GetMap.executeInternal(GetMap.java:623)</trace>
        <trace>org.geoserver.wms.GetMap.run(GetMap.java:279)</trace>
        <trace>org.geoserver.wms.GetMap.run(GetMap.java:125)</trace>
        <trace>org.geoserver.wms.DefaultWebMapService.getMap(DefaultWebMapService.java:320)</trace>
        <trace>sun.reflect.GeneratedMethodAccessor496.invoke(Unknown Source)</trace>
        <trace>sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)</trace>
        <trace>java.lang.reflect.Method.invoke(Method.java:498)</trace>
        <trace>org.springframework.aop.support.AopUtils.invokeJoinpointUsingReflection(AopUtils.java:302)</trace>
        <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.invokeJoinpoint(ReflectiveMethodInvocation.java:190)</trace>
        <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:157)</trace>
        <trace>org.geoserver.kml.WebMapServiceKmlInterceptor.invoke(WebMapServiceKmlInterceptor.java:34)</trace>
        <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
        <trace>org.geoserver.gwc.wms.CacheSeedingWebMapService.invoke(CacheSeedingWebMapService.java:62)</trace>
        <trace>org.geoserver.gwc.wms.CacheSeedingWebMapService.invoke(CacheSeedingWebMapService.java:36)</trace>
        <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
        <trace>org.geoserver.gwc.wms.CachingWebMapService.invoke(CachingWebMapService.java:80)</trace>
        <trace>org.geoserver.gwc.wms.CachingWebMapService.invoke(CachingWebMapService.java:55)</trace>
        <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
        <trace>org.geoserver.ows.util.RequestObjectLogger.invoke(RequestObjectLogger.java:55)</trace>
        <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
        <trace>org.springframework.aop.framework.JdkDynamicAopProxy.invoke(JdkDynamicAopProxy.java:208)</trace>
        <trace>com.sun.proxy.$Proxy127.getMap(Unknown Source)</trace>
        <trace>sun.reflect.GeneratedMethodAccessor508.invoke(Unknown Source)</trace>
        <trace>sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)</trace>
        <trace>java.lang.reflect.Method.invoke(Method.java:498)</trace>
        <trace>org.geoserver.ows.Dispatcher.execute(Dispatcher.java:857)</trace>
        <trace>org.geoserver.ows.Dispatcher.handleRequestInternal(Dispatcher.java:268)</trace>
        <trace>org.springframework.web.servlet.mvc.AbstractController.handleRequest(AbstractController.java:147)</trace>
        <trace>org.springframework.web.servlet.mvc.SimpleControllerHandlerAdapter.handle(SimpleControllerHandlerAdapter.java:50)</trace>
        <trace>org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:959)</trace>
        <trace>org.springframework.web.servlet.DispatcherServlet.doService(DispatcherServlet.java:893)</trace>
        <trace>org.springframework.web.servlet.FrameworkServlet.processRequest(FrameworkServlet.java:968)</trace>
        <trace>org.springframework.web.servlet.FrameworkServlet.doGet(FrameworkServlet.java:859)</trace>
        <trace>javax.servlet.http.HttpServlet.service(HttpServlet.java:621)</trace>
        <trace>org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:844)</trace>
        <trace>javax.servlet.http.HttpServlet.service(HttpServlet.java:722)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:305)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.geoserver.filters.ThreadLocalsCleanupFilter.doFilter(ThreadLocalsCleanupFilter.java:28)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:75)</trace>
        <trace>org.geoserver.wms.animate.AnimatorFilter.doFilter(AnimatorFilter.java:71)</trace>
        <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
        <trace>org.geoserver.monitor.MonitorFilter.doFilter(MonitorFilter.java:144)</trace>
        <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
        <trace>org.geoserver.gwc.web.blob.SqliteMultipartFilter.doFilterInternal(SqliteMultipartFilter.java:20)</trace>
        <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
        <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
        <trace>org.geoserver.flow.controller.IpBlacklistFilter.doFilter(IpBlacklistFilter.java:94)</trace>
        <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
        <trace>org.geoserver.filters.SpringDelegatingFilter.doFilter(SpringDelegatingFilter.java:46)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.geoserver.platform.AdvancedDispatchFilter.doFilter(AdvancedDispatchFilter.java:50)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:316)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
        <trace>org.springframework.security.web.access.intercept.FilterSecurityInterceptor.invoke(FilterSecurityInterceptor.java:126)</trace>
        <trace>org.springframework.security.web.access.intercept.FilterSecurityInterceptor.doFilter(FilterSecurityInterceptor.java:90)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
        <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
        <trace>org.springframework.security.web.access.ExceptionTranslationFilter.doFilter(ExceptionTranslationFilter.java:114)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
        <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
        <trace>org.geoserver.security.filter.GeoServerAnonymousAuthenticationFilter.doFilter(GeoServerAnonymousAuthenticationFilter.java:54)</trace>
        <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
        <trace>org.springframework.security.web.authentication.www.BasicAuthenticationFilter.doFilterInternal(BasicAuthenticationFilter.java:158)</trace>
        <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
        <trace>org.geoserver.security.filter.GeoServerBasicAuthenticationFilter.doFilter(GeoServerBasicAuthenticationFilter.java:84)</trace>
        <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
        <trace>org.springframework.security.web.context.SecurityContextPersistenceFilter.doFilter(SecurityContextPersistenceFilter.java:91)</trace>
        <trace>org.geoserver.security.filter.GeoServerSecurityContextPersistenceFilter$1.doFilter(GeoServerSecurityContextPersistenceFilter.java:53)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
        <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
        <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
        <trace>org.springframework.security.web.FilterChainProxy.doFilterInternal(FilterChainProxy.java:213)</trace>
        <trace>org.springframework.security.web.FilterChainProxy.doFilter(FilterChainProxy.java:176)</trace>
        <trace>org.geoserver.security.GeoServerSecurityFilterChainProxy.doFilter(GeoServerSecurityFilterChainProxy.java:152)</trace>
        <trace>org.springframework.web.filter.DelegatingFilterProxy.invokeDelegate(DelegatingFilterProxy.java:346)</trace>
        <trace>org.springframework.web.filter.DelegatingFilterProxy.doFilter(DelegatingFilterProxy.java:262)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.geoserver.filters.LoggingFilter.doFilter(LoggingFilter.java:87)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.geoserver.filters.XFrameOptionsFilter.doFilter(XFrameOptionsFilter.java:89)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.geoserver.filters.GZIPFilter.doFilter(GZIPFilter.java:42)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.geoserver.filters.SessionDebugFilter.doFilter(SessionDebugFilter.java:48)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.geoserver.filters.FlushSafeFilter.doFilter(FlushSafeFilter.java:44)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.springframework.web.filter.CharacterEncodingFilter.doFilterInternal(CharacterEncodingFilter.java:121)</trace>
        <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
        <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
        <trace>org.apache.catalina.core.StandardWrapperValve.invoke(StandardWrapperValve.java:224)</trace>
        <trace>org.apache.catalina.core.StandardContextValve.invoke(StandardContextValve.java:169)</trace>
        <trace>org.apache.catalina.authenticator.AuthenticatorBase.invoke(AuthenticatorBase.java:472)</trace>
        <trace>org.apache.catalina.core.StandardHostValve.invoke(StandardHostValve.java:168)</trace>
        <trace>org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:98)</trace>
        <trace>org.apache.catalina.valves.AccessLogValve.invoke(AccessLogValve.java:927)</trace>
        <trace>org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:118)</trace>
        <trace>org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:407)</trace>
        <trace>org.apache.coyote.ajp.AjpProcessor.process(AjpProcessor.java:200)</trace>
        <trace>org.apache.coyote.AbstractProtocol$AbstractConnectionHandler.process(AbstractProtocol.java:579)</trace>
        <trace>org.apache.tomcat.util.net.JIoEndpoint$SocketProcessor.run(JIoEndpoint.java:307)</trace>
        <trace>java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)</trace>
        <trace>java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)</trace>
        <trace>java.lang.Thread.run(Thread.java:745)</trace>
      </stackTrace>
      <suppressedExceptions class="java.util.Collections$UnmodifiableRandomAccessList" reference="../cause/suppressedExceptions"/>
    </cause>
    <stackTrace>
      <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:583)</trace>
      <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:276)</trace>
      <trace>org.geoserver.wms.map.RenderedImageMapOutputFormat.produceMap(RenderedImageMapOutputFormat.java:139)</trace>
      <trace>org.geoserver.wms.GetMap.executeInternal(GetMap.java:623)</trace>
      <trace>org.geoserver.wms.GetMap.run(GetMap.java:279)</trace>
      <trace>org.geoserver.wms.GetMap.run(GetMap.java:125)</trace>
      <trace>org.geoserver.wms.DefaultWebMapService.getMap(DefaultWebMapService.java:320)</trace>
      <trace>sun.reflect.GeneratedMethodAccessor496.invoke(Unknown Source)</trace>
      <trace>sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)</trace>
      <trace>java.lang.reflect.Method.invoke(Method.java:498)</trace>
      <trace>org.springframework.aop.support.AopUtils.invokeJoinpointUsingReflection(AopUtils.java:302)</trace>
      <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.invokeJoinpoint(ReflectiveMethodInvocation.java:190)</trace>
      <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:157)</trace>
      <trace>org.geoserver.kml.WebMapServiceKmlInterceptor.invoke(WebMapServiceKmlInterceptor.java:34)</trace>
      <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
      <trace>org.geoserver.gwc.wms.CacheSeedingWebMapService.invoke(CacheSeedingWebMapService.java:62)</trace>
      <trace>org.geoserver.gwc.wms.CacheSeedingWebMapService.invoke(CacheSeedingWebMapService.java:36)</trace>
      <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
      <trace>org.geoserver.gwc.wms.CachingWebMapService.invoke(CachingWebMapService.java:80)</trace>
      <trace>org.geoserver.gwc.wms.CachingWebMapService.invoke(CachingWebMapService.java:55)</trace>
      <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
      <trace>org.geoserver.ows.util.RequestObjectLogger.invoke(RequestObjectLogger.java:55)</trace>
      <trace>org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:179)</trace>
      <trace>org.springframework.aop.framework.JdkDynamicAopProxy.invoke(JdkDynamicAopProxy.java:208)</trace>
      <trace>com.sun.proxy.$Proxy127.getMap(Unknown Source)</trace>
      <trace>sun.reflect.GeneratedMethodAccessor508.invoke(Unknown Source)</trace>
      <trace>sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)</trace>
      <trace>java.lang.reflect.Method.invoke(Method.java:498)</trace>
      <trace>org.geoserver.ows.Dispatcher.execute(Dispatcher.java:857)</trace>
      <trace>org.geoserver.ows.Dispatcher.handleRequestInternal(Dispatcher.java:268)</trace>
      <trace>org.springframework.web.servlet.mvc.AbstractController.handleRequest(AbstractController.java:147)</trace>
      <trace>org.springframework.web.servlet.mvc.SimpleControllerHandlerAdapter.handle(SimpleControllerHandlerAdapter.java:50)</trace>
      <trace>org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:959)</trace>
      <trace>org.springframework.web.servlet.DispatcherServlet.doService(DispatcherServlet.java:893)</trace>
      <trace>org.springframework.web.servlet.FrameworkServlet.processRequest(FrameworkServlet.java:968)</trace>
      <trace>org.springframework.web.servlet.FrameworkServlet.doGet(FrameworkServlet.java:859)</trace>
      <trace>javax.servlet.http.HttpServlet.service(HttpServlet.java:621)</trace>
      <trace>org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:844)</trace>
      <trace>javax.servlet.http.HttpServlet.service(HttpServlet.java:722)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:305)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.geoserver.filters.ThreadLocalsCleanupFilter.doFilter(ThreadLocalsCleanupFilter.java:28)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:75)</trace>
      <trace>org.geoserver.wms.animate.AnimatorFilter.doFilter(AnimatorFilter.java:71)</trace>
      <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
      <trace>org.geoserver.monitor.MonitorFilter.doFilter(MonitorFilter.java:144)</trace>
      <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
      <trace>org.geoserver.gwc.web.blob.SqliteMultipartFilter.doFilterInternal(SqliteMultipartFilter.java:20)</trace>
      <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
      <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
      <trace>org.geoserver.flow.controller.IpBlacklistFilter.doFilter(IpBlacklistFilter.java:94)</trace>
      <trace>org.geoserver.filters.SpringDelegatingFilter$Chain.doFilter(SpringDelegatingFilter.java:71)</trace>
      <trace>org.geoserver.filters.SpringDelegatingFilter.doFilter(SpringDelegatingFilter.java:46)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.geoserver.platform.AdvancedDispatchFilter.doFilter(AdvancedDispatchFilter.java:50)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:316)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
      <trace>org.springframework.security.web.access.intercept.FilterSecurityInterceptor.invoke(FilterSecurityInterceptor.java:126)</trace>
      <trace>org.springframework.security.web.access.intercept.FilterSecurityInterceptor.doFilter(FilterSecurityInterceptor.java:90)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
      <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
      <trace>org.springframework.security.web.access.ExceptionTranslationFilter.doFilter(ExceptionTranslationFilter.java:114)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
      <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
      <trace>org.geoserver.security.filter.GeoServerAnonymousAuthenticationFilter.doFilter(GeoServerAnonymousAuthenticationFilter.java:54)</trace>
      <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
      <trace>org.springframework.security.web.authentication.www.BasicAuthenticationFilter.doFilterInternal(BasicAuthenticationFilter.java:158)</trace>
      <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
      <trace>org.geoserver.security.filter.GeoServerBasicAuthenticationFilter.doFilter(GeoServerBasicAuthenticationFilter.java:84)</trace>
      <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:69)</trace>
      <trace>org.springframework.security.web.context.SecurityContextPersistenceFilter.doFilter(SecurityContextPersistenceFilter.java:91)</trace>
      <trace>org.geoserver.security.filter.GeoServerSecurityContextPersistenceFilter$1.doFilter(GeoServerSecurityContextPersistenceFilter.java:53)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter$NestedFilterChain.doFilter(GeoServerCompositeFilter.java:73)</trace>
      <trace>org.geoserver.security.filter.GeoServerCompositeFilter.doFilter(GeoServerCompositeFilter.java:92)</trace>
      <trace>org.springframework.security.web.FilterChainProxy$VirtualFilterChain.doFilter(FilterChainProxy.java:330)</trace>
      <trace>org.springframework.security.web.FilterChainProxy.doFilterInternal(FilterChainProxy.java:213)</trace>
      <trace>org.springframework.security.web.FilterChainProxy.doFilter(FilterChainProxy.java:176)</trace>
      <trace>org.geoserver.security.GeoServerSecurityFilterChainProxy.doFilter(GeoServerSecurityFilterChainProxy.java:152)</trace>
      <trace>org.springframework.web.filter.DelegatingFilterProxy.invokeDelegate(DelegatingFilterProxy.java:346)</trace>
      <trace>org.springframework.web.filter.DelegatingFilterProxy.doFilter(DelegatingFilterProxy.java:262)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.geoserver.filters.LoggingFilter.doFilter(LoggingFilter.java:87)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.geoserver.filters.XFrameOptionsFilter.doFilter(XFrameOptionsFilter.java:89)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.geoserver.filters.GZIPFilter.doFilter(GZIPFilter.java:42)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.geoserver.filters.SessionDebugFilter.doFilter(SessionDebugFilter.java:48)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.geoserver.filters.FlushSafeFilter.doFilter(FlushSafeFilter.java:44)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.springframework.web.filter.CharacterEncodingFilter.doFilterInternal(CharacterEncodingFilter.java:121)</trace>
      <trace>org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:243)</trace>
      <trace>org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:210)</trace>
      <trace>org.apache.catalina.core.StandardWrapperValve.invoke(StandardWrapperValve.java:224)</trace>
      <trace>org.apache.catalina.core.StandardContextValve.invoke(StandardContextValve.java:169)</trace>
      <trace>org.apache.catalina.authenticator.AuthenticatorBase.invoke(AuthenticatorBase.java:472)</trace>
      <trace>org.apache.catalina.core.StandardHostValve.invoke(StandardHostValve.java:168)</trace>
      <trace>org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:98)</trace>
      <trace>org.apache.catalina.valves.AccessLogValve.invoke(AccessLogValve.java:927)</trace>
      <trace>org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:118)</trace>
      <trace>org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:407)</trace>
      <trace>org.apache.coyote.ajp.AjpProcessor.process(AjpProcessor.java:200)</trace>
      <trace>org.apache.coyote.AbstractProtocol$AbstractConnectionHandler.process(AbstractProtocol.java:579)</trace>
      <trace>org.apache.tomcat.util.net.JIoEndpoint$SocketProcessor.run(JIoEndpoint.java:307)</trace>
      <trace>java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)</trace>
      <trace>java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)</trace>
      <trace>java.lang.Thread.run(Thread.java:745)</trace>
    </stackTrace>
    <suppressedExceptions class="java.util.Collections$UnmodifiableRandomAccessList" reference="../cause/cause/suppressedExceptions"/>
    <code>internalError</code>
    <exceptionText/>
  </error>
  <responseStatus>200</responseStatus>
  <httpReferer>http://mapstore2.geo-solutions.it/mapstore/</httpReferer>
  <bbox class="org.geotools.geometry.jts.ReferencedEnvelope">
    <minx>-56.25000000000001</minx>
    <maxx>-45.00000000000001</maxx>
    <miny>11.178401873711772</miny>
    <maxy>21.94304553343817</maxy>
    <crs class="org.geotools.referencing.crs.DefaultGeographicCRS">
      <name class="org.geotools.referencing.NamedIdentifier">
        <code>WGS 84</code>
        <codespace>EPSG</codespace>
        <authority class="org.geotools.metadata.iso.citation.CitationImpl">
          <title class="org.geotools.util.SimpleInternationalString" serialization="custom">
            <unserializable-parents/>
            <org.geotools.util.SimpleInternationalString>
              <default/>
              <string>European Petroleum Survey Group</string>
            </org.geotools.util.SimpleInternationalString>
          </title>
          <alternateTitles class="org.geotools.resources.UnmodifiableArrayList">
            <array>
              <org.geotools.util.SimpleInternationalString serialization="custom">
                <unserializable-parents/>
                <org.geotools.util.SimpleInternationalString>
                  <default/>
                  <string>EPSG</string>
                </org.geotools.util.SimpleInternationalString>
              </org.geotools.util.SimpleInternationalString>
              <org.geotools.util.SimpleInternationalString serialization="custom">
                <unserializable-parents/>
                <org.geotools.util.SimpleInternationalString>
                  <default/>
                  <string>EPSG data base version 8.6 on HSQL Database Engine engine.</string>
                </org.geotools.util.SimpleInternationalString>
              </org.geotools.util.SimpleInternationalString>
            </array>
          </alternateTitles>
          <dates class="empty-set"/>
          <edition class="org.geotools.util.SimpleInternationalString" serialization="custom">
            <unserializable-parents/>
            <org.geotools.util.SimpleInternationalString>
              <default/>
              <string>8.6</string>
            </org.geotools.util.SimpleInternationalString>
          </edition>
          <editionDate>1416524400000</editionDate>
          <identifiers class="org.geotools.resources.UnmodifiableArrayList">
            <array>
              <org.geotools.metadata.iso.IdentifierImpl>
                <code>EPSG</code>
              </org.geotools.metadata.iso.IdentifierImpl>
            </array>
          </identifiers>
          <citedResponsibleParties class="org.geotools.resources.UnmodifiableArrayList">
            <array>
              <org.geotools.metadata.iso.citation.ResponsiblePartyImpl>
                <organisationName class="org.geotools.util.SimpleInternationalString" reference="../../../../title"/>
                <contactInfo class="org.geotools.metadata.iso.citation.ContactImpl">
                  <onLineResource class="org.geotools.metadata.iso.citation.OnLineResourceImpl">
                    <function>
                      <name>INFORMATION</name>
                    </function>
                    <linkage>http://www.epsg.org</linkage>
                  </onLineResource>
                </contactInfo>
                <role>
                  <name>PRINCIPAL_INVESTIGATOR</name>
                </role>
              </org.geotools.metadata.iso.citation.ResponsiblePartyImpl>
            </array>
          </citedResponsibleParties>
          <presentationForm class="org.geotools.resources.UnmodifiableArrayList">
            <array>
              <org.opengis.metadata.citation.PresentationForm>
                <name>TABLE_DIGITAL</name>
              </org.opengis.metadata.citation.PresentationForm>
            </array>
          </presentationForm>
        </authority>
        <name class="org.geotools.util.ScopedName">
          <scope class="org.geotools.util.LocalName">
            <name class="string">EPSG</name>
          </scope>
          <separator>:</separator>
          <name class="org.geotools.util.LocalName">
            <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
            <name class="string">WGS 84</name>
          </name>
        </name>
      </name>
      <identifiers class="singleton-set">
        <org.geotools.referencing.NamedIdentifier>
          <code>4326</code>
          <codespace>EPSG</codespace>
          <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../name/authority"/>
          <version>8.6</version>
          <name class="org.geotools.util.ScopedName">
            <scope class="org.geotools.util.LocalName" reference="../../../../name/name/scope"/>
            <separator>:</separator>
            <name class="org.geotools.util.LocalName">
              <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
              <name class="string">4326</name>
            </name>
          </name>
        </org.geotools.referencing.NamedIdentifier>
      </identifiers>
      <domainOfValidity class="org.geotools.metadata.iso.extent.ExtentImpl">
        <description class="org.geotools.util.SimpleInternationalString" serialization="custom">
          <unserializable-parents/>
          <org.geotools.util.SimpleInternationalString>
            <default/>
            <string>World.</string>
          </org.geotools.util.SimpleInternationalString>
        </description>
        <geographicElements class="org.geotools.resources.UnmodifiableArrayList">
          <array>
            <org.geotools.metadata.iso.extent.GeographicBoundingBoxImpl>
              <inclusion>true</inclusion>
              <westBoundLongitude>-180.0</westBoundLongitude>
              <eastBoundLongitude>180.0</eastBoundLongitude>
              <southBoundLatitude>-90.0</southBoundLatitude>
              <northBoundLatitude>90.0</northBoundLatitude>
            </org.geotools.metadata.iso.extent.GeographicBoundingBoxImpl>
          </array>
        </geographicElements>
        <temporalElements class="empty-set"/>
        <verticalElements class="empty-set"/>
      </domainOfValidity>
      <scope class="org.geotools.util.GrowableInternationalString" serialization="custom">
        <unserializable-parents/>
        <org.geotools.util.GrowableInternationalString>
          <default>
            <localMap class="singleton-map">
              <entry>
                <null/>
                <string>Horizontal component of 3D system. Used by the GPS satellite navigation system and for NATO military geodetic surveying.</string>
              </entry>
            </localMap>
          </default>
        </org.geotools.util.GrowableInternationalString>
      </scope>
      <coordinateSystem class="org.geotools.referencing.cs.DefaultEllipsoidalCS">
        <name class="org.geotools.referencing.NamedIdentifier">
          <code>Ellipsoidal 2D CS. Axes: latitude, longitude. Orientations: north, east. UoM: degree</code>
          <codespace>EPSG</codespace>
          <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../name/authority"/>
          <name class="org.geotools.util.ScopedName">
            <scope class="org.geotools.util.LocalName" reference="../../../../name/name/scope"/>
            <separator>:</separator>
            <name class="org.geotools.util.LocalName">
              <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
              <name class="string">Ellipsoidal 2D CS. Axes: latitude, longitude. Orientations: north, east. UoM: degree</name>
            </name>
          </name>
        </name>
        <alias class="singleton-set">
          <org.geotools.util.ScopedName>
            <scope class="org.geotools.util.LocalName">
              <name class="string">EPSG abbreviation</name>
            </scope>
            <separator>:</separator>
            <name class="org.geotools.util.LocalName">
              <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
              <name class="string">NAD83(2011) / CA 4 ftUS</name>
            </name>
          </org.geotools.util.ScopedName>
        </alias>
        <identifiers class="singleton-set">
          <org.geotools.referencing.NamedIdentifier>
            <code>6422</code>
            <codespace>EPSG</codespace>
            <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../name/authority"/>
            <version>8.6</version>
          </org.geotools.referencing.NamedIdentifier>
        </identifiers>
        <remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
          <unserializable-parents/>
          <org.geotools.util.GrowableInternationalString>
            <default>
              <localMap class="singleton-map">
                <entry>
                  <null/>
                  <string>Coordinates referenced to this CS are in degrees. Any degree representation (e.g. DMSH, decimal, etc.) may be used but that used must be declared for the user by the supplier of data. Used in geographic 2D coordinate reference systems.</string>
                </entry>
              </localMap>
            </default>
          </org.geotools.util.GrowableInternationalString>
        </remarks>
        <axis>
          <org.geotools.referencing.cs.DefaultCoordinateSystemAxis>
            <name class="org.geotools.referencing.NamedIdentifier">
              <code>Geodetic longitude</code>
              <codespace>EPSG</codespace>
              <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../name/authority"/>
              <name class="org.geotools.util.ScopedName">
                <scope class="org.geotools.util.LocalName" reference="../../../../../../name/name/scope"/>
                <separator>:</separator>
                <name class="org.geotools.util.LocalName">
                  <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                  <name class="string">Geodetic longitude</name>
                </name>
              </name>
            </name>
            <identifiers class="singleton-set">
              <org.geotools.referencing.NamedIdentifier>
                <code>107</code>
                <codespace>EPSG</codespace>
                <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../../name/authority"/>
                <version>8.6</version>
              </org.geotools.referencing.NamedIdentifier>
            </identifiers>
            <remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
              <unserializable-parents/>
              <org.geotools.util.GrowableInternationalString>
                <default>
                  <localMap class="singleton-map">
                    <entry>
                      <null/>
                      <string>Angle from the prime meridian plane to the meridian plane passing through the given point, eastwards usually treated as positive.
Used in geographic 2D and geographic 3D coordinate reference systems.</string>
                    </entry>
                  </localMap>
                </default>
              </org.geotools.util.GrowableInternationalString>
            </remarks>
            <abbreviation>Long</abbreviation>
            <direction>
              <name>EAST</name>
            </direction>
            <unit class="javax.measure.unit.TransformedUnit">
              <__parentUnit class="javax.measure.unit.AlternateUnit">
                <__symbol>rad</__symbol>
                <__parent class="javax.measure.unit.ProductUnit">
                  <__elements/>
                  <__hashCode>0</__hashCode>
                </__parent>
              </__parentUnit>
              <__toParentUnit class="javax.measure.converter.MultiplyConverter">
                <__factor>0.017453292519943295</__factor>
              </__toParentUnit>
            </unit>
            <minimum>-180.0</minimum>
            <maximum>180.0</maximum>
            <rangeMeaning>
              <name>WRAPAROUND</name>
            </rangeMeaning>
          </org.geotools.referencing.cs.DefaultCoordinateSystemAxis>
          <org.geotools.referencing.cs.DefaultCoordinateSystemAxis>
            <name class="org.geotools.referencing.NamedIdentifier">
              <code>Geodetic latitude</code>
              <codespace>EPSG</codespace>
              <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../name/authority"/>
              <name class="org.geotools.util.ScopedName">
                <scope class="org.geotools.util.LocalName" reference="../../../../../../name/name/scope"/>
                <separator>:</separator>
                <name class="org.geotools.util.LocalName">
                  <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                  <name class="string">Geodetic latitude</name>
                </name>
              </name>
            </name>
            <identifiers class="singleton-set">
              <org.geotools.referencing.NamedIdentifier>
                <code>106</code>
                <codespace>EPSG</codespace>
                <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../../name/authority"/>
                <version>8.6</version>
              </org.geotools.referencing.NamedIdentifier>
            </identifiers>
            <remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
              <unserializable-parents/>
              <org.geotools.util.GrowableInternationalString>
                <default>
                  <localMap class="singleton-map">
                    <entry>
                      <null/>
                      <string>Angle from the equatorial plane to the perpendicular to the ellipsoid through a given point, northwards usually treated as positive.
Used in geographic 2D and geographic 3D coordinate reference systems.</string>
                    </entry>
                  </localMap>
                </default>
              </org.geotools.util.GrowableInternationalString>
            </remarks>
            <abbreviation>Lat</abbreviation>
            <direction>
              <name>NORTH</name>
            </direction>
            <unit class="javax.measure.unit.TransformedUnit" reference="../../org.geotools.referencing.cs.DefaultCoordinateSystemAxis/unit"/>
            <minimum>-90.0</minimum>
            <maximum>90.0</maximum>
            <rangeMeaning>
              <name>EXACT</name>
            </rangeMeaning>
          </org.geotools.referencing.cs.DefaultCoordinateSystemAxis>
        </axis>
      </coordinateSystem>
      <datum class="org.geotools.referencing.datum.DefaultGeodeticDatum">
        <name class="org.geotools.referencing.NamedIdentifier">
          <code>World Geodetic System 1984</code>
          <codespace>EPSG</codespace>
          <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../name/authority"/>
          <name class="org.geotools.util.ScopedName">
            <scope class="org.geotools.util.LocalName" reference="../../../../name/name/scope"/>
            <separator>:</separator>
            <name class="org.geotools.util.LocalName">
              <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
              <name class="string">World Geodetic System 1984</name>
            </name>
          </name>
        </name>
        <alias class="java.util.Collections$UnmodifiableSet">
          <c class="linked-hash-set">
            <org.geotools.util.ScopedName>
              <scope class="org.geotools.util.LocalName" reference="../../../../../coordinateSystem/alias/org.geotools.util.ScopedName/scope"/>
              <separator>:</separator>
              <name class="org.geotools.util.LocalName">
                <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                <name class="string">WGS 84</name>
              </name>
            </org.geotools.util.ScopedName>
            <org.geotools.util.ScopedName>
              <scope class="org.geotools.util.LocalName">
                <name class="string">EPSG</name>
              </scope>
              <separator>:</separator>
              <name class="org.geotools.util.LocalName">
                <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                <name class="string">World Geodetic System 1984</name>
              </name>
            </org.geotools.util.ScopedName>
            <org.geotools.util.ScopedName>
              <scope class="org.geotools.util.LocalName">
                <name class="string">OGR</name>
              </scope>
              <separator>:</separator>
              <name class="org.geotools.util.LocalName">
                <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                <name class="string">World_Geodetic_System_1984</name>
              </name>
            </org.geotools.util.ScopedName>
            <org.geotools.util.ScopedName>
              <scope class="org.geotools.util.LocalName">
                <name class="string">ESRI</name>
              </scope>
              <separator>:</separator>
              <name class="org.geotools.util.LocalName">
                <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                <name class="string">D_WGS_1984</name>
              </name>
            </org.geotools.util.ScopedName>
            <org.geotools.util.ScopedName>
              <scope class="org.geotools.util.LocalName">
                <name class="string">Oracle</name>
              </scope>
              <separator>:</separator>
              <name class="org.geotools.util.LocalName">
                <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                <name class="string">WGS 84</name>
              </name>
            </org.geotools.util.ScopedName>
            <org.geotools.util.ScopedName>
              <scope class="org.geotools.util.LocalName">
                <name class="string">OGC</name>
              </scope>
              <separator>:</separator>
              <name class="org.geotools.util.LocalName">
                <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                <name class="string">WGS84</name>
              </name>
            </org.geotools.util.ScopedName>
            <org.geotools.util.LocalName>
              <name class="string">WGS_84</name>
            </org.geotools.util.LocalName>
            <org.geotools.util.LocalName>
              <name class="string">WGS_1984</name>
            </org.geotools.util.LocalName>
          </c>
        </alias>
        <identifiers class="singleton-set">
          <org.geotools.referencing.NamedIdentifier>
            <code>6326</code>
            <codespace>EPSG</codespace>
            <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../name/authority"/>
            <version>8.6</version>
          </org.geotools.referencing.NamedIdentifier>
        </identifiers>
        <remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
          <unserializable-parents/>
          <org.geotools.util.GrowableInternationalString>
            <default>
              <localMap class="singleton-map">
                <entry>
                  <null/>
                  <string>EPSG::6326 has been the then current realisation. No distinction is made between the original and subsequent (G730, G873, G1150, G1674 and G1762) WGS 84 frames. Since 1997, WGS 84 has been maintained within 10cm of the then current ITRF.</string>
                </entry>
              </localMap>
            </default>
          </org.geotools.util.GrowableInternationalString>
        </remarks>
        <anchorPoint class="org.geotools.util.GrowableInternationalString" serialization="custom">
          <unserializable-parents/>
          <org.geotools.util.GrowableInternationalString>
            <default>
              <localMap class="singleton-map">
                <entry>
                  <null/>
                  <string>Defined through a consistent set of station coordinates. These have changed with time: by 0.7m on 1994-06-29 (G730), a further 0.2m on 1997-01-29 (G873),  0.06m on 2002-01-20 (G1150), 0.2m on 2012-02-08 (G1674) and 0.02m on 2013-10-16 (G1762).</string>
                </entry>
              </localMap>
            </default>
          </org.geotools.util.GrowableInternationalString>
        </anchorPoint>
        <realizationEpoch>-9223372036854775808</realizationEpoch>
        <domainOfValidity class="org.geotools.metadata.iso.extent.ExtentImpl" reference="../../domainOfValidity"/>
        <scope class="org.geotools.util.GrowableInternationalString" serialization="custom">
          <unserializable-parents/>
          <org.geotools.util.GrowableInternationalString>
            <default>
              <localMap class="singleton-map">
                <entry>
                  <null/>
                  <string>Satellite navigation.</string>
                </entry>
              </localMap>
            </default>
          </org.geotools.util.GrowableInternationalString>
        </scope>
        <ellipsoid class="org.geotools.referencing.datum.DefaultEllipsoid">
          <name class="org.geotools.referencing.NamedIdentifier">
            <code>WGS 84</code>
            <codespace>EPSG</codespace>
            <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../name/authority"/>
            <name class="org.geotools.util.ScopedName">
              <scope class="org.geotools.util.LocalName" reference="../../../../../name/name/scope"/>
              <separator>:</separator>
              <name class="org.geotools.util.LocalName">
                <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                <name class="string">WGS 84</name>
              </name>
            </name>
          </name>
          <alias class="java.util.Collections$UnmodifiableSet">
            <c class="linked-hash-set">
              <org.geotools.util.ScopedName>
                <scope class="org.geotools.util.LocalName">
                  <name class="string">EPSG alias</name>
                </scope>
                <separator>:</separator>
                <name class="org.geotools.util.LocalName">
                  <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                  <name class="string">WGS84</name>
                </name>
              </org.geotools.util.ScopedName>
              <org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[2]"/>
              <org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[3]"/>
              <org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[4]"/>
              <org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[5]"/>
              <org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[6]"/>
              <org.geotools.util.LocalName reference="../../../../alias/c/org.geotools.util.LocalName"/>
              <org.geotools.util.LocalName reference="../../../../alias/c/org.geotools.util.LocalName[2]"/>
            </c>
          </alias>
          <identifiers class="singleton-set">
            <org.geotools.referencing.NamedIdentifier>
              <code>7030</code>
              <codespace>EPSG</codespace>
              <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../name/authority"/>
              <version>8.6</version>
            </org.geotools.referencing.NamedIdentifier>
          </identifiers>
          <remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
            <unserializable-parents/>
            <org.geotools.util.GrowableInternationalString>
              <default>
                <localMap class="singleton-map">
                  <entry>
                    <null/>
                    <string>Inverse flattening derived from four defining parameters (semi-major axis; C20 = -484.16685*10e-6; earth&apos;s angular velocity w = 7292115e11 rad/sec; gravitational constant GM = 3986005e8 m*m*m/s/s).</string>
                  </entry>
                </localMap>
              </default>
            </org.geotools.util.GrowableInternationalString>
          </remarks>
          <semiMajorAxis>6378137.0</semiMajorAxis>
          <semiMinorAxis>6356752.314245179</semiMinorAxis>
          <inverseFlattening>298.257223563</inverseFlattening>
          <ivfDefinitive>true</ivfDefinitive>
          <unit class="javax.measure.unit.BaseUnit">
            <__symbol>m</__symbol>
          </unit>
        </ellipsoid>
        <primeMeridian class="org.geotools.referencing.datum.DefaultPrimeMeridian">
          <name class="org.geotools.referencing.NamedIdentifier">
            <code>Greenwich</code>
            <codespace>EPSG</codespace>
            <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../name/authority"/>
            <name class="org.geotools.util.ScopedName">
              <scope class="org.geotools.util.LocalName" reference="../../../../../name/name/scope"/>
              <separator>:</separator>
              <name class="org.geotools.util.LocalName">
                <asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
                <name class="string">Greenwich</name>
              </name>
            </name>
          </name>
          <identifiers class="singleton-set">
            <org.geotools.referencing.NamedIdentifier>
              <code>8901</code>
              <codespace>EPSG</codespace>
              <authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../name/authority"/>
              <version>8.6</version>
            </org.geotools.referencing.NamedIdentifier>
          </identifiers>
          <greenwichLongitude>0.0</greenwichLongitude>
          <angularUnit class="javax.measure.unit.TransformedUnit" reference="../../../coordinateSystem/axis/org.geotools.referencing.cs.DefaultCoordinateSystemAxis/unit"/>
        </primeMeridian>
      </datum>
    </crs>
  </bbox>
</org.geoserver.monitor.RequestData>"""

req_xml = """<org.geoserver.monitor.RequestData>
<internalid>12681</internalid>
<id>12681</id>
<status>FINISHED</status>
<category>OWS</category>
<path>/wms</path>
<queryString>
<![CDATA[SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=nurc:Arc_Sample&STYLES=&FORMAT=image/png&TRANSPARENT=true&HEIGHT=256&WIDTH=256&TILED=true&ZINDEX=9&SRS=EPSG:3857&CRS=EPSG:3857&BBOX=-5009377.085697311,10018754.171394618,0,15028131.257091932]]>
</queryString>
<body/>
<bodyContentLength>0</bodyContentLength>
<httpMethod>GET</httpMethod>
<startTime>2017-05-30 16:04:00.719 UTC</startTime>
<endTime>2017-05-30 16:04:00.809 UTC</endTime>
<totalTime>90</totalTime>
<remoteAddr>201.195.233.98</remoteAddr>
<remoteHost>201.195.233.98</remoteHost>
<remoteUser>anonymous</remoteUser>
<remoteUserAgent>
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393
</remoteUserAgent>
<remoteLat>0.0</remoteLat>
<remoteLon>0.0</remoteLon>
<host>demo.geo-solutions.it</host>
<internalHost>ks390295.kimsufi.com</internalHost>
<service>WMS</service>
<operation>GetMap</operation>
<owsVersion>1.3.0</owsVersion>
<resources>
<string>nurc:Arc_Sample</string>
</resources>
<responseLength>3622</responseLength>
<responseContentType>image/png</responseContentType>
<responseStatus>200</responseStatus>
<httpReferer>
http://dev.mapstore2.geo-solutions.it/mapstore/examples/api/?map=Prueba
</httpReferer>
<bbox class="org.geotools.geometry.jts.ReferencedEnvelope">
<minx>-45.00000000000001</minx>
<maxx>0.0</maxx>
<miny>66.51326044311185</miny>
<maxy>79.17133464081945</maxy>
<crs class="org.geotools.referencing.crs.DefaultGeographicCRS">
<name class="org.geotools.referencing.NamedIdentifier">
<code>WGS 84</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl">
<title class="org.geotools.util.SimpleInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.SimpleInternationalString>
<default/>
<string>European Petroleum Survey Group</string>
</org.geotools.util.SimpleInternationalString>
</title>
<alternateTitles class="org.geotools.resources.UnmodifiableArrayList">
<array>
<org.geotools.util.SimpleInternationalString serialization="custom">
<unserializable-parents/>
<org.geotools.util.SimpleInternationalString>
<default/>
<string>EPSG</string>
</org.geotools.util.SimpleInternationalString>
</org.geotools.util.SimpleInternationalString>
<org.geotools.util.SimpleInternationalString serialization="custom">
<unserializable-parents/>
<org.geotools.util.SimpleInternationalString>
<default/>
<string>
EPSG data base version 8.6 on HSQL Database Engine engine.
</string>
</org.geotools.util.SimpleInternationalString>
</org.geotools.util.SimpleInternationalString>
</array>
</alternateTitles>
<dates class="empty-set"/>
<edition class="org.geotools.util.SimpleInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.SimpleInternationalString>
<default/>
<string>8.6</string>
</org.geotools.util.SimpleInternationalString>
</edition>
<editionDate>1416524400000</editionDate>
<identifiers class="org.geotools.resources.UnmodifiableArrayList">
<array>
<org.geotools.metadata.iso.IdentifierImpl>
<code>EPSG</code>
</org.geotools.metadata.iso.IdentifierImpl>
</array>
</identifiers>
<citedResponsibleParties class="org.geotools.resources.UnmodifiableArrayList">
<array>
<org.geotools.metadata.iso.citation.ResponsiblePartyImpl>
<organisationName class="org.geotools.util.SimpleInternationalString" reference="../../../../title"/>
<contactInfo class="org.geotools.metadata.iso.citation.ContactImpl">
<onLineResource class="org.geotools.metadata.iso.citation.OnLineResourceImpl">
<function>
<name>INFORMATION</name>
</function>
<linkage>http://www.epsg.org</linkage>
</onLineResource>
</contactInfo>
<role>
<name>PRINCIPAL_INVESTIGATOR</name>
</role>
</org.geotools.metadata.iso.citation.ResponsiblePartyImpl>
</array>
</citedResponsibleParties>
<presentationForm class="org.geotools.resources.UnmodifiableArrayList">
<array>
<org.opengis.metadata.citation.PresentationForm>
<name>TABLE_DIGITAL</name>
</org.opengis.metadata.citation.PresentationForm>
</array>
</presentationForm>
</authority>
<name class="org.geotools.util.ScopedName">
<scope class="org.geotools.util.LocalName">
<name class="string">EPSG</name>
</scope>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">WGS 84</name>
</name>
</name>
</name>
<identifiers class="singleton-set">
<org.geotools.referencing.NamedIdentifier>
<code>4326</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../name/authority"/>
<version>8.6</version>
<name class="org.geotools.util.ScopedName">
<scope class="org.geotools.util.LocalName" reference="../../../../name/name/scope"/>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">4326</name>
</name>
</name>
</org.geotools.referencing.NamedIdentifier>
</identifiers>
<domainOfValidity class="org.geotools.metadata.iso.extent.ExtentImpl">
<description class="org.geotools.util.SimpleInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.SimpleInternationalString>
<default/>
<string>World.</string>
</org.geotools.util.SimpleInternationalString>
</description>
<geographicElements class="org.geotools.resources.UnmodifiableArrayList">
<array>
<org.geotools.metadata.iso.extent.GeographicBoundingBoxImpl>
<inclusion>true</inclusion>
<westBoundLongitude>-180.0</westBoundLongitude>
<eastBoundLongitude>180.0</eastBoundLongitude>
<southBoundLatitude>-90.0</southBoundLatitude>
<northBoundLatitude>90.0</northBoundLatitude>
</org.geotools.metadata.iso.extent.GeographicBoundingBoxImpl>
</array>
</geographicElements>
<temporalElements class="empty-set"/>
<verticalElements class="empty-set"/>
</domainOfValidity>
<scope class="org.geotools.util.GrowableInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.GrowableInternationalString>
<default>
<localMap class="singleton-map">
<entry>
<null/>
<string>
Horizontal component of 3D system. Used by the GPS satellite navigation system and for NATO military geodetic surveying.
</string>
</entry>
</localMap>
</default>
</org.geotools.util.GrowableInternationalString>
</scope>
<coordinateSystem class="org.geotools.referencing.cs.DefaultEllipsoidalCS">
<name class="org.geotools.referencing.NamedIdentifier">
<code>
Ellipsoidal 2D CS. Axes: latitude, longitude. Orientations: north, east. UoM: degree
</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../name/authority"/>
<name class="org.geotools.util.ScopedName">
<scope class="org.geotools.util.LocalName" reference="../../../../name/name/scope"/>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">
Ellipsoidal 2D CS. Axes: latitude, longitude. Orientations: north, east. UoM: degree
</name>
</name>
</name>
</name>
<alias class="singleton-set">
<org.geotools.util.ScopedName>
<scope class="org.geotools.util.LocalName">
<name class="string">EPSG abbreviation</name>
</scope>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">NAD83(2011) / CA 4 ftUS</name>
</name>
</org.geotools.util.ScopedName>
</alias>
<identifiers class="singleton-set">
<org.geotools.referencing.NamedIdentifier>
<code>6422</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../name/authority"/>
<version>8.6</version>
</org.geotools.referencing.NamedIdentifier>
</identifiers>
<remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.GrowableInternationalString>
<default>
<localMap class="singleton-map">
<entry>
<null/>
<string>
Coordinates referenced to this CS are in degrees. Any degree representation (e.g. DMSH, decimal, etc.) may be used but that used must be declared for the user by the supplier of data. Used in geographic 2D coordinate reference systems.
</string>
</entry>
</localMap>
</default>
</org.geotools.util.GrowableInternationalString>
</remarks>
<axis>
<org.geotools.referencing.cs.DefaultCoordinateSystemAxis>
<name class="org.geotools.referencing.NamedIdentifier">
<code>Geodetic longitude</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../name/authority"/>
<name class="org.geotools.util.ScopedName">
<scope class="org.geotools.util.LocalName" reference="../../../../../../name/name/scope"/>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">Geodetic longitude</name>
</name>
</name>
</name>
<identifiers class="singleton-set">
<org.geotools.referencing.NamedIdentifier>
<code>107</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../../name/authority"/>
<version>8.6</version>
</org.geotools.referencing.NamedIdentifier>
</identifiers>
<remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.GrowableInternationalString>
<default>
<localMap class="singleton-map">
<entry>
<null/>
<string>
Angle from the prime meridian plane to the meridian plane passing through the given point, eastwards usually treated as positive. Used in geographic 2D and geographic 3D coordinate reference systems.
</string>
</entry>
</localMap>
</default>
</org.geotools.util.GrowableInternationalString>
</remarks>
<abbreviation>Long</abbreviation>
<direction>
<name>EAST</name>
</direction>
<unit class="javax.measure.unit.TransformedUnit">
<__parentUnit class="javax.measure.unit.AlternateUnit">
<__symbol>rad</__symbol>
<__parent class="javax.measure.unit.ProductUnit">
<__elements/>
<__hashCode>0</__hashCode>
</__parent>
</__parentUnit>
<__toParentUnit class="javax.measure.converter.MultiplyConverter">
<__factor>0.017453292519943295</__factor>
</__toParentUnit>
</unit>
<minimum>-180.0</minimum>
<maximum>180.0</maximum>
<rangeMeaning>
<name>WRAPAROUND</name>
</rangeMeaning>
</org.geotools.referencing.cs.DefaultCoordinateSystemAxis>
<org.geotools.referencing.cs.DefaultCoordinateSystemAxis>
<name class="org.geotools.referencing.NamedIdentifier">
<code>Geodetic latitude</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../name/authority"/>
<name class="org.geotools.util.ScopedName">
<scope class="org.geotools.util.LocalName" reference="../../../../../../name/name/scope"/>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">Geodetic latitude</name>
</name>
</name>
</name>
<identifiers class="singleton-set">
<org.geotools.referencing.NamedIdentifier>
<code>106</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../../name/authority"/>
<version>8.6</version>
</org.geotools.referencing.NamedIdentifier>
</identifiers>
<remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.GrowableInternationalString>
<default>
<localMap class="singleton-map">
<entry>
<null/>
<string>
Angle from the equatorial plane to the perpendicular to the ellipsoid through a given point, northwards usually treated as positive. Used in geographic 2D and geographic 3D coordinate reference systems.
</string>
</entry>
</localMap>
</default>
</org.geotools.util.GrowableInternationalString>
</remarks>
<abbreviation>Lat</abbreviation>
<direction>
<name>NORTH</name>
</direction>
<unit class="javax.measure.unit.TransformedUnit" reference="../../org.geotools.referencing.cs.DefaultCoordinateSystemAxis/unit"/>
<minimum>-90.0</minimum>
<maximum>90.0</maximum>
<rangeMeaning>
<name>EXACT</name>
</rangeMeaning>
</org.geotools.referencing.cs.DefaultCoordinateSystemAxis>
</axis>
</coordinateSystem>
<datum class="org.geotools.referencing.datum.DefaultGeodeticDatum">
<name class="org.geotools.referencing.NamedIdentifier">
<code>World Geodetic System 1984</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../name/authority"/>
<name class="org.geotools.util.ScopedName">
<scope class="org.geotools.util.LocalName" reference="../../../../name/name/scope"/>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">World Geodetic System 1984</name>
</name>
</name>
</name>
<alias class="java.util.Collections$UnmodifiableSet">
<c class="linked-hash-set">
<org.geotools.util.ScopedName>
<scope class="org.geotools.util.LocalName" reference="../../../../../coordinateSystem/alias/org.geotools.util.ScopedName/scope"/>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">WGS 84</name>
</name>
</org.geotools.util.ScopedName>
<org.geotools.util.ScopedName>
<scope class="org.geotools.util.LocalName">
<name class="string">EPSG</name>
</scope>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">World Geodetic System 1984</name>
</name>
</org.geotools.util.ScopedName>
<org.geotools.util.ScopedName>
<scope class="org.geotools.util.LocalName">
<name class="string">OGR</name>
</scope>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">World_Geodetic_System_1984</name>
</name>
</org.geotools.util.ScopedName>
<org.geotools.util.ScopedName>
<scope class="org.geotools.util.LocalName">
<name class="string">ESRI</name>
</scope>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">D_WGS_1984</name>
</name>
</org.geotools.util.ScopedName>
<org.geotools.util.ScopedName>
<scope class="org.geotools.util.LocalName">
<name class="string">Oracle</name>
</scope>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">WGS 84</name>
</name>
</org.geotools.util.ScopedName>
<org.geotools.util.ScopedName>
<scope class="org.geotools.util.LocalName">
<name class="string">OGC</name>
</scope>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">WGS84</name>
</name>
</org.geotools.util.ScopedName>
<org.geotools.util.LocalName>
<name class="string">WGS_84</name>
</org.geotools.util.LocalName>
<org.geotools.util.LocalName>
<name class="string">WGS_1984</name>
</org.geotools.util.LocalName>
</c>
</alias>
<identifiers class="singleton-set">
<org.geotools.referencing.NamedIdentifier>
<code>6326</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../name/authority"/>
<version>8.6</version>
</org.geotools.referencing.NamedIdentifier>
</identifiers>
<remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.GrowableInternationalString>
<default>
<localMap class="singleton-map">
<entry>
<null/>
<string>
EPSG::6326 has been the then current realisation. No distinction is made between the original and subsequent (G730, G873, G1150, G1674 and G1762) WGS 84 frames. Since 1997, WGS 84 has been maintained within 10cm of the then current ITRF.
</string>
</entry>
</localMap>
</default>
</org.geotools.util.GrowableInternationalString>
</remarks>
<anchorPoint class="org.geotools.util.GrowableInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.GrowableInternationalString>
<default>
<localMap class="singleton-map">
<entry>
<null/>
<string>
Defined through a consistent set of station coordinates. These have changed with time: by 0.7m on 1994-06-29 (G730), a further 0.2m on 1997-01-29 (G873), 0.06m on 2002-01-20 (G1150), 0.2m on 2012-02-08 (G1674) and 0.02m on 2013-10-16 (G1762).
</string>
</entry>
</localMap>
</default>
</org.geotools.util.GrowableInternationalString>
</anchorPoint>
<realizationEpoch>-9223372036854775808</realizationEpoch>
<domainOfValidity class="org.geotools.metadata.iso.extent.ExtentImpl" reference="../../domainOfValidity"/>
<scope class="org.geotools.util.GrowableInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.GrowableInternationalString>
<default>
<localMap class="singleton-map">
<entry>
<null/>
<string>Satellite navigation.</string>
</entry>
</localMap>
</default>
</org.geotools.util.GrowableInternationalString>
</scope>
<ellipsoid class="org.geotools.referencing.datum.DefaultEllipsoid">
<name class="org.geotools.referencing.NamedIdentifier">
<code>WGS 84</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../name/authority"/>
<name class="org.geotools.util.ScopedName">
<scope class="org.geotools.util.LocalName" reference="../../../../../name/name/scope"/>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">WGS 84</name>
</name>
</name>
</name>
<alias class="java.util.Collections$UnmodifiableSet">
<c class="linked-hash-set">
<org.geotools.util.ScopedName>
<scope class="org.geotools.util.LocalName">
<name class="string">EPSG alias</name>
</scope>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">WGS84</name>
</name>
</org.geotools.util.ScopedName>
<org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[2]"/>
<org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[3]"/>
<org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[4]"/>
<org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[5]"/>
<org.geotools.util.ScopedName reference="../../../../alias/c/org.geotools.util.ScopedName[6]"/>
<org.geotools.util.LocalName reference="../../../../alias/c/org.geotools.util.LocalName"/>
<org.geotools.util.LocalName reference="../../../../alias/c/org.geotools.util.LocalName[2]"/>
</c>
</alias>
<identifiers class="singleton-set">
<org.geotools.referencing.NamedIdentifier>
<code>7030</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../name/authority"/>
<version>8.6</version>
</org.geotools.referencing.NamedIdentifier>
</identifiers>
<remarks class="org.geotools.util.GrowableInternationalString" serialization="custom">
<unserializable-parents/>
<org.geotools.util.GrowableInternationalString>
<default>
<localMap class="singleton-map">
<entry>
<null/>
<string>
Inverse flattening derived from four defining parameters (semi-major axis; C20 = -484.16685*10e-6; earth's angular velocity w = 7292115e11 rad/sec; gravitational constant GM = 3986005e8 m*m*m/s/s).
</string>
</entry>
</localMap>
</default>
</org.geotools.util.GrowableInternationalString>
</remarks>
<semiMajorAxis>6378137.0</semiMajorAxis>
<semiMinorAxis>6356752.314245179</semiMinorAxis>
<inverseFlattening>298.257223563</inverseFlattening>
<ivfDefinitive>true</ivfDefinitive>
<unit class="javax.measure.unit.BaseUnit">
<__symbol>m</__symbol>
</unit>
</ellipsoid>
<primeMeridian class="org.geotools.referencing.datum.DefaultPrimeMeridian">
<name class="org.geotools.referencing.NamedIdentifier">
<code>Greenwich</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../name/authority"/>
<name class="org.geotools.util.ScopedName">
<scope class="org.geotools.util.LocalName" reference="../../../../../name/name/scope"/>
<separator>:</separator>
<name class="org.geotools.util.LocalName">
<asScopedName class="org.geotools.util.ScopedName" reference="../.."/>
<name class="string">Greenwich</name>
</name>
</name>
</name>
<identifiers class="singleton-set">
<org.geotools.referencing.NamedIdentifier>
<code>8901</code>
<codespace>EPSG</codespace>
<authority class="org.geotools.metadata.iso.citation.CitationImpl" reference="../../../../../name/authority"/>
<version>8.6</version>
</org.geotools.referencing.NamedIdentifier>
</identifiers>
<greenwichLongitude>0.0</greenwichLongitude>
<angularUnit class="javax.measure.unit.TransformedUnit" reference="../../../coordinateSystem/axis/org.geotools.referencing.cs.DefaultCoordinateSystemAxis/unit"/>
</primeMeridian>
</datum>
</crs>
</bbox>
</org.geoserver.monitor.RequestData>"""

req_big = xmljson.yahoo.data(fromstring(req_xml))
req_err_big = xmljson.yahoo.data(fromstring(req_err_xml))


class RequestsTestCase(TestCase):

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        create_models('layer')
        self.user = 'admin'
        self.passwd = 'admin'
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.is_active = True
        self.u.email = 'test@email.com'
        self.u.set_password(self.passwd)
        self.u.save()
        self.ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.47 Safari/537.36"
        populate()

        self.host = Host.objects.create(name='localhost', ip='127.0.0.1')
        self.service_type = ServiceType.objects.get(name=ServiceType.TYPE_GEONODE)
        self.service = Service.objects.create(name=settings.MONITORING_SERVICE_NAME, host=self.host, service_type=self.service_type)

    def test_gs_req(self):
        """
        Test if we can parse geoserver requests
        """
        rq = RequestEvent.from_geoserver(self.service, req_big)
        self.assertTrue(rq)

    def test_gs_err_req(self):
        """
        Test if we can parse geoserver requests
        """
        rq = RequestEvent.from_geoserver(self.service, req_err_big)
        self.assertTrue(rq)
        q = ExceptionEvent.objects.filter(request=rq)
        self.assertEqual(q.count(), 1)
        self.assertEqual(q[0].error_type, 'org.geoserver.platform.ServiceException')

    def test_gn_request(self):
        """
        Test if we have geonode requests logged
        """
        l = Layer.objects.all().first()
        self.client.login(username=self.user, password=self.passwd)
        self.client.get(reverse('layer_detail', args=(l.alternate,)), **{"HTTP_USER_AGENT": self.ua})

        self.assertEqual(RequestEvent.objects.all().count(), 1)
        rq = RequestEvent.objects.get()
        self.assertTrue(rq.response_time > 0)
        self.assertEqual(list(rq.resources.all().values_list('name', 'type')), [(l.alternate, u'layer',)])
        self.assertEqual(rq.request_method, 'GET')

    def test_gn_error(self):
        """
        Test if we get geonode errors logged
        """
        Layer.objects.all().first()
        self.client.login(username=self.user, password=self.passwd)
        self.client.get(reverse('layer_detail', args=('nonex',)), **{"HTTP_USER_AGENT": self.ua})

        RequestEvent.objects.get()
        self.assertEqual(RequestEvent.objects.all().count(), 1)

        self.assertEqual(ExceptionEvent.objects.all().count(), 1)
        eq = ExceptionEvent.objects.get()
        self.assertEqual('django.http.response.Http404', eq.error_type)

    def test_service_handlers(self):
        """
        Test if we can calculate metrics
        """
        self.client.login(username=self.user, password=self.passwd)
        for idx, l in enumerate(Layer.objects.all()):
            for inum in range(0, idx+1):
                self.client.get(reverse('layer_detail', args=(l.alternate,)), **{"HTTP_USER_AGENT": self.ua})
        requests = RequestEvent.objects.all()

        c = CollectorAPI()
        q = requests.order_by('created')
        c.process_requests(self.service, requests, q.last().created, q.first().created)
        interval = self.service.check_interval
        now = datetime.now()

        valid_from = now - (2*interval)
        valid_to = now

        self.assertTrue(isinstance(valid_from, datetime))
        self.assertTrue(isinstance(valid_to, datetime))
        self.assertTrue(isinstance(interval, timedelta))

        metrics = c.get_metrics_for(metric_name='request.ip',
                                    valid_from=valid_from,
                                    valid_to=valid_to,
                                    interval=interval)

        self.assertIsNotNone(metrics)


class MonitoringUtilsTestCase(TestCase):

    def test_time_periods(self):
        """
        Test if we can use time periods
        """
        start = datetime(year=2017, month=06, day=20, hour=12, minute=22, second=50) #2017-06-20 12:22:50
        start_aligned = datetime(year=2017, month=06, day=20, hour=12, minute=20, second=0) #2017-06-20 12:20:00

        interval = timedelta(minutes=5)
        # 12:22:50+ 0:05:20 = 12:27:02
        end = start + timedelta(minutes=5, seconds=22)

        expected_periods = [(start_aligned, start_aligned + interval,),
                            (start_aligned + interval, start_aligned + (2*interval),),
                            ]

        aligned = align_period_start(start, interval)
        self.assertEqual(start_aligned, aligned)

        periods = list(generate_periods(start, interval, end))
        self.assertEqual(expected_periods, periods)



        pnow = datetime.now()

        start_for_one = pnow - interval
        periods = list(generate_periods(start_for_one, interval, pnow))
        self.assertEqual(len(periods), 1)

        start_for_two = pnow - (2 * interval)
        periods = list(generate_periods(start_for_two, interval, pnow))
        self.assertEqual(len(periods), 2)

        start_for_three = pnow - (3 * interval)
        periods = list(generate_periods(start_for_three, interval, pnow))
        self.assertEqual(len(periods), 3)
        
        start_for_two_and_half = pnow - timedelta(seconds=(2.5 * interval.total_seconds()))
        periods = list(generate_periods(start_for_two_and_half, interval, pnow))
        self.assertEqual(len(periods), 3)


class MonitoringChecksTestCase(TestCase):

    reserved_fields = ('emails', 'severity', 'active', 'grace_period',)

    def setUp(self):
        super(MonitoringChecksTestCase, self).setUp()
        populate()
        self.host = Host.objects.create(name='localhost', ip='127.0.0.1')
        self.service_type = ServiceType.objects.get(name=ServiceType.TYPE_GEONODE)
        self.service = Service.objects.create(name=settings.MONITORING_SERVICE_NAME, host=self.host, service_type=self.service_type)
        self.metric = Metric.objects.get(name='request.count')
        self.user = 'admin'
        self.passwd = 'admin'
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.is_active = True
        self.u.email = 'test@email.com'
        self.u.set_password(self.passwd)
        self.u.save()
        self.user2 = 'test'
        self.passwd2 = 'test'
        self.u2, _ = get_user_model().objects.get_or_create(username=self.user2)
        self.u2.is_active = True
        self.u2.email = 'test2@email.com'
        self.u2.set_password(self.passwd2)
        self.u2.save()




    def test_monitoring_checks(self):
        start = datetime.now()
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval


        #sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        ows_service = OWSService.objects.get(name='WFS')
        resource, _= MonitoredResource.objects.get_or_create(type='layer', name='test:test')
        resource2, _= MonitoredResource.objects.get_or_create(type='layer', name='test:test2')

        label, _ = MetricLabel.objects.get_or_create(name='discount')
        m = MetricValue.add(self.metric, start_aligned, end_aligned, self.service, label="Count", value_raw=10, value_num=10, value=10)
        
        uthreshold = [(self.metric.name, 'min_value', False, False, False, False, 0, 100, None, "Min number of request"),
                      (self.metric.name, 'max_value', False, False, False, False, 1000, None, None, "Max number of request"),
                      ]
        notification_data = {'name': 'check requests name',
                             'description': 'check requests description',
                             'severity': 'warning',
                             'user_threshold': uthreshold}
        
        nc = NotificationCheck.create(**notification_data)
        
        mc = MetricNotificationCheck.objects.create(notification_check=nc,
                                                    service=self.service,
                                                    metric=self.metric,
                                                    min_value=None,
                                                    definition=nc.definitions.first(),
                                                    max_value=None,
                                                    max_timeout=None)
        with self.assertRaises(ValueError):
            mc.check_metric(for_timestamp=start)

        mc.min_value = 11
        mc.save()

        with self.assertRaises(mc.MetricValueError):
            mc.check_metric(for_timestamp=start)

        mc.min_value = 1
        mc.max_value = 11
        mc.save()

        self.assertTrue(mc.check_metric(for_timestamp=start))

        m = MetricValue.add(self.metric, start_aligned, end_aligned, self.service, label="discount", value_raw=10, value_num=10, value=10, ows_service=ows_service)

        mc.min_value = 11
        mc.max_value = None
        mc.ows_service=ows_service
        mc.save()

        
        with self.assertRaises(mc.MetricValueError):
            mc.check_metric(for_timestamp=start)

        m = MetricValue.add(self.metric, start_aligned, end_aligned, self.service, label="discount", value_raw=10, value_num=10, value=10, resource=resource)
        
        mc.min_value = 1
        mc.max_value = 10
        mc.ows_service = None
        mc.resource = resource
        mc.save()
        
        
        self.assertTrue(mc.check_metric(for_timestamp=start))

        MetricValue.objects.all().delete()

        m = MetricValue.add(self.metric, start_aligned, end_aligned, self.service, label="discount", value_raw=10, value_num=10, value=10, resource=resource2)
        # this should raise ValueError, because MetricValue won't match
        with self.assertRaises(ValueError):
            mc.check_metric(for_timestamp=start)

    def test_notifications_views(self):

        start = datetime.now()
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval


        #sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        ows_service = OWSService.objects.get(name='WFS')
        resource, _= MonitoredResource.objects.get_or_create(type='layer', name='test:test')
        resource2, _= MonitoredResource.objects.get_or_create(type='layer', name='test:test2')

        label, _ = MetricLabel.objects.get_or_create(name='discount')
        m = MetricValue.add(self.metric, start_aligned, end_aligned, self.service, label="Count", value_raw=10, value_num=10, value=10)
        nc = NotificationCheck.objects.create(name='check requests', description='check requests')

        mc = MetricNotificationCheck.objects.create(notification_check=nc,
                                                    service=self.service,
                                                    metric=self.metric,
                                                    min_value=10,
                                                    max_value=200,
                                                    resource=resource,
                                                    max_timeout=None)

        c = self.client
        c.login(username=self.user, password=self.passwd)
        nresp = c.get(reverse('monitoring:api_user_notifications'))
        self.assertEqual(nresp.status_code, 200)
        data = json.loads(nresp.content)
        self.assertTrue(data['data'][0]['id'] == nc.id) 
        
        nresp = c.get(reverse('monitoring:api_user_notification_config', kwargs={'pk': nc.id}))
        self.assertEqual(nresp.status_code, 200)
        data = json.loads(nresp.content)
        self.assertTrue(data['data']['notification']['id'] == nc.id) 

        nresp = c.get(reverse('monitoring:api_user_notifications'))
        self.assertEqual(nresp.status_code, 200)
        data = json.loads(nresp.content)
        self.assertTrue(data['data'][0]['id'] == nc.id) 

        c.login(username=self.user2, password=self.passwd2)
        nresp = c.get(reverse('monitoring:api_user_notifications'))
        self.assertEqual(nresp.status_code, 200)
        data = json.loads(nresp.content)
        self.assertTrue(len(data['data']) == 1)


    def test_notifications_edit_views(self):

        start = datetime.now()
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval


        #sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        host = Host.objects.all().first()
        ows_service = OWSService.objects.get(name='WFS')
        resource, _= MonitoredResource.objects.get_or_create(type='layer', name='test:test')

        label, _ = MetricLabel.objects.get_or_create(name='discount')

        c = self.client
        c.login(username=self.user, password=self.passwd)
        notification_url = reverse('monitoring:api_user_notifications')
        uthreshold = [('request.count', 'min_value', False, False, False, False, 0, 100, None, "Min number of request"),
                      ('request.count', 'max_value', False, False, False, False, 1000, None, None, "Max number of request"),
                      ]
        notification_data = {'name': 'test',
                             'description': 'more test',
                             'severity': 'warning',
                             'user_threshold': json.dumps(uthreshold)}

        out = c.post(notification_url, notification_data)
        self.assertEqual(out.status_code, 200)

        jout = json.loads(out.content)
        nid = jout['data']['id']
        ndef = NotificationMetricDefinition.objects.filter(notification_check__id=nid)
        self.assertEqual(ndef.count(), 2)

        notification_url = reverse('monitoring:api_user_notification_config', kwargs={'pk': nid})
        notification = NotificationCheck.objects.get(pk=nid)
        notification_data = {'name': 'testttt',
                             'emails': [self.u.email, 'testother@test.com',],
                             'severity': 'error',
                             'description': 'more tesddddt'}
        form = notification.get_user_form()
        fields = {}

        for field in form.fields.values():
            if not hasattr(field, 'name'):
                continue
            fields[field.name] = int((field.min_value or 0) + 1)
        notification_data.update(fields)
        out = c.post(notification_url, notification_data)
        self.assertEqual(out.status_code, 200)
        jout = json.loads(out.content)
        n = NotificationCheck.objects.get()
        self.assertTrue(n.is_error)
        
        self.assertEqual(MetricNotificationCheck.objects.all().count(), 2)
        for nrow in jout['data']:
            nitem = MetricNotificationCheck.objects.get(id=nrow['id'])
            for nkey, nval in nrow.items():
                if not isinstance(nval, dict):
                    compare_to = getattr(nitem, nkey)
                    if isinstance(compare_to, Decimal):
                        nval = Decimal(nval)
                    self.assertEqual(compare_to, nval)



        out = c.post(notification_url, json.dumps(notification_data), content_type='application/json')
        self.assertEqual(out.status_code, 200)
        jout = json.loads(out.content)
        n = NotificationCheck.objects.get()
        self.assertTrue(n.is_error)
        
        self.assertEqual(MetricNotificationCheck.objects.all().count(), 2)
        for nrow in jout['data']:
            nitem = MetricNotificationCheck.objects.get(id=nrow['id'])
            for nkey, nval in nrow.items():
                if not isinstance(nval, dict):
                    compare_to = getattr(nitem, nkey)
                    if isinstance(compare_to, Decimal):
                        nval = Decimal(nval)
                    self.assertEqual(compare_to, nval)





    def test_notifications_api(self):
        
        capi = CollectorAPI()
        start = datetime.now()

        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval

        
        #for (metric_name, field_opt, use_service, 
        #     use_resource, use_label, use_ows_service, 
        #     minimum, maximum, thresholds,) in thresholds:

        notifications_config = ('geonode is not working',
                                'detects when requests are not handled',
                                (('request.count', 'min_value', False, False,
                                 False, False, 0, 10, None, 'Number of handled requests is lower than',),
                                ('response.time', 'max_value', False, False,
                                 False, False, 500, None, None, 'Response time is higher than',),))
        nc = NotificationCheck.create(*notifications_config)
        self.assertTrue(nc.definitions.all().count() == 2)
            
        user = self.u2
        pwd = self.passwd2

        self.client.login(username=user.username, password=pwd)
        for nc in NotificationCheck.objects.all():
            notifications_config_url = reverse('monitoring:api_user_notification_config', args=(nc.id,))
            nc_form = nc.get_user_form()
            self.assertTrue(nc_form)
            self.assertTrue(nc_form.fields.keys())
            vals = [1000000, 100000]
            data = {'emails': []} #self.u.email, 'testotherr@test.com',]}
            data['emails'] = '\n'.join(data['emails'])
            idx = 0
            for fname, field in nc_form.fields.items():
                if fname in self.reserved_fields:
                    continue
                data[fname] = vals[idx]
                idx += 1
            resp = self.client.post(notifications_config_url, data)

            self.assertEqual(resp.status_code, 400)
            
            vals = [7, 600]
            data = {'emails': '\n'.join([self.u.email, self.u2.email, 'testsome@test.com'])}
            idx = 0
            for fname, field in nc_form.fields.items():
                if fname in self.reserved_fields:
                    continue
                data[fname] = vals[idx]
                idx += 1
            #data['emails'] = '\n'.join(data['emails'])
            resp = self.client.post(notifications_config_url, data)
            nc.refresh_from_db()
            self.assertEqual(resp.status_code, 200, resp)

            _emails = data['emails'].split('\n')[-1:]
            _users = data['emails'].split('\n')[:-1]
            self.assertEqual(set([u.email for u in nc.get_users()]), set(_users))
            self.assertEqual(set([email for email in nc.get_emails()]), set(_emails))

        metric_rq_count = Metric.objects.get(name='request.count')
        metric_rq_time = Metric.objects.get(name='response.time')

        MetricValue.add(metric_rq_count,
                        start_aligned,
                        end_aligned,
                        self.service,
                        label="Count",
                        value_raw=0,
                        value_num=0,
                        value=0)

        MetricValue.add(metric_rq_time,
                        start_aligned,
                        end_aligned,
                        self.service,
                        label="Count",
                        value_raw=700,
                        value_num=700,
                        value=700)
        
        nc = NotificationCheck.objects.get()
        self.assertTrue(len(nc.get_emails())> 0)
        self.assertTrue(len(nc.get_users())> 0)
        self.assertEqual(nc.last_send, None)
        self.assertTrue(nc.can_send)

        self.assertEqual(len(mail.outbox), 0)

        # make sure inactive will not trigger anything
        nc.active = False
        nc.save()
        capi.emit_notifications(start)
        self.assertEqual(len(mail.outbox), 0)

        nc.active = True
        nc.save()
        capi.emit_notifications(start)
        self.assertTrue(nc.receivers.all().count()>0)
        self.assertEqual(len(mail.outbox), nc.receivers.all().count())



        nc.refresh_from_db()
        notifications_url = reverse('monitoring:api_user_notifications')
        nresp = self.client.get(notifications_url)
        self.assertEqual(nresp.status_code, 200)
        ndata = json.loads(nresp.content)
        self.assertEqual(set([n['id'] for n in ndata['data']]), 
                         set(NotificationCheck.objects.all().values_list('id', flat=True)))
       
        self.assertTrue(isinstance(nc.last_send, datetime))
        self.assertFalse(nc.can_send)
        mail.outbox = []
        self.assertEqual(len(mail.outbox), 0)
        capi.emit_notifications(start)
        self.assertEqual(len(mail.outbox), 0)

        nc.last_send = start - nc.grace_period
        nc.save()

        self.assertTrue(nc.can_send)
        mail.outbox = []
        self.assertEqual(len(mail.outbox), 0)
        capi.emit_notifications(start)
        self.assertEqual(len(mail.outbox), nc.receivers.all().count())


class AutoConfigTestCase(TestCase):
    OGC_GS_1 = 'http://localhost/geoserver123/'
    OGC_GS_2 = 'http://google.com/test/'

    OGC_SERVER = {'default': {'BACKEND': 'nongeoserver'},
                  'geoserver1': {'BACKEND': 'geonode.geoserver', 'LOCATION': OGC_GS_1},
                  'external1': {'BACKEND': 'geonode.geoserver', 'LOCATION': OGC_GS_2}
                  }

    def setUp(self):
        super(AutoConfigTestCase, self).setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.is_active = True
        self.u.is_superuser = True
        self.u.email = 'test@email.com'
        self.u.set_password(self.passwd)
        self.u.save()
        self.user2 = 'test'
        self.passwd2 = 'test'
        self.u2, _ = get_user_model().objects.get_or_create(username=self.user2)
        self.u2.is_active = True
        self.u2.email = 'test2@email.com'
        self.u2.set_password(self.passwd2)
        self.u2.save()


    def test_autoconfig(self):
        with self.settings(OGC_SERVER=self.OGC_SERVER, SITEURL=self.OGC_GS_2):
            do_autoconfigure()
        h1 = Host.objects.get(name='localhost')
        h2 = Host.objects.get(name='google.com')
        s1 = Service.objects.get(name='geoserver1-geoserver')
        self.assertEqual(s1.host, h1)
        s2 = Service.objects.get(name='external1-geoserver')
        self.assertEqual(s2.host, h2)
    
        autoconf_url = reverse('monitoring:api_autoconfigure')
        resp = self.client.post(autoconf_url)
        self.assertEqual(resp.status_code, 401)
        self.client.login(username=self.user, password=self.passwd)

        resp = self.client.post(autoconf_url)
        self.assertEqual(resp.status_code, 200)





