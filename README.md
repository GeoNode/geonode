![GeoNode](https://raw.githubusercontent.com/GeoNode/documentation/master/about/img/geonode-logo_for_readme.gif "GeoNode")
![OSGeo Project](https://www.osgeo.cn/qgis/_static/images/osgeoproject.png)

Table of Contents
=================

- [Table of Contents](#table-of-contents)
  - [What is GeoNode?](#what-is-geonode)
  - [Try out GeoNode](#try-out-geonode)
  - [Quick Docker Start](#quick-docker-start)
  - [Learn GeoNode](#learn-geonode)
  - [Development](#development)
  - [Contributing](#contributing)
  - [Roadmap](#roadmap)
  - [Showcase](#showcase)
  - [Most useful links](#most-useful-links)
  - [Licensing](#licensing)

What is GeoNode?
----------------

GeoNode is a geospatial content management system, a platform for the
management and publication of geospatial data. It brings together mature
and stable open-source software projects under a consistent and
easy-to-use interface allowing non-specialized users to share data and
create interactive maps.

Data management tools built into GeoNode allow for integrated creation
of data, metadata, and map visualization. Each dataset in the system can
be shared publicly or restricted to allow access to only specific users.
Social features like user profiles and commenting and rating systems
allow for the development of communities around each platform to
facilitate the use, management, and quality control of the data the
GeoNode instance contains.

It is also designed to be a flexible platform that software developers
can extend, modify or integrate against to meet requirements in their
own applications.

Try out GeoNode
---------------

If you just want to try out GeoNode visit our official Demo online at:
[https://development.demo.geonode.org](https://development.demo.geonode.org). After your registration, you will be able
to test all basic functionalities like uploading layers, creation of
maps, editing metadata, styles, and much more. To get an overview what
GeoNode can do we recommend having a look at the [Users
Workshop](https://docs.geonode.org/en/master/usage/index.html).

Quick Docker Start
------------------

  ```bash
    python create-envfile.py
  ```
`create-envfile.py` accepts the following arguments:

- `--https`: Enable SSL. It's disabled by default
- `--env_type`: 
   - When set to `prod` `DEBUG` is disabled and the creation of a valid `SSL` is requested to Letsencrypt's ACME server
   - When set to `test`  `DEBUG` is disabled and a test `SSL` certificate is generated for local testing
   - When set to `dev`  `DEBUG` is enabled and no `SSL` certificate is generated
- `--hostname`: The URL that will serve GeoNode (`localhost` by default)
- `--email`: The administrator's email. Notice that a real email and valid SMPT configurations are required if  `--env_type` is set to `prod`. Letsencrypt uses email for issuing the SSL certificate 
- `--geonodepwd`: GeoNode's administrator password. A random value is set if left empty
- `--geoserverpwd`: GeoNode's administrator password. A random value is set if left empty
- `--pgpwd`: PostgreSQL's administrator password. A random value is set if left empty
- `--dbpwd`: GeoNode DB user role's password. A random value is set if left empty
- `--geodbpwd`: GeoNode data DB user role's password. A random value is set if left empty
- `--clientid`: Client id of Geoserver's GeoNode Oauth2 client. A random value is set if left empty
- `--clientsecret`: Client secret of Geoserver's GeoNode Oauth2 client. A random value is set if left empty

```bash
  docker compose build
  docker compose up -d
```

Learn GeoNode
-------------

After you´ve finished the setup process make yourself familiar with the
general usage and settings of your GeoNodes instance. - the [User
Training](https://docs.geonode.org/en/master/usage/index.html)
is going in depth into what we can do. - the [Administrators
Workshop](https://docs.geonode.org/en/master/admin/index.html)
will guide you to the most important parts regarding management commands
and configuration settings.

Development
-----------

GeoNode is a web-based GIS tool, and as such, in order to do development
on GeoNode itself or to integrate it into your own application, you
should be familiar with basic web development concepts as well as with
general GIS concepts.

For development, GeoNode can be run in a 'development environment'. In
contrast to a 'production environment' development differs as it uses
lightweight components to speed up things.

To get started visit the [Developer
workshop](https://docs.geonode.org/en/master/devel/index.html)
for a basic overview.

If you're planning to customize your GeoNode instance or to extend
its functionalities it's not advisable to change core files in any
case. In this case, it's common to setup a [GeoNode Project
Template](https://github.com/GeoNode/geonode-project).

Contributing
------------

GeoNode is an open source project and contributors are needed to keep
this project moving forward. Learn more on how to contribute on our
[Community
Bylaws](https://github.com/GeoNode/geonode/wiki/Community-Bylaws).

Roadmap
-------

GeoNode's development roadmap is documented in a series of GeoNode
Improvement Projects (GNIPS). They are documented at [GeoNode Wiki](https://github.com/GeoNode/geonode/wiki/GeoNode-Improvement-Proposals).

GNIPS are considered to be large undertakings that will add a large
number of features to the project. As such they are the topic of
community discussion and guidance. The community discusses these on the
developer mailing list: http://lists.osgeo.org/pipermail/geonode-devel/

Showcase
--------

A handful of other Open Source projects extend GeoNode’s functionality
by tapping into the re-usability of Django applications. Visit our
gallery to see how the community uses GeoNode: [GeoNode
Showcase](https://geonode.org/gallery/).

The development community is very supportive of new projects and
contributes ideas and guidance for newcomers.

Most useful links
-----------------


**General**

- Project homepage: https://geonode.org
- Repository: https://github.com/GeoNode/geonode
- Official Demos: https://demo.geonode.org
- GeoNode Wiki: https://github.com/GeoNode/geonode/wiki
- Issue tracker: https://github.com/GeoNode/geonode-project/issues

    In case of sensitive bugs like security vulnerabilities, please
    contact a GeoNode Core Developer directly instead of using an issue
    tracker. We value your effort to improve the security and privacy of
    this project!

**Related projects**

- GeoNode Project: https://github.com/GeoNode/geonode-project
- GeoNode at Docker: https://hub.docker.com/u/geonode
- GeoNode OSGeo-Live: https://live.osgeo.org/en/


**Support**

- User Mailing List: https://lists.osgeo.org/cgi-bin/mailman/listinfo/geonode-users
- Developer Mailing List: https://lists.osgeo.org/cgi-bin/mailman/listinfo/geonode-devel
- Gitter Chat: https://gitter.im/GeoNode/general


Licensing
---------

GeoNode is Copyright 2018 Open Source Geospatial Foundation (OSGeo).

GeoNode is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version. GeoNode is distributed in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with GeoNode. If not, see http://www.gnu.org/licenses.
