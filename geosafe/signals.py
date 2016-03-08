# coding=utf-8
from django.db.models.signals import post_save
from django.dispatch import receiver

from geonode.layers.models import Layer
from geosafe.models import Analysis
from geosafe.tasks.analysis import create_metadata_object, \
    process_impact_result
from geosafe.tasks.headless.analysis import run_analysis

__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'
__date__ = '2/3/16'


@receiver(post_save, sender=Layer)
def layer_post_save(sender, instance, created, **kwargs):
    # execute in a different task to let post_save returns and create metadata
    # asyncly
    create_metadata_object.delay(instance.id)


@receiver(post_save, sender=Analysis)
def analysis_post_save(sender, instance, created, **kwargs):
    """

    :param sender:
    :param instance:
    :type instance: Analysis
    :param created:
    :param kwargs:
    :return:
    """
    # Used to run impact analysis when analysis object is firstly created
    if created:
        hazard = instance.get_layer_url(instance.hazard_layer)
        exposure = instance.get_layer_url(instance.exposure_layer)
        function = instance.impact_function_id
        impact_url_result = run_analysis.delay(
            hazard,
            exposure,
            function,
            generate_report=True)
        async_result = process_impact_result.delay(
            instance.id, impact_url_result)
        instance.task_id = async_result.task_id
        instance.save()
