package org.geonode.web.security;

import org.geonode.security.GeoNodeAuthProviderConfig;
import org.geoserver.security.web.auth.AuthenticationProviderPanel;
import org.apache.wicket.markup.html.form.TextField;
import org.apache.wicket.model.IModel;
import org.apache.wicket.validation.validator.UrlValidator;

public class GeoNodeAuthProviderPanel
extends AuthenticationProviderPanel<GeoNodeAuthProviderConfig>
{
    private static final long serialVersionUID = -6290291071014462789L;

    public GeoNodeAuthProviderPanel(String id, IModel<GeoNodeAuthProviderConfig> model) {
        super(id, model);
        TextField<String> host = new TextField<String>("baseUrl");
        host.add(new UrlValidator());
        this.add(host);
    }
}
