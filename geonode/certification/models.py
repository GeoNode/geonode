from django.db import models
from geonode.people.models import Profile 
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from geonode.maps.models import  Map
from geonode.layers.models import Layer
from django.db.models import signals

# Create your models here.
    
class CertificationManager(models.Manager):

    def certify(self, user, model):
        """
        Create a certification for a particular map/layer and user
        """
        
        my_ct = ContentType.objects.get_for_model(model)
        certification, created = Certification.objects.get_or_create(certifier=user, object_ct = my_ct, object_id = model.id)
        if created:
            certification.save()
        return certification

    def uncertify(self,user,model):
        """
        Delete a certification for a particular map/layer and user
        """  
        my_ct = ContentType.objects.get_for_model(model)
        try:      
            Certification.objects.get(certifier=user, object_ct = my_ct, object_id = model.id).delete()
        except:
            pass
        
    def is_certified(self,user,model_obj):
        """
        Return a boolean indicating whether a model object has been certified by a user
        """
        if not user.id:
            return False
        my_ct = ContentType.objects.get_for_model(model_obj)
        return bool(Certification.objects.filter(certifier=user, object_ct = my_ct, object_id = model_obj.id))
    
    
    def certifications_user (self, user):
        return Certification.objects.filter(certifier=user)
    
    def certifications_object (self, model_obj):
        my_ct = ContentType.objects.get_for_model(model_obj)
        return Certification.objects.filter(object_ct = my_ct, object_id= model_obj.id)    
        
        
        
class Certification (models.Model):
    certifier = models.ForeignKey(Profile)
    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_ct', 'object_id')
    
    objects = CertificationManager()        
    
    
    
def delete_certification(instance, sender, **kwargs):
        my_ct = ContentType.objects.get_for_model(instance)
        certifications = Certification.objects.filter(object_ct = my_ct, object_id= instance.id)    
        for certification in certifications:
            certification.delete()
            
signals.post_delete.connect(delete_certification, sender=Layer)
signals.post_delete.connect(delete_certification, sender=Map)
