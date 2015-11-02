import os
from subprocess import call, Popen, PIPE
from celery.task import task


__author__ = 'lucernae'


@task(name='geosafe.tasks.analysis.run_analysis', queue='cleanup')
def run_analysis(command, output_file):
    """
    Running an analysis
    """
    # call system function
    call(["inasafe", command])
    # TODO: Save the layer file and all info to geonode (upload?)


@task(name='geosafe.tasks.analysis.if_list', queue='cleanup')
def if_list(hazard_file=None, exposure_file=None):
    """
    Show possible IF list
    """
    # call system function
    if hazard_file and exposure_file:
        p = Popen(["inasafe", "--hazard=%s --exposure=%s --list-functions" % (
            hazard_file, exposure_file
        )], stdout=PIPE)
    else:
        p = Popen(["inasafe", "--list-functions"], stdout=PIPE)

    output, err = p.communicate()
    start = False
    ifs = []
    for line in output.split('\n'):
        if line == 'Available Impact Function:' and not start:
            start = True
        elif start and not line.strip() == '':
            ifs.append(line)
        elif start and line.strip() == '':
            break
    return ifs
