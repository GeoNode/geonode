
from geonode.layers.models import Style, Attribute, Layer

styles = [
    {
        "name": "test_style_1", 
        "sld_url": "http://localhost:8080/geoserver/rest/styles/test_style.sld", 
        "sld_body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><sld:StyledLayerDescriptor xmlns=\"http://www.opengis.net/sld\" xmlns:sld=\"http://www.opengis.net/sld\" xmlns:ogc=\"http://www.opengis.net/ogc\" xmlns:gml=\"http://www.opengis.net/gml\" version=\"1.0.0\"><sld:NamedLayer><sld:Name>test_style_1</sld:Name><sld:UserStyle><sld:Name>test_style_1</sld:Name><sld:Title/><sld:FeatureTypeStyle><sld:Name>name</sld:Name><sld:Rule><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name=\"fill\">#888800</sld:CssParameter></sld:Fill><sld:Stroke><sld:CssParameter name=\"stroke\">#ffffbb</sld:CssParameter><sld:CssParameter name=\"stroke-width\">0.7</sld:CssParameter></sld:Stroke></sld:PolygonSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>", 
    },
    {
        "name": "test_style_2", 
        "sld_url": "http://localhost:8080/geoserver/rest/styles/test_style.sld", 
        "sld_body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><sld:StyledLayerDescriptor xmlns=\"http://www.opengis.net/sld\" xmlns:sld=\"http://www.opengis.net/sld\" xmlns:ogc=\"http://www.opengis.net/ogc\" xmlns:gml=\"http://www.opengis.net/gml\" version=\"1.0.0\"><sld:NamedLayer><sld:Name>test_style_2</sld:Name><sld:UserStyle><sld:Name>test_style_2</sld:Name><sld:Title/><sld:FeatureTypeStyle><sld:Name>name</sld:Name><sld:Rule><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name=\"fill\">#888800</sld:CssParameter></sld:Fill><sld:Stroke><sld:CssParameter name=\"stroke\">#ffffbb</sld:CssParameter><sld:CssParameter name=\"stroke-width\">0.7</sld:CssParameter></sld:Stroke></sld:PolygonSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>", 
    },
    {
        "name": "test_style_3", 
        "sld_url": "http://localhost:8080/geoserver/rest/styles/test_style.sld", 
        "sld_body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><sld:StyledLayerDescriptor xmlns=\"http://www.opengis.net/sld\" xmlns:sld=\"http://www.opengis.net/sld\" xmlns:ogc=\"http://www.opengis.net/ogc\" xmlns:gml=\"http://www.opengis.net/gml\" version=\"1.0.0\"><sld:NamedLayer><sld:Name>test_style_3</sld:Name><sld:UserStyle><sld:Name>test_style_3</sld:Name><sld:Title/><sld:FeatureTypeStyle><sld:Name>name</sld:Name><sld:Rule><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name=\"fill\">#888800</sld:CssParameter></sld:Fill><sld:Stroke><sld:CssParameter name=\"stroke\">#ffffbb</sld:CssParameter><sld:CssParameter name=\"stroke-width\">0.7</sld:CssParameter></sld:Stroke></sld:PolygonSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>", 
    }
]

attributes = [
    {
        "attribute": "the_geom",
        "attribute_label": "Shape",
        "attribute_type": "gml:Geometry",
        "visible": False,
        "display_order": 3
    },
    {
        "attribute": "description",
        "attribute_label": "Description",
        "attribute_type": "xsd:string",
        "visible": True,
        "display_order": 2
    },
    {
        "attribute": "place_name",
        "attribute_label": "Place Name",
        "attribute_type": "xsd:string",
        "visible": True,
        "display_order": 1
    }
]

def create_layer_data():
    layer = Layer.objects.get(pk=1)
    for style in styles:
        new_style = Style.objects.create(name=style['name'],sld_url=style['sld_url'],sld_body=style['sld_body'])
        layer.styles.add(new_style)
        layer.default_style = new_style
    layer.save() 


    for attr in attributes:
        Attribute.objects.create(layer=layer,
            attribute=attr['attribute'],
            attribute_label=attr['attribute_label'],
            attribute_type=attr['attribute_type'],
            visible=attr['visible'],
            display_order=attr['display_order']
        )