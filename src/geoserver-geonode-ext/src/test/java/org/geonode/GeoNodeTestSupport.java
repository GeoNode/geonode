package org.geonode;

import java.util.HashMap;
import java.util.Map;

import org.custommonkey.xmlunit.SimpleNamespaceContext;
import org.custommonkey.xmlunit.XMLUnit;
import org.geonode.security.GeoNodeDataAccessManager;
import org.geoserver.data.test.MockData;
import org.geoserver.platform.GeoServerExtensions;
import org.geoserver.test.GeoServerTestSupport;

public abstract class GeoNodeTestSupport extends GeoServerTestSupport {

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

        // if necessary, disable the authorization subsystem
        if (!isAuthorizationEnabled()) {
            GeoNodeDataAccessManager manager = GeoServerExtensions.bean(
                    GeoNodeDataAccessManager.class, applicationContext);
            manager.setAuthenticationEnabled(false);
        }
    }

    /**
     * Returns the spring context locations to be used in order to build the GeoServer Spring
     * context. Subclasses might want to provide extra locations in order to test extension points.
     * @return
     */
    @Override
    protected String[] getSpringContextLocations() {
        return new String[] {
                "classpath*:/applicationContext.xml",
                "classpath*:/geonodeApplicationSecurityContext.xml"
            };
    }

    protected boolean isAuthorizationEnabled() {
        return false;
    }

}
