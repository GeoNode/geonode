from django.contrib.contenttypes.models import ContentType

from django.test import TestCase
from django.contrib.auth.models import User
from geonode.maps.models import Map, Layer
from geonode.certification.models import Certification


class CertificationTest(TestCase):
    fixtures = ['certification_data.json']

    def test_certify_map(self):
        """
        Tests creation, removal, and retrieval of map certifications
        """
        user_obj = User.objects.get(id=1)
        map_obj = Map.objects.get(id=1)
        obj_type = ContentType.objects.get_for_model(map_obj)
        newcert = Certification.objects.certify(user_obj,map_obj)

        self.assertEquals(obj_type, newcert.object_ct)
        self.assertEquals(map_obj.id, newcert.object_id)
        self.assertEquals(1, len(Certification.objects.filter(object_ct=obj_type, object_id=map_obj.id)))
        self.assertTrue(Certification.objects.is_certified(user_obj,map_obj))

        self.assertEquals(1, len(Certification.objects.certifications_object(map_obj)))
        Certification.objects.certify(User.objects.get(id=2),map_obj)
        self.assertEquals(2, len(Certification.objects.certifications_object(map_obj)))

        self.assertEquals(1, len(Certification.objects.certifications_user(user_obj)))

        Certification.objects.uncertify(user_obj,map_obj)
        self.assertEquals(1, len(Certification.objects.certifications_object(map_obj)))        
        self.assertFalse(Certification.objects.is_certified(user_obj,map_obj))
        self.assertEquals(0, len(Certification.objects.certifications_user(user_obj)))

        Certification.objects.uncertify(User.objects.get(id=2),map_obj)
        self.assertEquals(0, len(Certification.objects.certifications_object(map_obj)))
        self.assertFalse(Certification.objects.is_certified(User.objects.get(id=2),map_obj))
        self.assertEquals(0, len(Certification.objects.certifications_user(User.objects.get(id=2))))


    def test_certify_layer(self):
        """
        Tests creation, removal, and retrieval of layer certifications
        """
        user_obj = User.objects.get(id=1)
        layer_obj = Layer.objects.get(id=1)
        obj_type = ContentType.objects.get_for_model(layer_obj)
        newcert = Certification.objects.certify(user_obj,layer_obj)

        self.assertEquals(obj_type, newcert.object_ct)
        self.assertEquals(layer_obj.id, newcert.object_id)
        self.assertEquals(1, len(Certification.objects.filter(object_ct=obj_type, object_id=layer_obj.id)))
        self.assertTrue(Certification.objects.is_certified(user_obj,layer_obj))

        self.assertEquals(1, len(Certification.objects.certifications_object(layer_obj)))
        Certification.objects.certify(User.objects.get(id=2),layer_obj)
        self.assertEquals(2, len(Certification.objects.certifications_object(layer_obj)))

        self.assertEquals(1, len(Certification.objects.certifications_user(user_obj)))

        Certification.objects.uncertify(user_obj,layer_obj)
        self.assertEquals(1, len(Certification.objects.certifications_object(layer_obj)))
        self.assertFalse(Certification.objects.is_certified(user_obj,layer_obj))
        self.assertEquals(0, len(Certification.objects.certifications_user(user_obj)))

        Certification.objects.uncertify(User.objects.get(id=2),layer_obj)
        self.assertEquals(0, len(Certification.objects.certifications_object(layer_obj)))
        self.assertFalse(Certification.objects.is_certified(User.objects.get(id=2),layer_obj))
        self.assertEquals(0, len(Certification.objects.certifications_user(User.objects.get(id=2))))
