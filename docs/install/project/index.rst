.. _geonode-project:

===============
GeoNode Project
===============

Overview
========

The following steps will guide you to a new setup of GeoNode Project. All guides will first install and configure the system to run it in ``DEBUG`` mode (also known as ``DEVELOPMENT`` mode) and then by configuring an HTTPD server to serve GeoNode through the standard ``HTTP`` (``80``) port.

Those guides **are not** meant to be used on a production system. There will be dedicated chapters that will show you some *hints* to optimize GeoNode for a production-ready machine. In any case, we strongly suggest to task an experienced *DevOp* or *System Administrator* before exposing your server to the ``WEB``.

Ubuntu 18.04
============

This part of the documentation describes the complete setup process for GeoNode on an Ubuntu 18.04 64-bit clean environment (Desktop or Server). All examples use shell commands that you must enter on a local terminal or a remote shell.
- If you have a graphical desktop environment you can open the terminal application after login;
- if you are working on a remote server the provider or sysadmin should has given you access through an ssh client.

.. _install_dep_proj:

Install the dependencies
^^^^^^^^^^^^^^^^^^^^^^^^

In this section, we are going to install all the basic packages and tools needed for a complete GeoNode installation. To follow this guide, a piece of basic knowledge about Ubuntu Server configuration and working with a shell is required. This guide uses ``vim`` as the editor; fill free to use ``nano``, ``gedit`` or others.

Upgrade system packages
.......................

Check that your system is already up-to-date with the repository running the following commands:

.. code-block:: shell

   sudo apt update
   sudo apt upgrade


Create a Dedicated User
.......................

In the following steps a User named ``geonode`` is used: to run installation commands the user must be in the ``sudo`` group.

Create User ``geonode`` **if not present**:

.. code-block:: shell

  # Follow the prompts to set the new user's information.
  # It is fine to accept the defaults to leave all of this information blank.
  sudo adduser geonode

  # The following command adds the user geonode to group sudo
  sudo usermod -aG sudo geonode

  # make sure the newly created user is allowed to login by ssh
  # (out of the scope of this documentation) and switch to User geonode
  su geonode

Packages Installation
.....................

First, we are going to install all the **system packages** needed for the GeoNode setup.

.. code-block:: shell

  # Install packages from GeoNode core
  sudo apt install -y python-gdal gdal-bin
  sudo apt install -y python-pip python-dev python-virtualenv
  sudo apt install -y libxml2 libxml2-dev gettext
  sudo apt install -y libxslt1-dev libjpeg-dev libpng-dev libpq-dev libgdal-dev libgdal20
  sudo apt install -y software-properties-common build-essential
  sudo apt install -y git unzip gcc zlib1g-dev libgeos-dev libproj-dev
  sudo apt install -y sqlite3 spatialite-bin libsqlite3-mod-spatialite

  # Install Openjdk
  sudo -i apt update
  sudo apt install openjdk-8-jdk-headless default-jdk-headless -y
  sudo update-java-alternatives --jre-headless --jre --set java-1.8.0-openjdk-amd64

  sudo apt update -y
  sudo apt upgrade -y
  sudo apt autoremove -y
  sudo apt autoclean -y
  sudo apt purge -y
  sudo apt clean -y

  # Install Packages for Virtual environment management
  sudo apt install -y virtualenv virtualenvwrapper
  
  # Install text editor
  sudo apt install -y vim

Geonode Project Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Geonode project is the proper way to run a customized installation of Geonode. The repository of geonode-project contains a minimal set of files following the structure of a django-project. Geonode itself will be installed as a requirement of your project.
Inside the project structure is possible to extend, replace or modify all geonode componentse (e.g. css and other static files, templates, models..) and even register new django apps **without touching the original Geonode code**.


