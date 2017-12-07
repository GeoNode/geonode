

def prepare_messages(layers):
    metadata_field_list = ['owner', 'title', 'date', 'date_type', 'edition', 'abstract', 'purpose',
                           'maintenance_frequency', 'regions', 'restriction_code_type', 'constraints_other',
                           'license', 'language', 'spatial_representation_type', 'resource_type',
                           'temporal_extent_start', 'temporal_extent_end', 'supplemental_information',
                           'data_quality_statement', 'thumbnail_url', 'elevation_regex', 'time_regex', 'keywords',
                           'category']

    list_messages = dict()

    for layer in layers:
        for field in metadata_field_list:
            if not getattr(layer, layer._meta.get_field(field).name):
                list_messages[layer.id] = "Please update layer metadata, missing some information"
                break
            else:
                list_messages[layer.id] = "Completed"

    return list_messages
