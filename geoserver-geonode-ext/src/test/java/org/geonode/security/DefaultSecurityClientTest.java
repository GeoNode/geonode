/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import junit.framework.TestCase;

import org.apache.commons.codec.binary.Base64;
import org.easymock.classextension.EasyMock;
import org.geonode.security.LayersGrantedAuthority.LayerMode;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;

/**
 * Unit test suite for {@link DefaultSecurityClient}
 * 
 * @author groldan
 * 
 */
public class DefaultSecurityClientTest extends TestCase {

    private HTTPClient mockHttpClient;

    private DefaultSecurityClient client;

    @Override
    public void setUp() {
        mockHttpClient = EasyMock.createNiceMock(HTTPClient.class);
        client = new DefaultSecurityClient("http://localhost:8000/", mockHttpClient);
    }

    public void testSetApplicationContext() throws Exception {
        final String baseUrl = "http://127.0.0.1/fake";
        DefaultSecurityClient client2 = new DefaultSecurityClient(baseUrl, mockHttpClient);

        assertEquals(baseUrl, client2.getBaseUrl());
    }

    public void testAuthenticateAnonymous() throws Exception {
        String response = "{'is_superuser': false, 'rw': [], 'ro': [], 'is_anonymous': true, 'name': ''}";
        EasyMock.expect(
                mockHttpClient.sendGET(EasyMock.eq("http://localhost:8000/data/acls"),
                        (String[]) EasyMock.isNull())).andReturn(response);
        EasyMock.replay(mockHttpClient);

        Authentication authentication = client.authenticateAnonymous();
        EasyMock.verify(mockHttpClient);

        assertNotNull(authentication);
        assertTrue(authentication instanceof AnonymousAuthenticationToken);
        assertTrue(authentication.isAuthenticated());
        assertEquals("anonymous", authentication.getPrincipal());

        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>();
        authorities.addAll(authentication.getAuthorities());
        assertEquals(3, authorities.size());
        assertTrue(authorities.get(0) instanceof LayersGrantedAuthority);
        assertEquals(LayerMode.READ_ONLY, ((LayersGrantedAuthority) authorities.get(0)).getAccessMode());
        assertEquals(0, ((LayersGrantedAuthority) authorities.get(0)).getLayerNames().size());

        assertEquals(LayerMode.READ_WRITE,
                ((LayersGrantedAuthority) authorities.get(1)).getAccessMode());
        assertEquals(0, ((LayersGrantedAuthority) authorities.get(1)).getLayerNames().size());

        assertTrue(authorities.get(2) instanceof GrantedAuthority);
        assertEquals("ROLE_ANONYMOUS", authorities.get(2).getAuthority());

    }

    public void testAuthenticateCookie() throws Exception {
        final String cookieValue = "ABCD";
        final String[] requestHeaders = { "Cookie",
                GeoNodeCookieProcessingFilter.GEONODE_COOKIE_NAME + "=" + cookieValue };

        final String response = "{'is_superuser': true, 'rw': ['layer1', 'layer2'], 'ro': ['layer3'], 'is_anonymous': false, 'name': 'aang'}";

        EasyMock.expect(
                mockHttpClient.sendGET(EasyMock.eq("http://localhost:8000/data/acls"),
                        EasyMock.aryEq(requestHeaders))).andReturn(response);
        EasyMock.replay(mockHttpClient);

        Authentication authentication = client.authenticateCookie(cookieValue);
        EasyMock.verify(mockHttpClient);

        assertNotNull(authentication);
        assertTrue(authentication instanceof GeoNodeSessionAuthToken);
        assertTrue(authentication.isAuthenticated());
        assertEquals("aang", authentication.getPrincipal());

        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>();
        authorities.addAll(authentication.getAuthorities());
        assertEquals(3, authorities.size());
        assertTrue(authorities.get(0) instanceof LayersGrantedAuthority);
        assertEquals(LayerMode.READ_ONLY, ((LayersGrantedAuthority) authorities.get(0)).getAccessMode());
        assertEquals(Collections.singletonList("layer3"),
                ((LayersGrantedAuthority) authorities.get(0)).getLayerNames());

        assertEquals(LayerMode.READ_WRITE,
                ((LayersGrantedAuthority) authorities.get(1)).getAccessMode());
        assertEquals(Arrays.asList("layer1", "layer2"),
                ((LayersGrantedAuthority) authorities.get(1)).getLayerNames());

        assertTrue(authorities.get(2) instanceof GrantedAuthority);
        assertEquals(GeoNodeDataAccessManager.ADMIN_ROLE, authorities.get(2).getAuthority());
    }

    public void testAuthenticateUserPassword() throws Exception {
        String username = "aang";
        String password = "katara";
        final String[] requestHeaders = { "Authorization",
                "Basic " + new String(Base64.encodeBase64((username + ":" + password).getBytes())) };

        final String response = "{'is_superuser': false, 'rw': ['layer1'], 'ro': ['layer2', 'layer3'], 'is_anonymous': false, 'name': 'aang'}";

        EasyMock.expect(
                mockHttpClient.sendGET(EasyMock.eq("http://localhost:8000/data/acls"),
                        EasyMock.aryEq(requestHeaders))).andReturn(response);
        EasyMock.replay(mockHttpClient);

        Authentication authentication = client.authenticateUserPwd(username, password);
        EasyMock.verify(mockHttpClient);

        assertNotNull(authentication);
        assertTrue(authentication instanceof UsernamePasswordAuthenticationToken);
        assertTrue(authentication.isAuthenticated());
        assertEquals("aang", authentication.getPrincipal());

        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>();
        authorities.addAll(authentication.getAuthorities());
        assertEquals(2, authorities.size());
        assertTrue(authorities.get(0) instanceof LayersGrantedAuthority);
        assertEquals(LayerMode.READ_ONLY, ((LayersGrantedAuthority) authorities.get(0)).getAccessMode());
        assertEquals(Arrays.asList("layer2", "layer3"),
                ((LayersGrantedAuthority) authorities.get(0)).getLayerNames());

        assertEquals(LayerMode.READ_WRITE,
                ((LayersGrantedAuthority) authorities.get(1)).getAccessMode());
        assertEquals(Arrays.asList("layer1"),
                ((LayersGrantedAuthority) authorities.get(1)).getLayerNames());
    }
}
