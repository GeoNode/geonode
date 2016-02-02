import logging
import tempfile

import os
from subprocess import call, Popen, PIPE

from celery.app import shared_task
from geonode.layers.utils import file_upload
from headless_app import app

__author__ = 'lucernae'


LOGGER = logging.getLogger(__name__)


# @shared_task
# def run_analysis_docker(arguments, output_file, layer_folder, output_folder, analysis):
#     """
#     Running an analysis via InaSAFE cli in docker container
#
#     (useful for sandboxing InaSAFE environment and deps)
#     """
#     # call system function
#     call(["inasafe", arguments, layer_folder, output_folder])
#     # TODO: Save the layer file and all info to geonode (upload?)
#     saved_layer = file_upload(
#         output_file,
#         overwrite=True,
#     )
#     saved_layer.set_default_permissions()
#     analysis.impact_layer = saved_layer
#     analysis.save(run_analysis=False)
#
#
# @shared_task
# def run_analysis_cli(arguments, output_file):
#     """
#     Running an analysis via InaSAFE CLI directly in the filesystem
#
#     inasafe-cli should be installed on /usr/local/bin or in the PATH
#     """
#     # call system function
#     call("inasafe "+arguments)
#     # TODO: Save the layer file and all info to geonode (upload?)


@app.task(name='headless.tasks.inasafe_wrapper.filter_impact_function')
def filter_impact_function(hazard=None, exposure=None):
    """Proxy tasks for celery broker"""
    LOGGER.info('Masuk sini')
    return ['doh']


@app.task(name='headless.tasks.inasafe_wrapper.run_analysis')
def run_analysis(hazard, exposure, function, aggregation=None,
                 generate_report=False):
    """Proxy tasks for celery broker"""
    LOGGER.info('Masuk sini')
    return 'nah'


# @shared_task
# def if_list(hazard_file=None, exposure_file=None,
#             layer_folder=None, output_folder=None):
#     """
#     Show possible IF list
#
#     Can also return filtered IF list if arguments is provided
#     :return: Filtered list of Impact Function IDs
#     :rtype: list
#     """
#     # call system function
#     if hazard_file and exposure_file:
#         arguments = [
#             "inasafe", "--hazard=%s --exposure=%s --list-functions" % (
#                 hazard_file, exposure_file)]
#         if layer_folder:
#             arguments.append(layer_folder)
#         p = Popen(arguments, stdout=PIPE)
#     else:
#         p = Popen(["inasafe", "--list-functions"], stdout=PIPE)
#
#     output, err = p.communicate()
#     start = False
#     ifs = []
#     for line in output.split('\n'):
#         line = line.strip()
#         if line == 'Available Impact Function:' and not start:
#             start = True
#         elif start and not line == '':
#             ifs.append(line)
#         elif start and line == '':
#             break
#
#     return ifs
#
#
# @shared_task
# def generate_map_report(impact_file=None, layer_folder=None):
#     """
#     Generate map report of given impact map
#     :return:
#     """
#     if impact_file:
#         temp_file = os.path.join(
#             tempfile._get_default_tempdir(),
#             tempfile._get_candidate_names().next())
#         arguments = [
#             "inasafe", "report --impact=%s --output-file=%s" % (
#                 impact_file,
#                 temp_file
#             )
#         ]
#         if layer_folder:
#             arguments.append(layer_folder)
#
#         p = Popen(arguments, stdout=PIPE)
#
#         output, err = p.communicate()
#         LOGGER.info('Output \n%s' % output)
#         LOGGER.info('Error : %s' % err)
