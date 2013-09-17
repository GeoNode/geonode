.. _projects.setup:

Setting up your GeoNode project
===============================

This section will walk you through the steps necessary to set up your own GeoNode project. It assumes that you have installed GeoNode from the Ubuntu packages and that you have a working GeoNode site.

Setup steps
-----------

If you are working remotely, you should first connect to the machine that has your GeoNode installation. You will need to perform the following steps in a directory where you intend to keep your newly created project.

#. Activate GeoNode's Virtual Environment:

   .. code-block:: console

      $ source /var/lib/geonode/bin/activate

#. Create your GeoNode project from the template:

   .. code-block:: console

      $ django-admin.py startproject --template=https://github.com/GeoNode/geonode-project/zipball/master my_geonode
      $ cd my_geonode

#. Update your :file:`local_settings.py`. You will need to check the :file:`local_settings.py` that is included with the template project and be sure that it reflects your own local environment. You should pay particular attention to the Database settings especially if you intend to reuse the database that was set up with your base GeoNode installation.

#. Synchronize your database:

   .. code-block:: console

      $ python manage.py syncdb --all

#. Run the test server:

   .. code-block:: console

      $ python manage.py runserver

#. Visit your new GeoNode site at http://localhost:8000.

Source code revision control
----------------------------

It is recommended that you immediately put your new project under source code revision control. The GeoNode development team uses Git and GitHub and recommends that you do the same. If you do not already have a GitHub account, you can easily set one up. A full review of Git and distributed source code revision control systems is beyond the scope of this tutorial, but you may find the `Git Book`_ useful if you are not already familiar with these concepts.

.. _Git Book: http://git-scm.com/book

#. Create a new repository in GitHub. You should use the GitHub user interface to create a new repository for your new project.

   .. figure:: img/github_home.jpg

      *Creating a new GitHub Repository From GitHub's Homepage*

   .. figure:: img/create_repo.jpg

      *Specifying new GitHub Repository Parameters*

   .. figure:: img/new_repo.jpg

      *Your new Empty GitHub Repository*

#. Initialize your own repository:

   .. code-block:: console

      $ git init

#. Add the remote repository reference to your local git configuration:

   .. code-block:: console

      $ git remote add 

#. Add your project files to the repository:

   .. code-block:: console

      $ git add .

#. Commit your changes:

   .. code-block:: console

      $ git commit -am "Initial commit"

#. Push to the remote repository:

   .. code-block:: console

      $ git push origin master

Project structure
-----------------

Your GeoNode project will now be structured as depicted below::

    |-- README.rst
    |-- manage.py
    |-- my_geonode
    |   |-- __init__.py
    |   |-- settings.py
    |   |-- static
    |   |   |-- README
    |   |   |-- css
    |   |   |   |-- site_base.css
    |   |   |-- img
    |   |   |   |-- README
    |   |   |-- js
    |   |       |-- README
    |   |-- templates
    |   |   |-- site_base.html
    |   |   |-- site_index.html
    |   |-- urls.py
    |   |-- wsgi.py
    |-- setup.py

You can also view your project on GitHub.

   .. figure:: img/github_project.png

      *Viewing your project on GitHub*

Each of the key files in your project are described below.

manage.py
~~~~~~~~~

:file:`manage.py` is the main entry point for managing your project during
development. It allows running all the management commands from each app in your
project. When run with no arguments, it will list all of the management commands.

settings.py
~~~~~~~~~~~

:file:`settings.py` is the primary settings file for your project. It is quite
common to put all sensible defaults here and keep deployment specific configuration
in the :file:`local_settings.py` file. All of the possible settings values and
their meanings are detailed in the Django documentation.

A common paradigm for handing 'local settings' (and in other areas where some
python module may not be available) is:

  .. code-block: python
  
  try:
      from local_settings import *
  except:
      pass

This is not required and there are many other solutions to handling varying
deployment configuration requirements.

urls.py
~~~~~~~

:file:`urls.py` is where your application specific URL routes go. Additionally,
any `overrides` can be placed here, too.

wsgi.py
~~~~~~~

This is a generated file to make deploying your project to a WSGI server easier.
Unless there is very specific configuration you need, :file:`wsgi.py` can be
left alone.

setup.py
~~~~~~~~

There are several packaging options in python but a common approach is to place
your project metadata (version, author, etc.) and dependencies in :file:`setup.py`.

This is a large topic and not necessary to understand while getting started with
GeoNode development but will be important for larger projects and to make
development easier for other developers.

More: http://docs.python.org/2/distutils/setupscript.html

static
~~~~~~

The :file:`static` directory will contain your fixed resources: css, html, 
images, etc. Everything in this directory will be copied to the final media
directory (along with the `static` resources from other apps in your project).

templates
~~~~~~~~~

All of your projects templates go in the :file:`templates` directory. While
no organization is required for your project specific templates, when overriding
or replacing a template from another app, the path must be the same as the template
to be replaced.

Deploying your GeoNode Project
------------------------------

Now that your own project is set up, you will need to replace the existing default configuration with configuration for your own project in order to visit your new project site.

.. todo:: Needs details.

#. Update Apache configuration

#. Check GeoServer configuration

#. Check database configuration

Production Ready
----------------

While not a complete checklist, some changes should be made prior to deploying
to production.

* Ensure DEBUG=False in your effective `settings`.
* Change any admin passwords from any common defaults (i.e. admin/admin)
* Change the geoserver `master password <http://docs.geoserver.org/stable/en/user/webadmin/security/passwords.html#webadmin-sec-masterpasswordprovider>`_ from the default
* Ensure GeoServer is `ready <http://docs.geoserver.org/stable/en/user/production/index.html>`_.


Staying in sync with mainline GeoNode
-------------------------------------

One of the primary reasons to set up your own GeoNode project using this method is so that you can stay in sync with the mainline GeoNode as the core development team makes new releases. Your own project should not be adversely affected by these changes, but you will receive bug fixes and other improvements by staying in sync.

#. Upgrade GeoNode:

   .. code-block:: console

      $ apt-get update
      $ apt-get install geonode

#. Verify that your new project works with the upgraded GeoNode:

   .. code-block:: console

      $ python manage.py runserver

#. Navigate to http://localhost:8000.
