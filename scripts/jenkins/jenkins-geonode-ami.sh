#!/bin/bash
source ~/.bashrc
cd scripts/cloud/
#python ec2.py terminate
rm .gnec2.cfg
python ec2.py launch_base

host=$(python ec2.py host)
key=$(python ec2.py key)
echo $host
echo $key

cd $WORKSPACE/scripts/cloud/
fab -i $key -H ubuntu@$host build_geonode_ami

#python ec2.py terminate
