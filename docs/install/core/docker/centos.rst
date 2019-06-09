Install the Docker and docker-compose packages on a CentOS host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Docker Setup (First time only)
..............................

.. warning:: The `centos-extras` repository must be enabled

.. code-block:: shell

  sudo yum install -y yum-utils device-mapper-persistent-data lvm2

  sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

  sudo yum install docker-ce docker-ce-cli containerd.io

  sudo systemctl start docker

  sudo usermod -aG docker geonode
  su geonode