from django import forms
from geonode.maps.models import Layer, LayerAttribute
from geonode.contrib.datatables.models import DataTable, DataTableAttribute

class TableJoinAdminForm(forms.ModelForm):
    """
    Limit the layer and attribute choices.
    """
    def __init__(self, *args, **kwargs):
        super(TableJoinAdminForm, self).__init__(*args, **kwargs)

        if self.instance and self.instance.id:
            # Yes, limit choices

            # Set the datatable and attribute
            self.fields['datatable'].queryset = DataTable.objects.filter(\
                                    pk=self.instance.datatable.id)

            self.fields['table_attribute'].queryset = DataTableAttribute.objects.filter(\
                                    datatable=self.instance.datatable.id)

            # Set the source layer and attribute
            self.fields['source_layer'].queryset = Layer.objects.filter(\
                                    pk=self.instance.source_layer.id)

            self.fields['layer_attribute'].queryset = LayerAttribute.objects.filter(\
                                    layer=self.instance.source_layer.id)

            # Set the Join layer
            self.fields['join_layer'].queryset = Layer.objects.filter(\
                                    pk=self.instance.join_layer.id)

        elif 'initial' in kwargs:
            # These objects can't be created through the admin
            # Also, production would create dropdowns with 1000s of listings
            #
            self.fields['datatable'].queryset = DataTable.objects.none()
            self.fields['table_attribute'].queryset = DataTableAttribute.objects.none()

            self.fields['source_layer'].queryset = Layer.objects.none()
            self.fields['layer_attribute'].queryset = LayerAttribute.objects.none()

            self.fields['join_layer'].queryset = Layer.objects.none()


class JoinTargetAdminForm(forms.ModelForm):
    """
    Limit the JoinTarget Layer and LayerAttribute choices.
    (If not limited, the page can take many minutes--or never load
        e.g. listing 20k+ layers and all of the attributes in those layers
    )
    """
    def __init__(self, *args, **kwargs):
        super(JoinTargetAdminForm, self).__init__(*args, **kwargs)

        selected_layer_id = kwargs.get('initial', {}).get('layer', None)

        # Is this an existing/saved Join Target?
        #
        if self.instance and self.instance.id:
            # Yes, limit choices to the chosen layer and its attributes
            #
            self.fields['layer'].queryset = Layer.objects.filter(\
                                    pk=self.instance.layer.id)
            self.fields['attribute'].queryset = LayerAttribute.objects.filter(\
                                    layer=self.instance.layer.id)

        elif selected_layer_id and selected_layer_id.isdigit():
            self.fields['layer'].queryset = Layer.objects.filter(\
                                            pk=selected_layer_id)
            self.fields['attribute'].queryset = LayerAttribute.objects.filter(\
                                            layer=selected_layer_id)


        elif 'initial' in kwargs:
            # We can't "afford" to list everything.
            # Don't list any layers or their attributes
            #   - An admin template instructs the user on how
            #       to add a new JoinTarget via the Layer admin
            #
            self.fields['layer'].queryset = Layer.objects.none()
            self.fields['attribute'].queryset = LayerAttribute.objects.none()
