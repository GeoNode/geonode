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

# Set an internal hosts record so when updateip calls updatelayers we dont have problems
ip=`wget -qO- http://instance-data/latest/meta-data/public-ipv4`
su - -c 'echo "$ip alpha.dev.geonode.org" >> /etc/hosts'

fab -i $key -H ubuntu@$host geonode_updateip:server_name=alpha.dev.geonode.org

python ec2.py set_alpha_ip
#python ec2.py terminate
