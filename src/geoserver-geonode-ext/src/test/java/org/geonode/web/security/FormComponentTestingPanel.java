package org.geonode.web.security;

import org.apache.wicket.Component;
import org.apache.wicket.markup.html.panel.Panel;

public class FormComponentTestingPanel extends Panel {
    private static final long serialVersionUID = 9132936853750313815L;

    public FormComponentTestingPanel(String id, Component component) {
        super(id);
        this.add(component);
    }
}
