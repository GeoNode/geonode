package org.geonode.web.security;

import org.apache.wicket.markup.html.panel.Panel;
import org.apache.wicket.model.Model;
import org.apache.wicket.util.tester.TestPanelSource;
import org.geonode.security.GeoNodeSecurityServiceConfig;
import org.geoserver.web.GeoServerWicketTestSupport;

public class GeoNodeAuthProviderPanelTest extends GeoServerWicketTestSupport {
    @SuppressWarnings("serial") // we should not be serializing TestPanelSource anyway...
    private static TestPanelSource geonodeAuthProviderSource = new TestPanelSource() {
        public Panel getTestPanel(String id) {
            return new FormComponentTestingPanel(id, 
                new GeoNodeAuthProviderPanel("formComponentPanel",
                    new Model<GeoNodeSecurityServiceConfig>(new GeoNodeSecurityServiceConfig())));
        }
    };

    public void testVisitPanel() {
        login();
        tester.startPanel(geonodeAuthProviderSource);
        tester.assertContains("GeoNode");
    }
}
