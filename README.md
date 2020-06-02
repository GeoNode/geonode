![GeoNode](https://raw.githubusercontent.com/GeoNode/documentation/master/about/img/geonode-logo_for_readme.gif "GeoNode")
![OSGeo Project](https://www.osgeo.cn/qgis/_static/images/osgeoproject.png)

Table of Contents
=================

-  [What is GeoNode?](#what-is-geonode)
-  [Try out GeoNode](#try-out-geonode)
-  [Install](#install)
-  [Learn GeoNode](#learn-geonode)
-  [Development](#development)
-  [Contributing](#contributing)
-  [Roadmap](#roadmap)
-  [Showcase](#showcase)
-  [Most useful links](#most-useful-links)
-  [Licensing](#licensing)

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
http://master.demo.geonode.org. After your registration you will be able
to test all basic functionalities like uploading layers, creation of
maps, editing metadata, styles and much more. To get an overview what
GeoNode can do we recommend to have a look at the [Users
Workshop](http://docs.geonode.org/en/2.10/usage/index.html).

Install
-------

    The latest official release is 2.10!

GeoNode can be setup in different ways, flavors and plattforms. If
you´re planning to do development or install for production please visit
the offical GeoNode installation documentation:

- [Docker](http://docs.geonode.org/en/2.10/install/core/index.html#docker)
- [Ubuntu 18.04](http://docs.geonode.org/en/2.10/install/core/index.html#ubuntu-18-04)

Learn GeoNode
-------------

After you´ve finished the setup process make yourself familiar with the
general usage and settings of your GeoNodes instance. - the [User
Training](http://docs.geonode.org/en/2.10/usage/index.html)
is going in depth into what we can do. - the [Administrators
Workshop](http://docs.geonode.org/en/2.10/admin/index.html)
will guide you to the most important parts regarding management commands
and configuration settings.

Development
-----------

GeoNode is a web based GIS tool, and as such, in order to do development
on GeoNode itself or to integrate it into your own application, you
should be familiar with basic web development concepts as well as with
general GIS concepts.

For development GeoNode can be run in a 'development environment'. In
contrast to a 'production environment' development differs as it uses
lightweight components to speed up things.

To get you started have a look at the [Install
instructions](#install) which cover all what is needed to run GeoNode
for development. Further visit the the [Developer
workshop](http://docs.geonode.org/en/2.10/devel/index.html)
for a basic overview.

If you're planning of customizing your GeoNode instance, or to extend
it's functionalities it's not advisable to change core files in any
case. In this case it's common to use setup a [GeoNode Project
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

GNIPS are considered to be large undertakings which will add a large
amount of features to the project. As such they are the topic of
community dicussion and guidance. The community discusses these on the
developer mailing list: http://lists.osgeo.org/pipermail/geonode-devel/

Showcase
--------

A handful of other Open Source projects extend GeoNode’s functionality
by tapping into the re-usability of Django applications. Visit our
gallery to see how the community uses GeoNode: [GeoNode
Showcase](http://geonode.org/gallery/).

The development community is very supportive of new projects and
contributes ideas and guidance for newcomers.

Most useful links
-----------------


**General**

- Project homepage: https://geonode.org
- Repository: https://github.com/GeoNode/geonode
- Offical Demo: http://master.demo.geonode.org
- GeoNode Wiki: https://github.com/GeoNode/geonode/wiki
- Issue tracker: https://github.com/GeoNode/geonode-project/issues

    In case of sensitive bugs like security vulnerabilities, please
    contact a GeoNode Core Developer directly instead of using issue
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

**HDN Customizations**
Alterações separadas por data:

01/04/2020
- Criação do Campo Ano de Criação do Conjunto de Dados;
- Criação do Campo Escala;
- Criação do Campo Link VINDE;
- Criação do Campo INDE.

02/04/2020
- Criação do Campo Frequência de Manutenção (Manter a lista);
- Criação do Campo Licença (Manter a lista);
- Criação do Campo Lista de Autores (Manter a lista);
- Criação do Campo Lista de Restrições.
- Criação do Campo Embrapa_Keywords

03/04/2020
- Mantido o Campo Pontos de Contato com uma única escolha;
- Customização de opções do Campo Frequência de Manutenção;

07/04/2020
- Customização conteúdo do Campo "Licença";
- Customização no Campo Regiões.

08/04/2020
- Ajustes no formulário de metadados;
- Correções de erros nos documentos e no metadata_detail.

09/04/2020
- Tradução dos campos;
- Ajustes no campo Language;

14/04/2020
- Alocação dos campos do formulário ao novo painel de metadados;
- Ajustes no template do formulário para alocação dos campos Ano de Criação do Conjunto de Dados,
	Autores, Escala, Link VINDE, Embrapa_Keywords, INDE.
- Custmizações nos textos explicativos.

15/04/2020
- Correção de bugs na hora do submit da camada;

24/04/2020
- Alterações no views.py da aplicação 'layers', alocado o campo embrapa_keywords com o método "add()";

27/04/2020
- Alteração no campo embrapa_keywords, alterado de MultipleChoiceField para TagField;

04/05/2020
- Alterações no banco de dados, renomeado o nome da tabela "base_resourcebase_embrapa_keywords" para "base_keywords_embrapa";
- Ajustes na consistência dos dados, remoção de espaços entre outros aspectos.

05/05/2020
- Ajustes nos dados da tabela "base_resourcebase";

20/05/2020
- Tratamento dos dados "Finalidade", "Autores" e "Declaração da Qualidade do Dado";

29/05/2020
- Criação do Campo Unidade e Customização do Campo Finalidade (transformando-o de TextField para ChoiceField);

01/06/2020
- Início da chamada para as api's INTEGRO e IDEARE para o Campo Finalidade;


