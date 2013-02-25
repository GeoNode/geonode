package org.geonode.web.security;

import org.apache.wicket.markup.html.panel.Panel;
import org.apache.wicket.model.Model;
import org.apache.wicket.util.tester.TestPanelSource;
import org.geonode.security.GeoNodeAuthFilterConfig;
import org.geoserver.web.GeoServerWicketTestSupport;
import org.springframework.security.core.context.SecurityContextHolder;

public class GeoNodeAuthFilterPanelTest extends GeoServerWicketTestSupport {
    @SuppressWarnings("serial")
    private static TestPanelSource createProviderSource(final GeoNodeAuthFilterConfig config) {
        return new TestPanelSource() {
            public Panel getTestPanel(String id) {
                return new FormComponentTestingPanel(id, 
                    new GeoNodeAuthFilterPanel("formComponentPanel",
                        new Model<GeoNodeAuthFilterConfig>(config)));
            }
        };
    }
    
    @Override
    protected void tearDownInternal() throws Exception {
        super.tearDownInternal();
        SecurityContextHolder.getContext().setAuthentication(null);
    }

    public void testVisitPanel() {
        GeoNodeAuthFilterConfig config = new GeoNodeAuthFilterConfig();
        login();
        tester.startPanel(createProviderSource(config));
        tester.assertComponent("panel:formComponentPanel", GeoNodeAuthFilterPanel.class);
    }
}