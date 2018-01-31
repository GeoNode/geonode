

def prepare_messages(layers):
    metadata_field_list = ['owner', 'title', 'date', 'date_type', 'edition', 'abstract', 'purpose',
                           'maintenance_frequency', 'regions', 'restriction_code_type', 'constraints_other',
                           'license', 'language', 'spatial_representation_type', 'resource_type',
                           'temporal_extent_start', 'temporal_extent_end', 'supplemental_information',
                           'data_quality_statement', 'thumbnail_url', 'elevation_regex', 'time_regex', 'keywords',
                           'category']


    metadata_mandatory_fields = ['title', 'date', 'edition', 'abstract', 'restriction_code_type',
                                 'spatial_representation_type',
                                 'resource_type', 'data_quality_statement', 'category']

    list_messages = dict()

    for layer in layers:
        messages = dict()

        for field in metadata_mandatory_fields:
            if not getattr(layer, layer._meta.get_field(field).name):
                messages['mandatory_fields_msg'] = "Please update mandatory fields, missing some information!"
                list_messages[layer.id] = messages
                break
            else:
                messages['mandatory_fields_msg'] = ''
                list_messages[layer.id] = messages

        for field in metadata_field_list:

            if not getattr(layer, layer._meta.get_field(field).name):
                messages['layer_msg'] = "Please update layer metadata, missing some information"
                # list_messages[layer.id] = "Please update layer metadata, missing some information"
                list_messages[layer.id] = messages
                break
            else:
                messages['layer_msg'] = "Completed"
                list_messages[layer.id] = messages

    return list_messages
