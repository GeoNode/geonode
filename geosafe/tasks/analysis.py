import logging

import os
from subprocess import call, Popen, PIPE

from celery.app import shared_task
from geonode.layers.utils import file_upload

__author__ = 'lucernae'


LOGGER = logging.getLogger(__name__)


@shared_task
def run_analysis_docker(arguments, output_file, layer_folder, output_folder, analysis):
    """
    Running an analysis via InaSAFE cli in docker container

    (useful for sandboxing InaSAFE environment and deps)
    """
    # call system function
    call(["inasafe", arguments, layer_folder, output_folder])
    # TODO: Save the layer file and all info to geonode (upload?)
    saved_layer = file_upload(
        output_file,
        overwrite=True,
    )
    saved_layer.set_default_permissions()
    analysis.impact_layer = saved_layer
    analysis.save(run_analysis=False)


@shared_task
def run_analysis_cli(arguments, output_file):
    """
    Running an analysis via InaSAFE CLI directly in the filesystem

    inasafe-cli should be installed on /usr/local/bin or in the PATH
    """
    # call system function
    call("inasafe "+arguments)
    # TODO: Save the layer file and all info to geonode (upload?)


@shared_task
def if_list(hazard_file=None, exposure_file=None,
            layer_folder=None, output_folder=None):
    """
    Show possible IF list

    Can also return filtered IF list if arguments is provided
    :return: Filtered list of Impact Function IDs
    :rtype: list
    """
    # call system function
    if hazard_file and exposure_file:
        arguments = [
            "inasafe", "--hazard=%s --exposure=%s --list-functions" % (
                hazard_file, exposure_file)]
        if layer_folder:
            arguments.append(layer_folder)
        p = Popen(arguments, stdout=PIPE)
    else:
        p = Popen(["inasafe", "--list-functions"], stdout=PIPE)

    output, err = p.communicate()
    start = False
    ifs = []
    for line in output.split('\n'):
        line = line.strip()
        if line == 'Available Impact Function:' and not start:
            start = True
        elif start and not line == '':
            ifs.append(line)
        elif start and line == '':
            break

    return ifs


@shared_task
def test_add(x, y):
    LOGGER.info('Test Add : %s + %s = %s' % (x, y, x + y))
    return x + y
