<div align="right">
<a href="http://travis-ci.org/GeoNode/geonode"><img src="https://secure.travis-ci.org/GeoNode/geonode.png"></a> <a href="https://coveralls.io/github/GeoNode/geonode?branch=master"><img src="https://coveralls.io/repos/github/GeoNode/geonode/badge.svg?branch=master"></a> <a href="https://codecov.io/gh/GeoNode/geonode)
[![travis-ci.org"><img src="https://codecov.io/gh/GeoNode/geonode/branch/master/graph/badge.svg"></a> <a href="https://www.gnu.org/licenses/gpl-3.0.en.html"><img src="docs/img/gpl.png" alt="GPL badge"></a>
</div>
<img src="docs/img/geonode-logo_for_readme.gif" alt="GeoNode Logo" width="450px"/>
<div style="text-align:center"><hr><b>A powerful yet easy to use web-based application and platform for deploying spatial data infrastructures (SDI).</b><hr></div>

# Table of Contents
- [What is GeoNode?](#what-is-geonode)
- [Try out GeoNode](#try-out-geonode)
- [Install](#install)
- [Learn GeoNode](#learn-geonode)
- [Development](#development)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [Showcase](#showcase)
- [Most useful links](#most-useful-links)
- [Licensing](#licensing)

## What is GeoNode?
GeoNode is a geospatial content management system, a platform for the management and publication of geospatial data. It brings together mature and stable open-source software projects under a consistent and easy-to-use interface allowing non-specialized users to share data and create interactive maps.

Data management tools built into GeoNode allow for integrated creation of data, metadata, and map visualization. Each dataset in the system can be shared publicly or restricted to allow access to only specific users. Social features like user profiles and commenting and rating systems allow for the development of communities around each platform to facilitate the use, management, and quality control of the data the GeoNode instance contains.

It is also designed to be a flexible platform that software developers can extend, modify or integrate against to meet requirements in their own applications.

## Try out GeoNode
If you just want to try out GeoNode visit our official Demo online at: http://master.demo.geonode.org. After your registration you will be able to test all basic functionalities like uploading layers, creation of maps, editing metadata, styles and much more. To get an overview what GeoNode can do we recommend to have a look at the [Users Workshop](http://docs.geonode.org/en/master/tutorials/users/index.html).

## Install
> The latest official release is 2.8!

GeoNode can be setup in different ways, flavors and plattforms. If you´re planning to do development or install for production please visit 
the offical GeoNode installation documentation:
- [Docker](http://docs.geonode.org/en/master/tutorials/install_and_admin/running_docker/index.html)
- [VM Setup with VirtualBox](http://docs.geonode.org/en/master/tutorials/install_and_admin/vm_setup_virtualbox.html)
- [Ubuntu 16.04](http://docs.geonode.org/en/master/tutorials/install_and_admin/geonode_install/index.html) 
- [CentOS 7](http://docs.geonode.org/en/master/tutorials/install_and_admin/setup_on_centos/index.html)
- [Windows Binary Installer](http://docs.geonode.org/en/master/tutorials/install_and_admin/win_bin_install/win_binary_installer.html)
- [Installation by deb packages](http://geonode.org)

## Learn GeoNode

After you´ve finished the setup process make yourself familiar with the general usage and settings of your GeoNodes instance. 
- the [User Training](http://docs.geonode.org/en/master/tutorials/users/index.html) is going in depth into what we can do.
- the [Administrators Workshop](http://docs.geonode.org/en/master/tutorials/admin/index.html) will guide you to the most important parts regarding management commands and configuration settings.

## Development

<img src="docs/img/opensource.png">

GeoNode is a web based GIS tool, and as such, in order to do development on GeoNode itself or to integrate it into your own application, you should be familiar with basic web development concepts as well as with general GIS concepts. 

For development GeoNode can be run in a 'development environment'. In contrast to  a 'production environment' development differs as it uses lightweight components to speed up things. 

To get you started have a look at the [Install instructions](#install) which cover all what is needed to run GeoNode for development. Further visit the the [Developer workshop](http://docs.geonode.org/en/master/tutorials/devel/index.html) for a basic overview.

If you´re planning of customizing your GeoNode instance, or to extend it´s functionalities it´s not advisable to change core files in any case. In this case it´s common to use setup a [GeoNode Project Template](https://github.com/GeoNode/geonode-project).


## Contributing

GeoNode is an open source project and contributors are needed to keep this project moving forward. Learn more on how to contribute on our [Community Bylaws](https://github.com/GeoNode/geonode/wiki/Community-Bylaws).

## Roadmap

GeoNode's development roadmap is documented in a series of GeoNode Improvement Projects (GNIPS). They are documented at GeoNode Wiki: https://github.com/GeoNode/geonode/wiki/GeoNode-Improvement-Proposals. 

GNIPS are considered to be large undertakings which will add a large amount of features to the project. As such they are the topic of community dicussion and guidance. The community discusses these on the developer mailing list: http://lists.osgeo.org/pipermail/geonode-devel/ 

## Showcase

A handful of other Open Source projects extend GeoNode’s functionality by tapping into the re-usability of Django applications. Visit our gallery to see how the community uses GeoNode: [GeoNode Showcase](http://geonode.org/gallery/).

The development community is very supportive of new projects and contributes ideas and guidance for newcomers.

## Most useful links

<table>
  <tr>
    <th colspan="2" width="660px" align="left">General</th>
  </tr>
  
  <tr>
    <td>Project homepage</td>
    <td>https://geonode.org</td>
  </tr>
  <tr>
    <td>Repository</td>
    <td>https://github.com/GeoNode/geonode</td>
  </tr>
  <tr>
    <td>Offical Demo</td>
    <td>http://master.demo.geonode.org</td>
  </tr>
  <tr>
    <td>GeoNode Wiki</td>
    <td>https://github.com/GeoNode/geonode/wiki</td>
  </tr>
  <tr>
    <td>Issue tracker *</td>
    <td>https://github.com/GeoNode/geonode-project/issues</td>
  </tr>
</table>
<table>
  <tr>
    <th colspan="2" width="660px" align="left">Related projects</th>
  </tr>
  <tr>
    <td>GeoNode Project</td>
    <td>https://github.com/GeoNode/geonode-project</td>
  </tr>
  <tr>
    <td>GeoNode at Docker</td>
    <td>https://hub.docker.com/u/geonode</td>
  </tr>
  <tr>
    <td>GeoNode OSGeo-Live</td>
    <td>https://live.osgeo.org/en/</td>
  </tr>
</table>

<table>
  <tr>
    <th colspan="2" width="660px" align="left">Support</th>
  </tr>
  <tr>
    <td>User Mailing List</td>
    <td>https://lists.osgeo.org/cgi-bin/mailman/listinfo/geonode-users</td>
  </tr>
  <tr>
    <td>Developer Mailing List</td>
    <td>https://lists.osgeo.org/cgi-bin/mailman/listinfo/geonode-devel</td>
  </tr>
  <tr>
    <td>Gitter Chat</td>
    <td>https://gitter.im/GeoNode/general</td>
  </tr>
</table>

> In case of sensitive bugs like security vulnerabilities, please contact a GeoNode Core Developer directly instead of using issue tracker. We value your effort to improve the security and privacy of this project!


## Licensing

GeoNode is Copyright 2018 Open Source Geospatial Foundation (OSGeo).

GeoNode is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version. 
GeoNode is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with GeoNode.  If not, see http://www.gnu.org/licenses.
