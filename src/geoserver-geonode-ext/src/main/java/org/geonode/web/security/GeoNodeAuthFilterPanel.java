package org.geonode.web.security;

import org.apache.wicket.markup.html.form.TextField;
import org.apache.wicket.model.IModel;
import org.apache.wicket.validation.validator.UrlValidator;
import org.geonode.security.GeoNodeAuthFilterConfig;
import org.geoserver.security.web.auth.AuthenticationFilterPanel;

public class GeoNodeAuthFilterPanel extends AuthenticationFilterPanel<GeoNodeAuthFilterConfig> {
    private static final long serialVersionUID = 6525505737315060871L;

    public GeoNodeAuthFilterPanel(String id, IModel<GeoNodeAuthFilterConfig> model) {
        super(id, model);
        TextField<String> baseUrl = new TextField<String>("baseUrl");
        baseUrl.add(new UrlValidator());
        add(baseUrl);
    }
}
