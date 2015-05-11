import json
import jenkins
import sys
from optparse import OptionParser
from six.moves.urllib.request import Request

JENKINS_IP = 'http://52.5.141.226/'
GEONODE_DEMO_DOMAIN = 'demo.geonode.org'
NODE_LIST = 'computer/api/json'
GEONODE_DEMO_JOB = 'geonde-aws'


class DemoGeonode(object):
    def __init__(self, username, token):

        self.j = jenkins.Jenkins(JENKINS_IP, self.username, self.token)

    def redeployDemo(self):
        nodes_data = json.loads(self.j.jenkins_open(Request(self.j.server + NODE_LIST)))
        demo_node = getDemoNode(nodes_data)
        if demo_node is not None:
            deleteNode('demo_node')
            buildJob(GEONODE_DEMO_JOB)
            print 're-deploy complete!'
        else:
            print 'No demo.genode.org node found on jenkins'
        

    def getDemoNode(self, nodes_data):
        demo_node = None
        for node in nodes_data['computer']:
            if NODE_LIST in node['displayName']:
                demo_node = node['displayName']
        return demo_node


    def deleteNode(self, node_name):
        print 'Deleting demo node'
        self.j.delete_node('node_name')


    def buildJob(self):
        print 'Building %s job' % GEONODE_DEMO_JOB
        self.j.build_job(GEONODE_DEMO_JOB)



if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-u", "--username", dest="username",
                  help="jenkins username")
    parser.add_option("-t", "--token",
                  dest="token",
                  help="jenkins access token")
    (options, args) = parser.parse_args()
    if options.username is not None and options.token is not None:
        task = sys.argv[-1]
        if not task in ['redeploy-demo-site']:
            print 'command not found'
        else:
            demo = DemoGeonode(options.username, options.token)
            if task == 'redeploy-demo-site':
                demo.redeployDemo()
    else:
        print 'username and access token are both required'
    import ipdb; ipdb.set_trace()
