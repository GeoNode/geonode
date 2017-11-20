from .db_connections import Database
from django.db import models


class ClassFactory(object):
    DJANGO_MODEL = {
        'bigint': models.BigIntegerField,
        'character varying': models.CharField,
        'integer': models.IntegerField,
        'boolean': models.BooleanField,
        'text': models.TextField,
        'smallint': models.SmallIntegerField
    }
    def __init__(self):
        super(ClassFactory, self).__init__()
            
    def create_model(self, name, fields=None, app_label='', module='', options=None, admin_opts=None, db='default'):      
        """
        Create specified model
        EX: model = create_model('NycRoad', app_label='front_end', options=dict(db_table='nyc_road'))
        """
        class Meta:
            # Using type('Meta', ...) gives a dictproxy error during model creation
            pass
        if app_label:
            # app_label must be set using the Meta inner class
            setattr(Meta, 'app_label', app_label)
        # Update Meta with any options that were provided
        if options is not None:
            for key, value in options.iteritems():
                setattr(Meta, key, value)

        # Set up a dictionary to simulate declarations within a class
        attrs = {'__module__': module, 'Meta': Meta, 'database':db}                 
        # Add in any fields that were provided                       
        if fields:                                                            
            attrs.update(fields)                                              
        # Create the class, which automatically triggers ModelBase processing
        model = type(name, (models.Model,), attrs)                            
        # Create an Admin class if admin options were provided                
        # if admin_opts is not None:                            
        #     class Admin(admin.ModelAdmin):                    
        #         pass                      
        #     for key, value in admin_opts:    
        #         setattr(Admin, key, value)   
        #     admin.site.register(model, Admin)
        return model
     
    def get_model_field(self, data_type,column_name=None, blank=True, is_null=True, character_maximum_length=None, *args, **kwargs):
        if character_maximum_length is None:
            if column_name == 'fid':
                return self.DJANGO_MODEL[data_type](null=is_null, primary_key=True)
            else:
                return self.DJANGO_MODEL[data_type](null=is_null)
        else:
            return self.DJANGO_MODEL[data_type](null=is_null, max_length=character_maximum_length)

    def get_model(self, name, table_name, app_label='dynamic', db=None):
        schema_infos = Database(db_name=db).get_table_schema_info(table_name=table_name)
        fields = {f.column_name: self.get_model_field(**f) for f in schema_infos if f.data_type in self.DJANGO_MODEL}
        return self.create_model(name, app_label=app_label, fields=fields, options=dict(db_table=table_name), db=db)                
