"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from actstream.models import Action, actor_stream
from dialogos.models import Comment
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils.translation import ugettext as _
from geonode.layers.populate_layers_data import create_layer_data
from geonode.base.populate_test_data import create_models
from geonode.social.templatetags.social_tags import activity_item
from geonode.layers.models import Layer


class SimpleTest(TestCase):

    fixtures = ['initial_data.json']

    def setUp(self):
        create_models(type='layer')
        create_layer_data()
        self.user = get_user_model().objects.filter(username='admin')[0]

    def test_layer_activity(self):
        """
        Tests the activity functionality when a layer is saved.
        """

        # A new activity should be created for each Layer.
        self.assertEqual(Action.objects.all().count(), Layer.objects.all().count())

        action = Action.objects.all()[0]
        layer = action.action_object

        # The activity should read:
        # layer.owner (actor) 'uploaded' (verb) layer (object)
        self.assertEqual(action.actor, action.action_object.owner)
        self.assertEqual(action.data.get('raw_action'), 'created')
        self.assertEqual(action.data.get('object_name'), layer.name)
        self.assertTrue(isinstance(action.action_object, Layer))
        self.assertIsNone(action.target)

        # Test the  activity_item template tag
        template_tag = activity_item(Action.objects.all()[0])

        self.assertEqual(template_tag.get('username'), action.actor.username)
        self.assertEqual(template_tag.get('object_name'), layer.name)
        self.assertEqual(template_tag.get('actor'), action.actor)
        self.assertEqual(template_tag.get('verb'), _('uploaded'))
        self.assertEqual(template_tag.get('action'), action)
        self.assertEqual(template_tag.get('activity_class'), 'upload')

        layer_name = layer.name
        layer.delete()

        # <user> deleted <object_name>
        action = Action.objects.all()[0]

        self.assertEqual(action.data.get('raw_action'), 'deleted')
        self.assertEqual(action.data.get('object_name'), layer_name)

        # objects are literally deleted so no action object or target should be related to a delete action.
        self.assertIsNone(action.action_object)
        self.assertIsNone(action.target)

        # Test the activity_item template tag
        action = Action.objects.all()[0]
        template_tag = activity_item(action)

        # Make sure the 'delete' class is returned
        self.assertEqual(template_tag.get('activity_class'), 'delete')

        # The layer's name should be returned
        self.assertEqual(template_tag.get('object_name'), layer_name)
        self.assertEqual(template_tag.get('verb'), _('deleted'))

        content_type = ContentType.objects.get_for_model(Layer)
        layer = Layer.objects.all()[0]
        comment = Comment(author=self.user,
                          content_type=content_type,
                          object_id=layer.id,
                          comment="This is a cool layer.")
        comment.save()

        action = Action.objects.all()[0]

        self.assertEqual(action.actor, self.user)
        self.assertEqual(action.data.get('raw_action'), 'created')
        self.assertEqual(action.action_object, comment)
        self.assertEqual(action.target, layer)

        template_tag = activity_item(action)

        # <user> added a comment on <target>
        self.assertEqual(template_tag.get('verb'), _('added a comment'))
        self.assertEqual(template_tag.get('activity_class'), 'comment')
        self.assertEqual(template_tag.get('target'), action.target)
        self.assertEqual(template_tag.get('preposition'), _('on'))
        self.assertIsNone(template_tag.get('object'))
        self.assertEqual(template_tag.get('target'), layer)

        # Pre-fecthing actstream breaks the actor stream
        self.assertIn(action, actor_stream(self.user))
