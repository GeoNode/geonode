/**
 * Copyright (c) 2008-2012 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = FormFieldHelp
 */

Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: SchemaAnnotations
 *
 *    Module for getting annotations from the WFS DescribeFeatureType schema.
 *    This is currently used in gxp.plugins.FeatureEditorForm and
 *    gxp.plugins.FeatureEditorGrid.
 *   
 *    The WFS needs to provide xsd:annotation in the XML Schema which is 
 *    reported back on a WFS DescribeFeatureType request. An example is:
 *  
 *    .. code-block:: xml
 *
 *      <xsd:element maxOccurs="1" minOccurs="0" name="PERSONS" nillable="true" type="xsd:double">
 *        <xsd:annotation>
 *          <xsd:appinfo>{"title":{"en":"Population"}}</xsd:appinfo>
 *          <xsd:documentation xml:lang="en">
 *            Number of persons living in the state
 *          </xsd:documentation>
 *        </xsd:annotation>
 *      </xsd:element>
 *
 *    To use this module simply use Ext.override in your class, and use the 
 *    getAnnotationsFromSchema function on a record from the attribute store.
 *
 *    .. code-block:: javascript
 *
 *    Ext.override(gxp.plugins.YourPlugin, gxp.plugins.SchemaAnnotations);
 *
 */
gxp.plugins.SchemaAnnotations = {

    /** api: method[getAnnotationsFromSchema]
     *
     *  :arg r: ``Ext.data.Record`` a record from the AttributeStore
     *  :returns: ``Object`` Object with label and helpText properties or
     *  null if no annotation was found.
     */
    getAnnotationsFromSchema: function(r) {
        var result = null;
        var annotation = r.get('annotation');
        if (annotation !== undefined) {
            result = {};
            var lang = GeoExt.Lang.locale.split("-").shift();
            var i, ii;
            for (i=0, ii=annotation.appinfo.length; i<ii; ++i) {
                var json = Ext.decode(annotation.appinfo[i]);
                if (json.title && json.title[lang]) {
                    result.label = json.title[lang];
                    break;
                }
            }
            for (i=0, ii=annotation.documentation.length; i<ii; ++i) {
                if (annotation.documentation[i].lang === lang) {
                    result.helpText = annotation.documentation[i].textContent;
                    break;
                }
            }
        }
        return result;
    }
};