# GeoFence Advanced Features

## GeoFence Rules Management and Tutorials

- [This tutorial](http://docs.geoserver.org/latest/en/user/community/geofence-server/tutorial.html) shows how to install and configure the Geofence Internal Server plug-in. It shows how to create rules in two ways: using the GUI and REST methods.
- GeoFence Rules can be created / updated / deleted through a REST API, accessible only by a GeoServer Admin user. You can find more details on how the GeoFence REST API works [here](https://github.com/geoserver/geofence/wiki/REST-API).

## GeoFence Rules Storage Configuration

By default GeoFence is configured to use a filesystem based DB stored on the GeoServer Data Dir `<GEOSERVER_DATA_DIR>/geofence`.

- It is possible also to configure GeoFence in order to use an external PostgreSQL / PostGIS Database. For more details please refer to the official GeoFence documentation [here](https://github.com/geoserver/geofence/wiki/GeoFence-configuration).

1. Add `Java Libraries` to `GeoServer`

    ```bash
    wget --no-check-certificate "https://maven.geo-solutions.it/org/hibernatespatial/hibernate-spatial-postgis/1.1.3.2/hibernate-spatial-postgis-1.1.3.2.jar" -O hibernate-spatial-postgis-1.1.3.2.jar
    wget --no-check-certificate "https://repo1.maven.org/maven2/org/postgis/postgis-jdbc/1.3.3/postgis-jdbc-1.3.3.jar" -O postgis-jdbc-1.3.3.jar

    cp hibernate-spatial-postgis-1.1.3.2.jar <GEOSERVER_WEBAPP_DIR>/WEB-INF/lib
    cp postgis-jdbc-1.3.3.jar <GEOSERVER_WEBAPP_DIR>/WEB-INF/lib

    restart geoserver
    ```

2. Either create a DB with the updated schema [here](https://github.com/geoserver/geofence/blob/master/doc/setup/sql/002_create_schema_postgres.sql) or enable the `hbm2ddl` auto creation through the configuration file, see step `3`

    !!! Note
        Notice that `update` also creates the tables if they do not exist. In production, however, I would suggest changing it to `validate`

    ```bash
    # If you want to create a new DB for GeoFence
    sudo -u postgres createdb -O geonode geofence
    sudo -u postgres psql -d geofence -c 'CREATE EXTENSION postgis;'
    sudo -u postgres psql -d geofence -c 'GRANT ALL ON geometry_columns TO PUBLIC;'
    sudo -u postgres psql -d geofence -c 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'
    sudo -u postgres psql -d geofence -c 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO geonode;'
    ```

3. Add configuration similar to `geofence-datasource-ovr.properties` sample below, if loaded as GeoServer extension

    **`<GEOSERVER_DATA_DIR>/geofence/geofence-datasource-ovr.properties`**

    ```bash
    # /* (c) 2019 Open Source Geospatial Foundation - all rights reserved
    #  * This code is licensed under the GPL 2.0 license, available at the root
    #  * application directory.
    #  */
    #
    geofenceVendorAdapter.databasePlatform=org.hibernate.spatial.dialect.postgis.PostgisDialect
    geofenceDataSource.driverClassName=org.postgresql.Driver
    geofenceDataSource.url=jdbc:postgresql://localhost:5432/geofence
    geofenceDataSource.username=postgres
    geofenceDataSource.password=postgres
    geofenceEntityManagerFactory.jpaPropertyMap[hibernate.default_schema]=public

    geofenceDataSource.testOnBorrow=true
    geofenceDataSource.validationQuery=SELECT 1
    geofenceEntityManagerFactory.jpaPropertyMap[hibernate.testOnBorrow]=true
    geofenceEntityManagerFactory.jpaPropertyMap[hibernate.validationQuery]=SELECT 1

    geofenceDataSource.removeAbandoned=true
    geofenceDataSource.removeAbandonedTimeout=60
    geofenceDataSource.connectionProperties=ApplicationName=GeoFence;

    geofenceEntityManagerFactory.jpaPropertyMap[hibernate.hbm2ddl.auto]=update
    geofenceEntityManagerFactory.jpaPropertyMap[javax.persistence.validation.mode]=none
    geofenceEntityManagerFactory.jpaPropertyMap[hibernate.validator.apply_to_ddl]=false
    geofenceEntityManagerFactory.jpaPropertyMap[hibernate.validator.autoregister_listeners]=false
    ```
