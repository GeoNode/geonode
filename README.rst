=========
 GeoNode
=========

Install
=======

::

  git clone git@github.com:GeoNode/GeoNode.git
  cd GeoNode
  python bootstrap.py
  paver build
  django-admin --settings=geonode.settings syncdb
  paster serve shared/dev-paste.ini