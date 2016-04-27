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

# easy_install boto 
# You will also need:
# - A .pem keyfile generated using the Amazon web interface to launch new instances
# - The secret and access keys created from the 
# The only pre-reqs are having created a keypair (.pem file) 
# via the amazon web interface and knowing the AWS key and secret
#
# Usage:
#     export AWS_ACCESS_KEY_ID='blahblah'
#     export AWS_SECRET_ACCESS_KEY='blebleble'
#     ec2.py launch 
import os, time, boto
import sys
import ConfigParser

CONFIG_FILE=".gnec2.cfg"

# Ubuntu
# https://help.ubuntu.com/community/EC2StartersGuide
# All us-east-1 EBS Backed
LUCID_32="ami-3e9b4957"
LUCID_64="ami-349b495d"
MAVERIK_32="ami-c012cea9"
MAVERIK_64="ami-c412cead"
NATTY_32="ami-1616ca7f"
NATTY_64="ami-e016ca89"
ONEIRIC_32="ami-e1aa7388"
ONEIRIC_64="ami-8baa73e2"
PRECISE_32="ami-b89842d1"
PRECISE_64="ami-3c994355"
TRUSTY_32="ami-134b0923"
TRUSTY_64="ami-d0ba0cb8"


# CentOS
# All us-east-1
CENTOS_52_32=""
CENTOS_52_64=""
CENTOS_54_32="ami-f8b35e91"
CENTOS_54_64="ami-ccb35ea5"
CENTOS_62_32="ami-5c4e9235"
CENTOS_62_64=""

DEFAULT_BASE=TRUSTY_64
DEFAULT_INSTANCE_TYPE='m1.small'

GEONODE_LUCID_32=""
GEONODE_LUCID_64=""
GEONODE_MAVERIK_32=""
GEONODE_MAVERIK_64=""
GEONODE_NATTY_32=""
GEONODE_NATTY_64=""
GEONODE_ONEIRIC_32=""
GEONODE_ONEIRIC_64=""
GEONODE_PRECISE_32=""
GEONODE_PRECISE_64=""

DEFAULT_BASE_GEONODE=GEONODE_PRECISE_32

ALPHA_ELASTIC_IP="54.235.204.189"

def writeconfig(config):
    # Writing our configuration file to CONFIG_FILE
    configfile = open(CONFIG_FILE, 'wb')
    config.write(configfile)
    configfile.close()
 
def readconfig(default_ami=None):

    config = ConfigParser.RawConfigParser()

    # If there is no config file, let's write one.
    if not os.path.exists(CONFIG_FILE):
        config.add_section('ec2')
        if default_ami == None:
            config.set('ec2', 'AMI', DEFAULT_BASE)
        else:
            config.set('ec2', 'AMI', default_ami)
        config.set('ec2', 'INSTANCE_TYPE', DEFAULT_INSTANCE_TYPE)
        config.set('ec2', 'SECURITY_GROUP', 'geonode')
        config.set('ec2', 'KEY_PATH', '~/.ssh/geonode-dev.pem')
        config.set('ec2', 'USER', 'ec2-user')
        writeconfig(config)
    else:
        config.read(CONFIG_FILE)
    return config

def launch_geonode():
    readconfig(default_ami=DEFAULT_BASE_GEONODE)
    launch()

def launch_base():
    readconfig(default_ami=DEFAULT_BASE)
    launch()
    
def set_alpha_ip():
    config = readconfig()
    conn = boto.connect_ec2()
    # Assign elastic ip to instance
    instance_id = config.get('ec2', 'INSTANCE')
    conn.associate_address(instance_id=instance_id, public_ip=ALPHA_ELASTIC_IP)


