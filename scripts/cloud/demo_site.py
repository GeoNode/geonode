# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import json
import jenkins
import sys
from optparse import OptionParser
from six.moves.urllib.request import Request


JENKINS_IP = 'http://52.7.139.177/'
GEONODE_DEMO_DOMAIN = 'demo.geonode.org'  # should match the jenkins configuration
NODE_LIST = 'computer/api/json'  # jenkins api backend
GEONODE_DEMO_JOB = 'geonode-aws'  # jenkins job name for demo site

# USAGE
# python demo_site.py -u username -t jenkins_api_token task
# task can be either "redeploy-demo-site", "build-demo-job"


class DemoGeonode(object):
    """
    This class allows interaction with the Jenkins APIs to do several tasks,
    for a more detailed guide on how to use self.j see
    https://python-jenkins.readthedocs.org/en/latest/api.html
    """
    def __init__(self, username, token):
        self.j = jenkins.Jenkins(JENKINS_IP, username, token)

    def redeployDemo(self):
        """Delete the jenkins node on which runs the amazon VM,
        this will both shutdown the VM and create a new one with a fresh geonode instance"""
        nodes_data = json.loads(self.j.jenkins_open(Request(self.j.server + NODE_LIST)))
        demo_node = self.getDemoNode(nodes_data)
        if demo_node is not None:
            self.deleteNode(demo_node)
            self.buildJob(GEONODE_DEMO_JOB)
            print('re-deploy complete!')
        else:
            print('No demo.genode.org node found on jenkins')

    def getDemoNode(self, nodes_data):
        """Commodity method to get the correct jenkins node name,
        the name is composed by 'demo.geonode.org' and the VM id"""
        demo_node = None
        for node in nodes_data['computer']:
            if GEONODE_DEMO_DOMAIN in node['displayName']:
                demo_node = node['displayName']
        return demo_node

    def deleteNode(self, node_name):
        """Delete the jenkins node and shutdown the amazon VM"""
        print('Deleting demo node')
        self.j.delete_node(node_name)
        print('Deletion requested')

    def buildJob(self, job):
        """Trigger a job build"""
        print(f'Building {job} job')
        self.j.build_job(job)
        print('Build requested')


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-u", "--username", dest="username",
                      help="jenkins username")
    parser.add_option("-t", "--token", dest="token",
                      help="jenkins access token")

    (options, args) = parser.parse_args()

    if options.username is not None and options.token is not None:
        task = sys.argv[-1]
        demo = DemoGeonode(options.username, options.token)
        if task == 'redeploy-demo-site':
            demo.redeployDemo()
        elif task == 'build-demo-job':
            demo.buildJob(GEONODE_DEMO_JOB)
        else:
            print('Command not found')
    else:
        print('username and access token are both required')
