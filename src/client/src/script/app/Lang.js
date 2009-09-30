/* Copyright (c) 2006-2008 MetaCarta, Inc., published under the Clear BSD
 * license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */


/**
 * Namespace: Lang
 * Internationalization namespace.  Contains dictionaries in various languages
 *     and methods to set and get the current language.
 */
Lang = {
    registerLinks: function () {
        var languages = {
            '#spanish': 'es',
            '#english': 'en'
        };

        for (var id in languages) {
            var domNode = Ext.DomQuery.selectNode(id);
            if (domNode) {
                domNode.onclick = (function(langcode) {
                    return function () {
                        (new Ext.state.CookieProvider).set("locale", langcode);
                        window.location.reload();
                        return false;
                    };
                })(languages[id]);
            }
        }
    }
};

Ext.onReady(Lang.registerLinks);


