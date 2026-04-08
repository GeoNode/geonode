# Prerequisites

### System requirements

Before proceed to the Docker installation for the vanilla GeoNode or GeoNode project, install the required repositories / libraries:

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt install curl python3.12-venv git
```

### Docker Setup for Ubuntu 24.04

To prepare an Ubuntu 24.04 machine with Docker and Docker Compose you can follow the steps below:

```bash
# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker APT repository
UBUNTU_CODENAME=$(lsb_release -cs)

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $UBUNTU_CODENAME stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine + Docker Compose plugin
sudo apt-get update -y

sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Allow your user to run Docker without sudo
sudo usermod -aG docker $USER

# Refresh your group membership in the current shell
newgrp docker
```

### Prepare the environment

Afterward, set up the working directory, and assign the appropriate permissions to it. If you are deploying a `vanilla GeoNode`, the working directory is commonly named `geonode`. For a `GeoNode project`, the directory name depends on the specific project configuration. In this guide, the working directory is named `my_geonode`.

For production environments, you can deploy GeoNode on `/opt` folder:

```bash
sudo adduser geonode
sudo usermod -a -G www-data geonode

# in case of vanilla GeoNode
sudo mkdir -p /opt/geonode/
sudo chown -Rf geonode:www-data /opt/geonode/
sudo chmod -Rf 775 /opt/geonode/

# in case of GeoNode project
sudo mkdir -p /opt/my_geonode
sudo chown -Rf geonode:www-data /opt/my_geonode/
sudo chmod -Rf 775 /opt/my_geonode/
```

However, GeoNode can be installed in a subdirectory within the home directory e.g `/home/<organization>/geonode`. This is the approach followed in this guide.