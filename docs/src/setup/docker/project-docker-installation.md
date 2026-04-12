# GeoNode project Docker installation

In this section, we are going to list the steps needed to deploy a GeoNode project with Docker.

### Clone the source code

```bash
mkdir -p ~/geonode_projects
cd ~/geonode_projects
git clone https://github.com/GeoNode/geonode-project.git
```

This will clone the `master` branch. You will have to checkout the desidered branch or tag. As an example, if you want to generate a propject for GeoNode 4.4.3 you will docker.

```bash
cd geonode-project
git checkout -b 4.4.3
```

### Generate a custom GeoNode project

This is the most important part for the GeoNode project installation. Before building the project, you have to generate custom GeoNode project intance, using the `GeoNode Template`

!!! Note
    We will call our instance my_geonode. You can change the name at your convenience.

```bash
# Create and activate a Python environment called my_geonode_env
mkdir path/to/.venvs
python3 -m venv /path/to/.venvs/my_geonode_env
source /path/to/.venvs/my_geonode_env/bin/activate

# Install Django in the activated Python environment
pip install Django==5.2.8

cd ~/geonode_projects
django-admin startproject --template=./geonode-project -e py,sh,md,rst,json,yml,ini,env,sample,properties -n monitoring-cron -n Dockerfile my_geonode
```

### Prepare the .env file

Navigate to `my_geonode` folder and create the .env file by using the `create-envfile` script:

```bash
cd my_geonode
python create-envfile.py
```

Depending on the project's requirements, align the `.env` varialbes accordingly.
!!! Note
    For more information about the accepted arguments please see the section [Prepare the .env file](../vanilla-docker-installation) from the Vanilla GeoNode installation.

Before building the project, check the created `.env` variable and align the arguments according to your requirements.

### Build and run

Finally, to build and run GeoNode run the following:

```bash
docker compose build --no-cache
docker compose up -d
```

If the build is successful, you will be able to navigate on GeoNode project at `http://localhost`

### Investigate the logs

If something went wrong, you can check the logs of the containers from `my_geonode` root folder by running the following commands:

```bash
# GeoNode Container
docker-compose logs -f django

# GeoServer Container
docker-compose logs -f geoserver

# DB Container
docker-compose logs -f db

# NGINX Container
docker-compose logs -f geonode
```

### Login as an administrator on GeoNode

To connect on the GeoNode project as administrator, use the credentials from the `.env` file:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD={geonodepwd}
```