#
# spec file for package python-geonode
#
# Copyright (c) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

%define _webappconfdir /etc/apache2/conf.d/
%define _htdocsdir /srv/www/htdocs/

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

%define pyname geonode

Name:           python-%{pyname}
Version:        2.0b1
Release:        1
License:        GPL-3.0
Summary:        GeoNode is a platform for the management and publication of geospatial data
Url:            http://geonode.org/
Group:          Productivity/Scientific/Other
Source0:        %{pyname}-%{version}.tar.gz
BuildRequires:  fdupes 
BuildRequires:  python-devel
BuildRequires:  python-distribute
BuildRequires:  python-django
# native dependencies
Requires:	python
Requires:	python-imaging
Requires:	python-lxml
# python dependencies
Requires:	python-gsconfig
Requires:	python-owslib
Requires:	python-django
Requires:	python-httplib2
# Django Apps
Requires:	python-pinax-theme-bootstrap
Requires:	python-pinax-theme-bootstrap-account
Requires:	python-django-user-accounts
Requires:	python-django-pagination
Requires:	python-django-jsonfield
Requires:	python-django-friendly-tag-loader
Requires:	python-django-taggit
Requires:	python-django-taggit-templatetags
Requires:	python-django-geoexplorer
Requires:	python-django-relationships
Requires:	python-django-notification
Requires:	python-django-announcements
Requires:	python-django-activity-stream
Requires:	python-django-request
Requires:	python-user-messages
Requires:	python-geonode-avatar
Requires:	python-dialogos
Requires:	python-agon-ratings
Requires:	python-South
# catalogue
Requires:	python-Shapely
Requires:	python-pycsw
# setup
Requires:	python-Paver
# sample and test data / metadata

# testing

# translation

Provides:       %{pyname} = %{version}

BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%description
GeoNode is a platform for the management and publication of geospatial data. 
It brings together mature and stable open-source software projects under a 
consistent and easy-to-use interface allowing users, with little training, 
to quickly and easily share data and create interactive maps. GeoNode provides 
a cost-effective and scalable tool for developing information management systems.

%prep
%setup -q -n %{pyname}-%{version}
rm geonode/static/libs/datatables/images/Sorting*

%build

%install
rm -rf %{buildroot}

python setup.py install --prefix=%{_prefix} --root=%{buildroot} \
                                            --record-rpm=INSTALLED_FILES

%fdupes -s %{buildroot}

%post 

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
