# Metadata XSL output App

The ``metadataxsl`` contrib app provides a downloadable metadata having the same format as the ISO
metadata, but having a header like
```XML
      <?xml-stylesheet type="text/xsl"
                       href="http://url.to.transfromation.xsl/this.is.the.xsl"?>
```
in order to have the metadata properly formatted on the browser.

The interface will present the link "ISO with XSL" along with the other output formats:
     ![image](https://cloud.githubusercontent.com/assets/717359/14913848/4663a80c-0e06-11e6-868d-0877acdb65d6.png)

In order to have a different output, you will only need to customize the XSL file and provide the CSS files if needed.

# Settings

## Update the existing resources

In order to make it possibile for a resource to have its metadata exported as ISO+XSL, it needs to
have a new entry in the ``base_link`` table.
The implementation will create the needed links every time a new resource is added, but we need to
post-process the existing resources and add the missing links.

In order to add the missing links, you need to enter the geonode directory and issue the command:

        python manage.py addmissinglinks

For each resource having a link for the ISO metadata, a new link for the ISO+XSL will be created.

## Collect static files

This step is needed in order to copy in the static dir the ``.xsl`` file that will be referenced by the
exported metadata file, and one ``.css`` file that is referenced within the xsl file.

        python manage.py collectstatic

This means that any customization to the output format should be performed on these files.

# Other refs

Please check the issue https://github.com/GeoNode/geonode/issues/2453
