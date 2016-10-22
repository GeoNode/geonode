#
# spec file for package python-django-geoexplorer
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

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

%define pyname django-geoexplorer

Name:           python-%{pyname}
Version:        3.0.2.dev35dd99db
Release:        1
License:        GPL-2.0
Summary:        Use GeoExplorer in your django projects
Url:            http://suite.opengeo.org/opengeo-docs/geoexplorer/
Group:          Productivity/Scientific/Other
Source0:        %{pyname}-%{version}.zip
BuildRequires:  fdupes 
BuildRequires:  unzip
BuildRequires:  python-devel
BuildRequires:  python-distribute
BuildArchitectures: noarch
Provides:       %{pyname} = %{version}
BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%description
Use GeoExplorer in your django projects. GeoExplorer is a web application, based on the GeoExt framework, for composing and publishing maps. With GeoExplorer you can quickly assemble maps from GeoServer or any OGC Web Mapping Server (WMS) and integrate with hosted maps such as Google Maps and OpenStreetMap. You can also edit map styling information, embed the maps you compose in any web page, or output the maps in PDF format.

%prep
%setup -q -n %{pyname}-%{version}

%build

%install
rm -rf %{buildroot}

python setup.py install --prefix=%{_prefix} --root=%{buildroot} \
                                            --record-rpm=INSTALLED_FILES

%fdupes -s %{buildroot}

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
