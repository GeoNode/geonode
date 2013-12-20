#!/bin/bash
source ~/.bashrc
PYENV_HOME=$HOME/.pyenv-aws
source $PYENV_HOME/bin/activate

# Install build & test tools
pip install fabric
pip install boto
 
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

fab -i $key -H ubuntu@$host set_temp_hosts_entry:server_name=demo.geonode.org

fab -i $key -H ubuntu@$host install_sample_data

fab -i $key -H ubuntu@$host geonode_updateip:server_name=demo.geonode.org

fab -i $key -H ubuntu@$host update_geoserver_geonode_auth
fab -i $key -H ubuntu@$host remove_temp_hosts_entry 
python ec2.py set_alpha_ip
#python ec2.py terminate

