import json
import jenkins
import sys
from optparse import OptionParser
from six.moves.urllib.request import Request


JENKINS_IP = 'http://52.5.141.226/'
GEONODE_DEMO_DOMAIN = 'demo.geonode.org'
NODE_LIST = 'computer/api/json'
GEONODE_DEMO_JOB = 'geonode-aws'


class DemoGeonode(object):
    def __init__(self, username, token):
        self.j = jenkins.Jenkins(JENKINS_IP, username, token)

    def redeployDemo(self):
        nodes_data = json.loads(self.j.jenkins_open(Request(self.j.server + NODE_LIST)))
        demo_node = self.getDemoNode(nodes_data)
        if demo_node is not None:
            self.deleteNode(demo_node)
            self.buildJob(GEONODE_DEMO_JOB)
            print 're-deploy complete!'
        else:
            print 'No demo.genode.org node found on jenkins'

    def getDemoNode(self, nodes_data):
        demo_node = None
        for node in nodes_data['computer']:
            if GEONODE_DEMO_DOMAIN in node['displayName']:
                demo_node = node['displayName']
        return demo_node

    def deleteNode(self, node_name):
        print 'Deleting demo node'
        self.j.delete_node(node_name)
        print 'Deletion requested'

    def buildJob(self, job):
        print 'Building %s job' % job
        self.j.build_job(job)
        print 'Build requested'


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
            print 'Command not found'
    else:
        print 'username and access token are both required'