def launch():
    config = readconfig()
    MY_AMI=config.get('ec2', 'AMI')
    SECURITY_GROUP=config.get('ec2', 'SECURITY_GROUP')
    KEY_PATH = config.get('ec2', 'KEY_PATH')
    INSTANCE_TYPE = config.get('ec2', 'INSTANCE_TYPE')

    launch = True

    if config.has_option('ec2', 'HOST'):
        host = config.get('ec2', 'HOST')
        if host != "" and host is not None:
            print "there is already an instance launched"
            launch = False
            return
 
    if launch:
        conn = boto.connect_ec2()
        image = conn.get_image(MY_AMI)
        security_groups = conn.get_all_security_groups()

        try:
            [geonode_group] = [x for x in security_groups if x.name == SECURITY_GROUP]
        except ValueError:
            # this probably means the security group is not defined
            # create the rules programatically to add access to ports 21, 22, 80, 2300-2400, 8000, 8001, 8021 and 8080
            geonode_group = conn.create_security_group(SECURITY_GROUP, 'Cool GeoNode rules')
            geonode_group.authorize('tcp', 21, 21, '0.0.0.0/0') # Batch Upload FTP
            geonode_group.authorize('tcp', 22, 22, '0.0.0.0/0') # SSH
            geonode_group.authorize('tcp', 80, 80, '0.0.0.0/0') # Apache
            geonode_group.authorize('tcp', 2300, 2400, '0.0.0.0/0') # Passive FTP 
            geonode_group.authorize('tcp', 8000, 8001, '0.0.0.0/0') # Dev Django and Jetty
            geonode_group.authorize('tcp', 8021, 8021, '0.0.0.0/0' ) # Batch Upload FTP
            geonode_group.authorize('tcp', 8080, 8080, '0.0.0.0/0' ) # Tomcat

        try:
            [geonode_key] = [x for x in conn.get_all_key_pairs() if x.name == 'geonode']
        except ValueError:
            # this probably means the key is not defined
            # get the first one in the belt for now:
            print "GeoNode file not found in the server"
            geonode_key = conn.get_all_key_pairs()[0]

        reservation = image.run(security_groups=[geonode_group,], key_name=geonode_key.name, instance_type=INSTANCE_TYPE)
        instance = reservation.instances[0]

        print "Firing up instance"

        # Give it 10 minutes to appear online
        for i in range(120):
            time.sleep(5)
            instance.update()
            print instance.state
            if instance.state == "running":
                break

        if instance.state == "running":
            dns = instance.dns_name
            print "Instance up and running at %s" % dns

        config.set('ec2', 'HOST', dns)
        config.set('ec2', 'INSTANCE', instance.id)
        writeconfig(config)
        
        print "ssh -i %s ubuntu@%s" % (KEY_PATH, dns)
        print "Terminate the instance via the web interface %s" % instance

        time.sleep(20)
 
def terminate():
    config = readconfig()
    instance_id = config.get('ec2', 'INSTANCE')
    conn = boto.connect_ec2()
    conn.get_all_instances()
    instance = None
    for reservation in conn.get_all_instances():
        for ins in reservation.instances:
            if ins.id == instance_id:
                instance = ins

    print 'Terminating instance'
    instance.terminate()
    # Give it 10 minutes to terminate
    for i in range(120):
        time.sleep(5)
        instance.update()
        print instance.state
        if instance.state == "terminated":
            config.set('ec2', 'HOST', '')
            config.set('ec2', 'INSTANCE', '')
            configfile = open(CONFIG_FILE, 'wb')
            config.write(configfile)
            configfile.close()
            break

if sys.argv[1] == "launch_geonode":
    launch_geonode()
elif sys.argv[1] == "launch_base":
    launch_base()
elif sys.argv[1] == "set_alpha_ip":
    set_alpha_ip()
elif sys.argv[1] == "terminate":
    terminate()
elif sys.argv[1] == "host":
    config = readconfig()
    print config.get('ec2', 'HOST')
elif sys.argv[1] == "key":
    config = readconfig()
    print config.get('ec2', 'KEY_PATH')
else:
    print "Usage:\n    python %s launch_base\n     python %s launch_geonode\n    python %s terminate" % (sys.argv[0], sys.argv[0], sys.argv[0])
