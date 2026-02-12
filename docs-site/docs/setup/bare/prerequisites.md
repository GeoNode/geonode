# Prerequisites

### Overview
The following steps will guide you to a fresh setup of `GeoNode`.

All guides will first install and configure the system to run it in `DEBUG` mode (also known as `DEVELOPMENT` mode) and then by configuring an HTTPD server to serve GeoNode through the standard HTTP (80) port.

!!! Warning
    Those guides are not meant to be used on a production system. There will be dedicated chapters that will show you some hints to optimize GeoNode for a production-ready machine. In any case, we strongly suggest to task an experienced DevOp or System Administrator before exposing your server to the WEB.

### Ubuntu 24.04

This part of the documentation describes the complete setup process for GeoNode on an `Ubuntu 24.04 LTS` 64-bit clean environment (Desktop or Server).

All examples use shell commands that you must enter on a local terminal or a remote shell.

- If you have a graphical desktop environment you can open the terminal application after login;
- if you are working on a remote server the provider or sysadmin should has given you access through an ssh client.

### Install the dependencies

In this section, we are going to install all the basic packages and tools needed for a complete GeoNode installation.

!!! Warning 
    To follow this guide, a basic knowledge about Ubuntu Server configuration and working with a shell is required.

!!! Note
    This guide uses `vim` as the editor; fill free to use `nano`, `gedit` or others.

#### Upgrade system packages

Check that your system is already up-to-date with the repository running the following commands:

```bash
sudo apt update -y
sudo apt install -y software-properties-common
sudo add-apt-repository universe
```

#### Packages Installation

!!! Note
    You don’t need to install the system packages if you want to run the project using Docker

We will use `example.org` as fictitious Domain Name.

First, we are going to install all the system packages needed for the GeoNode setup. Login to the target machine and execute the following commands:

```bash
# Install packages from GeoNode core
sudo apt install -y --allow-downgrades \
  build-essential \
  python3-gdal=3.8.4+dfsg-3ubuntu3 gdal-bin=3.8.4+dfsg-3ubuntu3 libgdal-dev=3.8.4+dfsg-3ubuntu3 \
  python3-all-dev python3.12-dev python3.12-venv \
  libxml2 libxml2-dev gettext libmemcached-dev zlib1g-dev \
  libxslt1-dev libjpeg-dev libpng-dev libpq-dev \
  software-properties-common \
  git unzip gcc zlib1g-dev libgeos-dev libproj-dev \
  sqlite3 spatialite-bin libsqlite3-mod-spatialite libsqlite3-dev \
  wget

# Install Openjdk
sudo apt install openjdk-11-jdk-headless default-jdk-headless -y

# Verify GDAL version
gdalinfo --version
  $> GDAL 3.8.4, released 2024/02/08

# Verify Python version
python3.12 --version
  $> Python 3.12.3

which python3.12
  $> /usr/bin/python3.12

# Verify Java version
java -version
  $> openjdk version "21.0.9" 2025-10-21

# Install VIM
sudo apt install -y vim

# Cleanup the packages
sudo apt update -y; sudo apt autoremove --purge
```

After above setup, you can proceed with the main GeoNode installation.