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

import configparser
# pip install boto3
# You will also need:
# - A .pem keyfile generated using the Amazon web interface to launch
# new instances
# - The secret and access keys created from the
# The only pre-reqs are having created a keypair (.pem file)
# via the amazon web interface and knowing the AWS key and secret
#
# Usage:
#     export AWS_ACCESS_KEY_ID='blahblah'
#     export AWS_SECRET_ACCESS_KEY='blebleble'
#     ec2.py launch
import os
import sys
import time

import botocore

import boto3

CONFIG_FILE = ".gnec2.cfg"

# Ubuntu
# https://help.ubuntu.com/community/EC2StartersGuide
# All us-east-1 EBS Backed
LUCID_32 = "ami-3e9b4957"
LUCID_64 = "ami-349b495d"
MAVERIK_32 = "ami-c012cea9"
MAVERIK_64 = "ami-c412cead"
NATTY_32 = "ami-1616ca7f"
NATTY_64 = "ami-e016ca89"
ONEIRIC_32 = "ami-e1aa7388"
ONEIRIC_64 = "ami-8baa73e2"
PRECISE_32 = "ami-b89842d1"
PRECISE_64 = "ami-3c994355"
TRUSTY_32 = "ami-134b0923"
TRUSTY_64 = "ami-d0ba0cb8"

# CentOS
# All us-east-1
CENTOS_52_32 = ""
CENTOS_52_64 = ""
CENTOS_54_32 = "ami-f8b35e91"
CENTOS_54_64 = "ami-ccb35ea5"
CENTOS_62_32 = "ami-5c4e9235"
CENTOS_62_64 = ""

DEFAULT_BASE = TRUSTY_64
DEFAULT_INSTANCE_TYPE = 't2.small'

GEONODE_LUCID_32 = ""
GEONODE_LUCID_64 = ""
GEONODE_MAVERIK_32 = ""
GEONODE_MAVERIK_64 = ""
GEONODE_NATTY_32 = ""
GEONODE_NATTY_64 = ""
GEONODE_ONEIRIC_32 = ""
GEONODE_ONEIRIC_64 = ""
GEONODE_PRECISE_32 = ""
GEONODE_PRECISE_64 = ""

DEFAULT_BASE_GEONODE = GEONODE_PRECISE_32

ALPHA_ELASTIC_IP = "54.235.204.189"


def wait_for_state(ec2, instance_id, state):
    assert state in ('pending', 'running', 'shutting-down',
                     'terminated', 'stopped')
    # Poll for 10 minutes for instance to transition to the specified state
    for i in range(120):
        for reservation in ec2.describe_instances(
                InstanceIds=[instance_id])['Reservations']:
            for instance in reservation['Instances']:
                if instance['InstanceId'] == instance_id and \
                   instance['State']['Name'] == state:
                    return instance
        time.sleep(5)


def writeconfig(config):
    # Writing our configuration file to CONFIG_FILE
    configfile = open(CONFIG_FILE, 'wb')
    config.write(configfile)
    configfile.close()


def readconfig(default_ami=None):
    config = configparser.RawConfigParser()

    # If there is no config file, let's write one.
    if not os.path.exists(CONFIG_FILE):
        config.add_section('ec2')
        if default_ami is None:
            config.set('ec2', 'AMI', DEFAULT_BASE)
        else:
            config.set('ec2', 'AMI', default_ami)
        config.set('ec2', 'INSTANCE', '')
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
    instance_id = config.get('ec2', 'INSTANCE')
    ec2 = boto3.client('ec2')
    try:
        allocation = ec2.allocate_address(Domain='vpc')
        response = ec2.associate_address(
            AllocationId=allocation['AllocationId'],
            InstanceId=instance_id,
            PublicIp=ALPHA_ELASTIC_IP)
        return response
    except botocore.exceptions.ClientError as e:
        print(e)
        return None


def launch():
    config = readconfig()
    ami = config.get('ec2', 'AMI')
    group_name = config.get('ec2', 'SECURITY_GROUP')
    key_name = 'geonode'
    key_path = config.get('ec2', 'KEY_PATH')
    instance_type = config.get('ec2', 'INSTANCE_TYPE')

    if config.has_option('ec2', 'HOST'):
        host = config.get('ec2', 'HOST')
        if host != "" and host is not None:
            print("There is already an instance launched")
            return

    ec2 = boto3.client('ec2')
    vpc_id = ec2.describe_vpcs().get('Vpcs', [{}])[0].get('VpcId', '')

    try:
        geonode_group = ec2.describe_security_groups(
            GroupNames=[group_name])['SecurityGroups'][0]
    except botocore.exceptions.ClientError:
        # Create the security group
        geonode_group = ec2.create_security_group(
            GroupName=group_name, Description='GeoNode rules.', VpcId=vpc_id)
        port_ranges = [
            (21, 21),  # Batch upload FTP
            (22, 22),  # SSH
            (80, 80),  # Apache
            (2300, 2400),  # Passive FTP
            (8000, 8001),  # Dev Django and Jetty
            (8021, 8021),  # Batch upload FTP
            (8080, 8080),  # Tomcat
        ]

        for from_port, to_port in port_ranges:
            ec2.authorize_security_group_ingress(
                GroupId=geonode_group['GroupId'],
                IpProtocol='tcp',
                FromPort=from_port,
                ToPort=to_port,
                CidrIp='0.0.0.0/0')

    try:
        key_pairs = ec2.describe_key_pairs(KeyNames=[key_name])['KeyPairs']
    except botocore.exceptions.ClientError:
        # Key is not likely not defined
        print("GeoNode file not found in server.")
        key_pairs = ec2.describe_key_pairs()['KeyPairs']

    key = key_pairs[0] if len(
        key_pairs) > 0 else ec2.create_key_pair(KeyName=key_name)
    reservation = ec2.run_instances(
        ImageId=ami,
        InstanceType=instance_type,
        KeyName=key['KeyName'],
        MaxCount=1,
        MinCount=1,
        SecurityGroupIds=[
            geonode_group['GroupId']])
    instance_id = [instance['InstanceId']
                   for instance in reservation['Instances']
                   if instance['ImageId'] == ami][0]

    print("Firing up instance...")
    instance = wait_for_state(ec2, instance_id, 'running')
    dns = instance['PublicDnsName']
    print(f"Instance running at {dns}")

    config.set('ec2', 'HOST', dns)
    config.set('ec2', 'INSTANCE', instance_id)
    writeconfig(config)

    print(f"ssh -i {key_path} ubuntu@{dns}")
    print("Terminate the instance via the web interface.")

    time.sleep(20)


def terminate():
    config = readconfig()
    instance_id = config.get('ec2', 'INSTANCE')

    ec2 = boto3.client('ec2')
    ec2.terminate_instances(InstanceIds=[instance_id])

    print("Terminating instance...")
    wait_for_state(ec2, instance_id, 'terminated')
    print("Instance terminated.")

    config.set('ec2', 'HOST', '')
    config.set('ec2', 'INSTANCE', '')
    configfile = open(CONFIG_FILE, 'wb')
    config.write(configfile)
    configfile.close()


if __name__ == '__main__':
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
        print(config.get('ec2', 'HOST'))
    elif sys.argv[1] == "key":
        config = readconfig()
        print(config.get('ec2', 'KEY_PATH'))
    else:
        print(f"Usage:\n    python {sys.argv[0]} launch_base\n     python {sys.argv[0]} launch_geonode\n    python {sys.argv[0]} terminate")
