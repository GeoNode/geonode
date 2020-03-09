from django.db import models


class SingletonModel(models.Model):
    """
    Base, abstract class for django singleton models

    Note: when registering a Singleton model in admin panel, remember to restrict deletion permissions
    according to your requirements, since "delete selected objects" uses QuerysSet.delete() instead of
    Model.delete()
    """

    class Meta:
        abstract = True

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass
