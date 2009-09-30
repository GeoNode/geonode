=========
 GeoNode
=========

Install
=======

::

  git clone git@github.com:GeoNode/GeoNode.git
  cd GeoNode
  . bin/activate
  python bootstrap.py
  paver build
  django-admin.py syncdb --settings=geonode.settings 
  paster serve shared/dev-paste.ini