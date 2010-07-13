package org.geonode.security;

import static org.custommonkey.xmlunit.XMLAssert.*;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.servlet.Filter;
import javax.servlet.http.Cookie;
import javax.xml.parsers.ParserConfigurationException;

import junit.framework.Test;

import org.apache.commons.codec.binary.Base64;
import org.custommonkey.xmlunit.SimpleNamespaceContext;
import org.custommonkey.xmlunit.XMLUnit;
import org.custommonkey.xmlunit.exceptions.XpathException;
import org.geoserver.data.test.MockData;
import org.geoserver.platform.GeoServerExtensions;
import org.geoserver.test.GeoServerTestSupport;
import org.w3c.dom.Document;
import org.xml.sax.SAXException;

import com.mockrunner.mock.web.MockHttpServletRequest;
import com.mockrunner.mock.web.MockHttpServletResponse;

public class SecuredAccessTest extends GeoServerTestSupport {

    /**
     * This behaves like a read only test in that the mock status is reset by each test
     * independently
     */
    public static Test suite() {
        return new OneTimeTestSetup(new SecuredAccessTest());
    }

    static MockSecurityClient client;

    @Override
    protected List<Filter> getFilters() {
        return Collections.singletonList((Filter) GeoServerExtensions
                .bean("geonodeFilterChainProxy"));
    }

    @Override
    protected void oneTimeSetUp() throws Exception {
        super.oneTimeSetUp();

        // init xmlunit
        Map<String, String> namespaces = new HashMap<String, String>();
        namespaces.put("wfs", "http://www.opengis.net/wfs");
        namespaces.put("ows", "http://www.opengis.net/ows");
        namespaces.put("ogc", "http://www.opengis.net/ogc");
        namespaces.put("xs", "http://www.w3.org/2001/XMLSchema");
        namespaces.put("xsd", "http://www.w3.org/2001/XMLSchema");
        namespaces.put("gml", "http://www.opengis.net/gml");
        namespaces.put(MockData.CITE_PREFIX, MockData.CITE_URI);
        namespaces.put(MockData.CDF_PREFIX, MockData.CDF_URI);
        namespaces.put(MockData.CGF_PREFIX, MockData.CGF_URI);
        namespaces.put(MockData.SF_PREFIX, MockData.SF_URI);
        XMLUnit.setXpathNamespaceContext(new SimpleNamespaceContext(namespaces));

        // build an empty mock client
        client = new MockSecurityClient();

        // override the auth provider client
        GeoNodeAuthenticationProvider authProvider = GeoServerExtensions.bean(
                GeoNodeAuthenticationProvider.class, applicationContext);
        authProvider.client = client;

        // override the cookie filter
        GeoNodeCookieProcessingFilter filter = GeoServerExtensions.bean(
                GeoNodeCookieProcessingFilter.class, applicationContext);
        filter.client = client;
    }

    /**
     * No authentication, we should get a challenge to authenticate
     */
    public void testNoAuth() throws Exception {
        MockHttpServletResponse resp = getAsServletResponse("wfs?request=GetFeature&version=1.0.0&service=wfs&typeName="
                + getLayerId(MockData.BUILDINGS));
        assertEquals(401, resp.getErrorCode());
        assertEquals("Basic realm=\"GeoServer Realm\"", resp.getHeader("WWW-Authenticate"));
    }

    public void testAdminBasic() throws Exception {
        String username = "admin";
        String password = "geonode";
        client.addUserAuth(username, password, true, null, null);

        checkValidBasicAuth(username, password);
    }

    public void testAdminCookie() throws Exception {
        String username = "admin";
        String cookie = "geonode-auth-abcde";
        client.addCookieAuth(cookie, username, true, null, null);

        checkValidCookieAuth(cookie);
    }
    
    public void testUserBasicRead() throws Exception {
        String username = "joe";
        String password = "secret";
        client.addUserAuth(username, password, false, Collections.singletonList(getLayerId(MockData.BUILDINGS)), null);

        checkValidBasicAuth(username, password);
    }
    
    public void testUserBasicReadWrite() throws Exception {
        String username = "joe";
        String password = "secret";
        client.addUserAuth(username, password, false, null, Collections.singletonList(getLayerId(MockData.BUILDINGS)));

        checkValidBasicAuth(username, password);
    }
    
    public void testUserCookie() throws Exception {
        String username = "joe";
        String cookie = "geonode-auth-lameuser";
        client.addCookieAuth(cookie, username, false, Collections.singletonList(getLayerId(MockData.BUILDINGS)), null);

        checkValidCookieAuth(cookie);
    }

    void checkValidBasicAuth(String username, String password) throws Exception,
            ParserConfigurationException, SAXException, IOException, XpathException {
        MockHttpServletRequest request = createRequest("wfs?request=GetFeature&version=1.0.0&service=wfs&typeName="
                + getLayerId(MockData.BUILDINGS));
        request.addHeader("Authorization", "Basic "
                + new String(Base64.encodeBase64((username + ":" + password).getBytes())));

        MockHttpServletResponse resp = dispatch(request);
        assertEquals(200, resp.getErrorCode());
        Document doc = dom(new ByteArrayInputStream(resp.getOutputStreamContent().getBytes()));
        print(doc);
        assertXpathEvaluatesTo("1", "count(/wfs:FeatureCollection)", doc);
    }

    void checkValidCookieAuth(String cookie) throws Exception,
            ParserConfigurationException, SAXException, IOException, XpathException {
        MockHttpServletRequest request = createRequest("wfs?request=GetFeature&version=1.0.0&service=wfs&typeName="
                + getLayerId(MockData.BUILDINGS));
        request.addCookie(new Cookie(GeoNodeCookieProcessingFilter.GEONODE_COOKIE_NAME, cookie));

        MockHttpServletResponse resp = dispatch(request);
        assertEquals(200, resp.getErrorCode());
        Document doc = dom(new ByteArrayInputStream(resp.getOutputStreamContent().getBytes()));
        print(doc);
        assertXpathEvaluatesTo("1", "count(/wfs:FeatureCollection)", doc);
    }
    
    
}