.. note:: You can call your geonode project whatever you like following the naming conventions for python packages (generally lower case with underscores (_). In the examples below, replace ``my_geonode`` with whatever you would like to name your project.

See also the `README <https://github.com/GeoNode/geonode-project/blob/master/README.rst>`_ file on geonode-project repository

First of all we need to prepare a new Python Virtual Environment

Prepare the environment

.. code-block:: shell

  sudo mkdir -p /opt/geonode_custom/
  sudo usermod -a -G www-data geonode
  sudo chown -Rf geonode:www-data /opt/geonode_custom/
  sudo chmod -Rf 775 /opt/geonode_custom/

Clone the source code

.. code-block:: shell

  cd /opt/geonode_custom/
  git clone https://github.com/GeoNode/geonode-project.git

Make an instance out of the ``Django Template``

.. note:: We will call our instance ``my_geonode``. You can change the name at your convenience.

.. code-block:: shell

  mkvirtualenv my_geonode
  pip install Django==1.11.21
  django-admin startproject --template=./geonode-project -e py,rst,json,yml,ini,env,sample -n Dockerfile my_geonode

  # Install the Python packages
  cd /opt/geonode_custom/my_geonode
  pip install -r requirements.txt --upgrade --no-cache --no-cache-dir
  pip install -e . --upgrade --no-cache --no-cache-dir

  # Install GDAL Utilities for Python
  GDAL_VERSION=`gdal-config --version`; \
    PYGDAL_VERSION="$(pip install pygdal==$GDAL_VERSION 2>&1 | grep -oP '(?<=: )(.*)(?=\))' | grep -oh $GDAL_VERSION\.[0-9])"; \
    pip install pygdal==$PYGDAL_VERSION

Run GeoNode Project for the first time in DEBUG Mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::

  Be sure you have successfully completed all the steps of the section :ref:`install_dep_proj`.

This command will run both GeoNode and GeoServer locally after having prepared the SQLite database. The server will start in ``DEBUG`` (or ``DEVELOPMENT``) mode, and it will start the following services:

#. GeoNode on ``http://localhost:8000/``
#. GeoServer on ``http://localhost:8080/geoserver/``

This modality is beneficial to debug issues and/or develop new features, but it cannot be used on a production system.

.. code-block:: shell

  # Prepare the GeoNode SQLite database (the first time only)
  paver setup
  paver sync

.. note::

  In case you want to start again from a clean situation, just run

  .. code:: shell

    paver reset_hard

.. warning:: This will blow up completely your ``local_settings``, delete the SQLlite database and remove the GeoServer data dir.

.. code-block:: shell

  # Run the server in DEBUG mode
  paver start

Once the server has finished the initialization and prints on the console the sentence ``GeoNode is now available.``, you can open a browser and go to::

  http://localhost:8000/

Sign-in with::

  user: admin
  password: admin

From now on, everything already said for GeoNode Core (please refer to the section :ref:`configure_dbs_core` and following), applies to a
GeoNode Project.

**Be careful** to use the **new** paths and names everywhere:

* Everytime you'll find the keyword ``goenode``, you'll need to use your geonode custom name instead (in this example ``my_geonode``).

* Everytime you'll find paths pointing to ``/opt/geonode/``, you'll need to update them to point to your custom project instead (in this example ``/opt/geonode_custom/my_geonode``).

Docker
======

.. warning:: Before moving with this section, you should have read and clearly understood the ``INSTALLATION > GeoNode Core`` sections, and in particular the ``Docker`` one. Everything said for the GeoNode Core Vanilla applies here too, except that the Docker container names will be slightly different. As an instance if you named your project ``my_geonode``, your containers will be called:

  .. code-block:: shell

    'django4my_geonode' instead of 'django4geonode' and so on...

Deploy an instance of a geonode-project Django template 2.10.x with Docker on localhost
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Prepare the environment

.. code-block:: shell

  sudo mkdir -p /opt/geonode_custom/
  sudo usermod -a -G www-data geonode
  sudo chown -Rf geonode:www-data /opt/geonode_custom/
  sudo chmod -Rf 775 /opt/geonode_custom/

Clone the source code

.. code-block:: shell

  cd /opt/geonode_custom/
  git clone https://github.com/GeoNode/geonode-project.git

Make an instance out of the ``Django Template``

.. note:: We will call our instance ``my_geonode``. You can change the name at your convenience.

.. code-block:: shell

  mkvirtualenv my_geonode
  pip install Django==1.11.21
  django-admin startproject --template=./geonode-project -e py,rst,json,yml,ini,env,sample -n Dockerfile my_geonode
  cd /opt/geonode_custom/my_geonode

Modify the code and the templates and rebuild the Docker Containers

.. code-block:: shell

  docker-compose -f docker-compose.yml -f docker-compose.override.yml build --no-cache

Finally, run the containers

.. code-block:: shell

  docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

Deploy an instance of a geonode-project Django template 2.10.x with Docker on a domain
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: We will use ``www.example.org`` as an example. You can change the name at your convenience.

Stop the containers

.. code-block:: shell

  cd /opt/geonode_custom/my_geonode

  docker-compose -f docker-compose.yml -f docker-compose.override.yml stop

Edit the ``ENV`` override file in order to deploy on ``www.example.org``

.. code-block:: shell

  # Make a copy of docker-compose.override.yml
  cp docker-compose.override.yml docker-compose.override.example-org.yml

Replace everywhere ``localhost`` with ``www.example.org``

.. code-block:: shell

  vim docker-compose.override.example-org.yml

.. code-block:: shell

  # e.g.: :%s/localhost/www.example.org/g

  version: '2.2'
  services:

    django:
      build: .
      # Loading the app is defined here to allow for
      # autoreload on changes it is mounted on top of the
      # old copy that docker added when creating the image
      volumes:
        - '.:/usr/src/my_geonode'
      environment:
        - DEBUG=False
        - GEONODE_LB_HOST_IP=www.example.org
        - GEONODE_LB_PORT=80
        - SITEURL=http://www.example.org/
        - ALLOWED_HOSTS=['www.example.org', ]
        - GEOSERVER_PUBLIC_LOCATION=http://www.example.org/geoserver/
        - GEOSERVER_WEB_UI_LOCATION=http://www.example.org/geoserver/

    geoserver:
      environment:
        - GEONODE_LB_HOST_IP=localhost
        - GEONODE_LB_PORT=80
    #    - NGINX_BASE_URL=


.. note:: It is possible to override here even more variables to customize the GeoNode instance. See the ``GeoNode Settings`` section in order to get a list of the available options.

Run the containers in daemon mode

.. code-block:: shell

  docker-compose -f docker-compose.yml -f docker-compose.override.example-org.yml up --build -d

.. _install-with-ansible:

Ansible
=======
`Ansible <https://www.ansible.com/>`__ is an open-source software provisioning, configuration management, and application-deployment tool for IT infrastructure. It is written in `Python <https://www.python.org/>`_ and
allows users to manage `nodes` (computers) over SSH. Configuration files are written in `YAML <https://en.wikipedia.org/wiki/YAML>`_, a simple, human-readable, data serialization format.

Ansible can be used for automating the manual installation process of GeoNode. In case you're new to GeoNode we suggest first to get an Overview of  :doc:`/install/core/index` components.


Installing Ansible
^^^^^^^^^^^^^^^^^^

Before you install `Ansible` make sure you have Python 2 (version 2.7) or Python 3 (versions 3.5 and higher) 
on the controlling machine, you will also need an SSH client. Most Linux distributions
come with an SSH client preinstalled. 

.. note:: For further installation instruction, please visit the `official installation documentation <http://docs.ansible.com/ansible/intro_installation.html>`_.


Test your Setup
^^^^^^^^^^^^^^^

After you've installed Ansible, you can test your setup by use of the following command

.. code:: 

        ansible localhost -m ping

You should get the following output::

        localhost | success >> {
        "changed": false,
        "ping": "pong"
    }

Ansible Hosts file
^^^^^^^^^^^^^^^^^^

Ansible keeps information about the managed nodes in the `inventory` or `hosts file`.
Edit or create the hosts file with your favorite editor::

    vim /etc/ansible/hosts

This file should contain a list of nodes for Ansible to manage. Nodes can be referred to
either with IP or hostname. The syntax is the following::

    192.168.1.50
    aserver.example.org
    bserver.example.org

For targeting several servers you can group them like::

    mail.example.com

    [webservers]
    foo.example.com
    bar.example.com

    [dbservers]
    one.example.com
    two.example.com
    three.example.com

    [geonode]
    mygeonode.org

Public Key access
^^^^^^^^^^^^^^^^^

To avoid having to type your user's password to connect to the nodes over and over, using
SSH keys is recommended. To setup Public Key SSH access to the nodes. First, create a key pair::

    ssh-keygen

And follow the instructions on the screen. A new key pair will be generated and
placed inside the `.ssh` folder in your user's home directory.

All you need to do now is copy the public key (id_rsa.pub) into the `authorized_keys`
file on the node you want to manage, inside the user's home directory. For example,
if you want to be able to connect to mygeonode.org as user `geo` edit the
/home/geo/.ssh/authorized_keys file on the remote machine and add the content
of your public key inside the file.

For more information on how to set up SSH keys in Ubuntu
refer to `this <https://help.ubuntu.com/community/SSH/OpenSSH/Keys>`_ document.

Connect to managed nodes
^^^^^^^^^^^^^^^^^^^^^^^^

Now that SSH access to the managed nodes is in place for all the nodes inside the Ansible
`inventory` (hosts file), we can run our first command::

    ansible geonode -m ping -u geo

.. note::

        change `geo` with the username to use for SSH login

The output will be similar to this::

    ansible all -m ping -u geo
    84.33.2.70 | success >> {
        "changed": false,
        "ping": "pong"
    }

We asked Ansible to connect to the machine in our `Inventory` grouped under `[geonode] as user `geo`
and run the `module` ping (modules are Ansible's units of work).
As you can see by the output, Ansible successfully connected to the remote machine
and executed the module `ping`.

Ad hoc commands and playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ansible integrates two basic concepts of running commands:
An ad-hoc command is something that you might type in to do something immediately,
but don’t want to save for later. One example of an ad-hoc command is the ping command we just ran. We typed in the
command line and ran it interactively.

For more information on ad-hoc command refer to the `adhoc documentation section <https://docs.ansible.com/ansible/intro_adhoc.html>`_.

Playbooks are Ansible’s configuration, deployment and orchestration language.
In contrast to ad hoc commands, Playbooks can declare configurations, but they can also orchestrate steps of any manual ordered process. 

For more information on playbooks refer to the `playbook documentation section <https://docs.ansible.com/ansible/latest/user_guide/playbooks.html>`_.

In the following, we will provide you an example on how to setup a playbook for installing GeoNode on a server.


Installing GeoNode project by use of a playbook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, we have to install the  underlying steps for installing geonode provided by the official GeoNode role::

   $ ansible-galaxy install geonode.geonode


.. note:: Roles are ways of automatically loading certain vars_files, tasks, and handlers based on a known file structure. Grouping content by roles also allows easy sharing of roles with other users.

See: https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html

To find out how these install tasks are defined, we suggest having a look a the `different tasks <https://github.com/GeoNode/ansible-geonode/tree/master/tasks>`_ of role geonode.

Setup a playbook
^^^^^^^^^^^^^^^^

After installation of the role geonode.geonode we will now create a simple playbook which defines what should happen. 
Create the playbook file where it suits best for you. For example in your home folder::

  mkdir ~/geonode_ansible
  vim ~/geonode_ansible/install_geonode.yml

with following content

.. code-block:: shell

    ---
    - name: Provision a GeoNode into Production
      hosts: geonode 
      remote_user: geo
      vars:
        app_name: my_geonode
        server_name: 84.33.2.70
        deploy_user: ubuntu
        code_repository: https://github.com/GeoNode/geonode-project.git
        branch_name: master
        virtualenv_dir: /home/geo/.venvs
        site_url: http://mygeonode.org/
        geoserver_url: https://build.geo-solutions.it/geonode/geoserver/latest/geoserver-2.15.2.war
        pg_max_connections: 100
        pg_shared_buffers: 128MB
        tomcat_xms: 1024M
        tomcat_xmx: 2048M
        nginx_client_max_body_size: 400M
      gather_facts: False
      pre_tasks:
        - name: Install python for Ansible
          become: yes
          become_user: root
          raw: test -e /usr/bin/python || (apt -y update && apt install -y python-minimal)
      roles:
         - { role: GeoNode.geonode }


The playbook is composed of different parts. The most important are:

The **hosts part** specifies to which hosts in the Inventory this playbook applies and
how to connect to them. This points to your hosts file with grouped servers under `[geonode]` as 
explained before. (Most likely you will only have one node under group geonode)

The **vars** section mainly describe configured settings. Please visit the geonode ansible readme regarding `role variables <https://github.com/GeoNode/ansible-geonode#role-variables>`_.

**Roles** points to our installed geonode role which has all needed installation tasks.



Run the Playbook
^^^^^^^^^^^^^^^^

Now that we have created our Playbook, we can execute it with::

    ansible-playbook ~/geonode_ansible/install_geonode.yml -u geo

    PLAY [84.33.2.70] *************************************************************

    GATHERING FACTS ***************************************************************
    ok: [84.33.2.70]

    ...

Ansible should connect to the host specified in the hosts section grouped by `[geonode]` and run the install tasks one by one. If something goes wrong Ansible will fail fast and stop the installation process.
When successfully finished you should be able to see GeoNode's welcome screen at your `site_url`.

This concludes our brief tutorial on Ansible. For a more thorough introduction
refer to the `official documentation <https://docs.ansible.com/>`_.

Also, take a look at the `Ansible examples repository <https://github.com/ansible/ansible-examples>`_
or a set of Playbooks showing common techniques.
