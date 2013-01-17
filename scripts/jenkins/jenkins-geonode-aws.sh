#!/bin/bash
source ~/.bashrc
cd scripts/cloud/
python ec2.py terminate
rm .gnec2.cfg
python ec2.py launch_base

host=$(python ec2.py host)
key=$(python ec2.py key)
echo $host
echo $key

cd $WORKSPACE/scripts/cloud/
fab -i $key -H ubuntu@$host deploy_geonode_testing_package

fab -i $key -H ubuntu@$host install_sample_data

python ec2.py set_alpha_ip
fab -i $key -H ubuntu@$host geonode_updateip:server_name=alpha.dev.geonode.org
#python ec2.py terminate
