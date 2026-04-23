# Loading Data into GeoNode

There are situations where it is not possible or not convenient to use the `Upload Form` to add new datasets to GeoNode through the web interface. For instance:

- The dataset is too big to be uploaded through a web interface.
- Importing data from a mass storage system programmatically.
- Importing tables from a database.

This section walks through the various options available to load data into GeoNode from GeoServer, from the command line, or programmatically.

!!! Warning
    Some parts of this section are adapted from the [GeoServer](https://geoserver.geo-solutions.it/edu/en) project and training documentation.

## Management Command `importlayers`

The `geonode.geoserver` Django app includes two management commands that you can use to load data into GeoNode.

Both of them can be invoked by using the `manage.py` script.

First, let us look at the `--help` option of the `importlayers` management command in order to inspect all command options and features.

Run:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py importlayers --help
```

!!! Note
    If you enabled `local_settings.py`, the command becomes:

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.local_settings python manage.py importlayers --help
    ```

This produces output similar to the following:

```bash
usage: manage.py importlayers [-h] [-hh HOST] [-u USERNAME] [-p PASSWORD]
                              [--version] [-v {0,1,2,3}] [--settings SETTINGS]
                              [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                              [--force-color] [--skip-checks]
                              [path [path ...]]

Brings files from a local directory, including subfolders, into a GeoNode site.
The datasets are added to the Django database, the GeoServer configuration, and the
pycsw metadata index. At this moment only files of type Esri Shapefile (.shp) and GeoTiff (.tif) are supported.
In order to perform the import, GeoNode must be up and running.

positional arguments:
path                  path [path...]

optional arguments:
-h, --help            show this help message and exit
--version             show program's version number and exit
-v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
--settings SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
--pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
-hh HOST, --host HOST
                        Geonode host url
-u USERNAME, --username USERNAME
                        Geonode username
-p PASSWORD, --password PASSWORD
                        Geonode password
```

While most options are self-explanatory, a few of the key ones are worth reviewing:

- `-hh` identifies the GeoNode server where you want to upload the datasets. The default value is `http://localhost:8000`.
- `-u` identifies the username for the login. The default value is `admin`.
- `-p` identifies the password for the login. The default value is `admin`.

The import datasets management command is invoked by specifying options as described above and giving the path to a directory that contains multiple files. For this exercise, use the default set of testing datasets that ship with GeoNode. You can replace this path with a directory containing your own shapefiles.

```bash
First let's run the GeoNode server:
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py runserver

Then let's import the files:
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py importlayers /home/user/.virtualenvs/geonode/lib/python3.8/site-packages/gisdata/data/good/vector/
```

This command produces output similar to the following:

```bash
san_andres_y_providencia_poi.shp: 201
san_andres_y_providencia_location.shp: 201
san_andres_y_providencia_administrative.shp: 201
san_andres_y_providencia_coastline.shp: 201
san_andres_y_providencia_highway.shp: 201
single_point.shp: 201
san_andres_y_providencia_water.shp: 201
san_andres_y_providencia_natural.shp: 201

1.7456605294117646 seconds per Dataset

Output data: {
    "success": [
        "san_andres_y_providencia_poi.shp",
        "san_andres_y_providencia_location.shp",
        "san_andres_y_providencia_administrative.shp",
        "san_andres_y_providencia_coastline.shp",
        "san_andres_y_providencia_highway.shp",
        "single_point.shp",
        "san_andres_y_providencia_water.shp",
        "san_andres_y_providencia_natural.shp"
    ],
    "errors": []
}
```

As output, the command prints:

```bash
layer_name: status code for each Layer

upload_time spent of each Dataset

A json with the representation of the Datasets uploaded or with some errors.
```

The status code is the response returned by GeoNode. For example, `201` means that the dataset has been uploaded correctly.

If you encounter errors while running this command, check the GeoNode logs for more information.

## Management Command `updatelayers`

While it is possible to import datasets directly from your server filesystem into GeoNode, you may already have an existing GeoServer with data in it, or you may want to configure data from a GeoServer that is not directly supported by file upload.

GeoServer supports a wide range of data formats and database connections. Some of them may not be supported as GeoNode upload formats. You can add them to GeoNode by following the procedure below.

GeoServer supports four types of data: `Raster`, `Vector`, `Databases`, and `Cascaded`.

For a list of supported formats for each type of data, consult the following pages:

- [GeoServer vector data formats](https://docs.geoserver.org/latest/en/user/data/vector/index.html)
- [GeoServer raster data formats](https://docs.geoserver.org/latest/en/user/data/raster/index.html)
- [GeoServer database data formats](https://docs.geoserver.org/latest/en/user/data/database/index.html)
- [GeoServer cascaded data formats](https://docs.geoserver.org/latest/en/user/data/cascaded/index.html)

!!! Note
    Some raster or vector formats, or some database types, require specific plugins in GeoServer in order to be used. Consult the GeoServer documentation for more information.

## Data from a PostGIS database

Let us walk through an example of configuring a new PostGIS database in GeoServer and then configuring those datasets in GeoNode.

First, visit the GeoServer administration interface on your server. This is usually on port `8080` and is available at `http://localhost:8080/geoserver/web/`.

1. Login with the superuser credentials you set up when you first configured your GeoNode instance.

    Once you are logged in to the GeoServer Admin interface, you should see the following:

    ![](img/geoserver_admin.png){ align=center }

    !!! Note
        The number of stores, datasets, and workspaces may be different depending on what you already have configured in GeoServer.

2. Select the `Stores` option in the left-hand menu, then choose `Add new Store`. The following screen is displayed:

    ![](img/geoserver_new_store.png){ align=center }

3. Select the PostGIS store type to create a connection to your existing database. On the next screen, enter the parameters required to connect to your PostGIS database and adapt them as needed for your own setup.

    ![](img/geoserver_postgis_params.png){ align=center }

    !!! Note
        If you are unsure about any of the settings, leave them at their default values.

4. The next screen lets you configure the datasets in your database. This will differ depending on the datasets in your database.

    ![](img/geoserver_publish_layers.png){ align=center }

5. Select the `Publish` button for one of the datasets. The next screen is displayed, where you can enter metadata for that dataset. Since this metadata is managed in GeoNode, you can leave it unchanged for now.

    ![](img/geoserver_layer_params.png){ align=center }

6. The values that *must* be specified are the Declared SRS. You must also select the `Compute from Data` and `Compute from native bounds` links after the SRS is specified.

    ![](img/geoserver_srs.png){ align=center }

    ![](img/geoserver_srs_2.png){ align=center }

7. Click save and this dataset is then configured for use in GeoServer.

    ![](img/geoserver_layers.png){ align=center }

8. The next step is to configure these datasets in GeoNode. The `updatelayers` management command can be used for this purpose. As with `importlayers`, it is useful to look at the command line options for this command by passing the `--help` option.

    Run:

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py updatelayers --help
    ```

    !!! Note
        If you enabled `local_settings.py`, the command becomes:

        ```bash
        DJANGO_SETTINGS_MODULE=geonode.local_settings python manage.py updatelayers --help
        ```

    This produces output similar to the following:

    ```bash
    usage: manage.py updatelayers [-h] [--version] [-v {0,1,2,3}]
                                [--settings SETTINGS] [--pythonpath PYTHONPATH]
                                [--traceback] [--no-color] [-i]
                                [--skip-unadvertised]
                                [--skip-geonode-registered] [--remove-deleted]
                                [-u USER] [-f FILTER] [-s STORE] [-w WORKSPACE]
                                [-p PERMISSIONS]

    Update the GeoNode application with data from GeoServer

    optional arguments:
    -h, --help            show this help message and exit
    --version             show program's version number and exit
    -v {0,1,2,3}, --verbosity {0,1,2,3}
                            Verbosity level; 0=minimal output, 1=normal output,
                            2=verbose output, 3=very verbose output
    --settings SETTINGS   The Python path to a settings module, e.g.
                            "myproject.settings.main". If this isn't provided, the
                            DJANGO_SETTINGS_MODULE environment variable will be
                            used.
    --pythonpath PYTHONPATH
                            A directory to add to the Python path, e.g.
                            "/home/djangoprojects/myproject".
    --traceback           Raise on CommandError exceptions
    --no-color            Don't colorize the command output.
    -i, --ignore-errors   Stop after any errors are encountered.
    --skip-unadvertised   Skip processing unadvertised datasets from GeoServer.
    --skip-geonode-registered
                            Just process GeoServer datasets still not registered
                            in GeoNode.
    --remove-deleted      Remove GeoNode datasets that have been deleted from
                            GeoServer.
    -u USER, --user USER  Name of the user account which should own the imported
                            datasets
    -f FILTER, --filter FILTER
                            Only update data for datasets that match the given
                            filter
    -s STORE, --store STORE
                            Only update data for datasets in the given GeoServer
                            store name
    -w WORKSPACE, --workspace WORKSPACE
                            Only update data on the specified workspace
    -p PERMISSIONS, --permissions PERMISSIONS
                            Permissions to apply to each dataset
    ```

    The update procedure includes the following steps:

    - The process fetches from GeoServer the relevant WMS layers, whether all layers or filtered by store or workspace.
    - If a filter is defined, the GeoServer layers are filtered.
    - For each layer, a GeoNode dataset is created based on the metadata registered on GeoServer, such as title, abstract, and bounds.
    - New layers are added and existing layers are replaced, unless the `--skip-geonode-registered` option is used.
    - GeoNode layers added in previous runs of the update process that are no longer available in GeoServer are removed if the `--remove-deleted` option is set.

    !!! Warning
        One of `--workspace` or `--store` must always be specified if you want to ingest datasets belonging to a specific `Workspace`. For example, in order to ingest the datasets present in the `geonode` workspace, you need to specify the option `-w geonode`.

9. Let us ingest the dataset `geonode:_1_SARMIENTO_ENERO_2018` from the `geonode` workspace.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py updatelayers -w geonode -f _1_SARMIENTO_ENERO_2018
    ```

    ```bash
    Inspecting the available Datasets in GeoServer ...
    Found 1 Datasets, starting processing
    /usr/local/lib/python2.7/site-packages/owslib/iso.py:117: FutureWarning: the .identification and .serviceidentification properties will merge into .identification being a list of properties.  This is currently implemented in .identificationinfo.  Please see https://github.com/geopython/OWSLib/issues/38 for more information
    FutureWarning)
    /usr/local/lib/python2.7/site-packages/owslib/iso.py:495: FutureWarning: The .keywords and .keywords2 properties will merge into the .keywords property in the future, with .keywords becoming a list of MD_Keywords instances. This is currently implemented in .keywords2. Please see https://github.com/geopython/OWSLib/issues/301 for more information
    FutureWarning)
    Content-Type: text/html; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    Subject: [master.demo.geonode.org] A new Dataset has been uploaded
    From: webmaster@localhost
    To: mapadeldelito@chubut.gov.ar
    Reply-To: webmaster@localhost
    Date: Tue, 08 Oct 2019 12:26:17 -0000
    Message-ID: <20191008122617.28801.94967@d3cf85425231>


    <body>
    You have received the following notice from master.demo.geonode.org:
    <p>

    The user <i><a href="http://master.demo.geonode.org/people/profile/admin">admin</a></i> uploaded the following Dataset:<br/>
    <strong>_1_SARMIENTO_ENERO_2018</strong><br/>
    You can visit the Dataset's detail page here: http://master.demo.geonode.org/Datasets/geonode:_1_SARMIENTO_ENERO_2018

    </p>
    <p>
    To change how you receive notifications, please go to http://master.demo.geonode.org
    </p>
    </body>

    -------------------------------------------------------------------------------
    Content-Type: text/html; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    Subject: [master.demo.geonode.org] A new Dataset has been uploaded
    From: webmaster@localhost
    To: giacomo8vinci@gmail.com
    Reply-To: webmaster@localhost
    Date: Tue, 08 Oct 2019 12:26:17 -0000
    Message-ID: <20191008122617.28801.53784@d3cf85425231>


    <body>
    You have received the following notice from master.demo.geonode.org:
    <p>

    The user <i><a href="http://master.demo.geonode.org/people/profile/admin">admin</a></i> uploaded the following Dataset:<br/>
    <strong>_1_SARMIENTO_ENERO_2018</strong><br/>
    You can visit the Dataset's detail page here: http://master.demo.geonode.org/Datasets/geonode:_1_SARMIENTO_ENERO_2018

    </p>
    <p>
    To change how you receive notifications, please go to http://master.demo.geonode.org
    </p>
    </body>

    -------------------------------------------------------------------------------
    Content-Type: text/html; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    Subject: [master.demo.geonode.org] A new Dataset has been uploaded
    From: webmaster@localhost
    To: fmgagliano@gmail.com
    Reply-To: webmaster@localhost
    Date: Tue, 08 Oct 2019 12:26:17 -0000
    Message-ID: <20191008122617.28801.26265@d3cf85425231>


    <body>
    You have received the following notice from master.demo.geonode.org:
    <p>

    The user <i><a href="http://master.demo.geonode.org/people/profile/admin">admin</a></i> uploaded the following Dataset:<br/>
    <strong>_1_SARMIENTO_ENERO_2018</strong><br/>
    You can visit the Dataset's detail page here: http://master.demo.geonode.org/Datasets/geonode:_1_SARMIENTO_ENERO_2018

    </p>
    <p>
    To change how you receive notifications, please go to http://master.demo.geonode.org
    </p>
    </body>

    -------------------------------------------------------------------------------
    Found geoserver resource for this Dataset: _1_SARMIENTO_ENERO_2018
    ... Creating Default Resource Links for Layer [geonode:_1_SARMIENTO_ENERO_2018]
    -- Resource Links[Prune old links]...
    -- Resource Links[Prune old links]...done!
    -- Resource Links[Compute parameters for the new links]...
    -- Resource Links[Create Raw Data download link]...
    -- Resource Links[Create Raw Data download link]...done!
    -- Resource Links[Set download links for WMS, WCS or WFS and KML]...
    -- Resource Links[Set download links for WMS, WCS or WFS and KML]...done!
    -- Resource Links[Legend link]...
    -- Resource Links[Legend link]...done!
    -- Resource Links[Thumbnail link]...
    -- Resource Links[Thumbnail link]...done!
    -- Resource Links[OWS Links]...
    -- Resource Links[OWS Links]...done!
    Content-Type: text/html; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    Subject: [master.demo.geonode.org] A Dataset has been updated
    From: webmaster@localhost
    To: mapadeldelito@chubut.gov.ar
    Reply-To: webmaster@localhost
    Date: Tue, 08 Oct 2019 12:26:20 -0000
    Message-ID: <20191008122620.28801.81598@d3cf85425231>


    <body>
    You have received the following notice from master.demo.geonode.org:
    <p>

    The following Dataset was updated:<br/>
    <strong>_1_SARMIENTO_ENERO_2018</strong>, owned by <i><a href="http://master.demo.geonode.org/people/profile/admin">admin</a></i><br/>
    You can visit the Dataset's detail page here: http://master.demo.geonode.org/Datasets/geonode:_1_SARMIENTO_ENERO_2018

    </p>
    <p>
    To change how you receive notifications, please go to http://master.demo.geonode.org
    </p>
    </body>

    -------------------------------------------------------------------------------
    Content-Type: text/html; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    Subject: [master.demo.geonode.org] A Dataset has been updated
    From: webmaster@localhost
    To: giacomo8vinci@gmail.com
    Reply-To: webmaster@localhost
    Date: Tue, 08 Oct 2019 12:26:20 -0000
    Message-ID: <20191008122620.28801.93778@d3cf85425231>


    <body>
    You have received the following notice from master.demo.geonode.org:
    <p>

    The following Dataset was updated:<br/>
    <strong>_1_SARMIENTO_ENERO_2018</strong>, owned by <i><a href="http://master.demo.geonode.org/people/profile/admin">admin</a></i><br/>
    You can visit the Dataset's detail page here: http://master.demo.geonode.org/Datasets/geonode:_1_SARMIENTO_ENERO_2018

    </p>
    <p>
    To change how you receive notifications, please go to http://master.demo.geonode.org
    </p>
    </body>

    -------------------------------------------------------------------------------
    Content-Type: text/html; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    Subject: [master.demo.geonode.org] A Dataset has been updated
    From: webmaster@localhost
    To: fmgagliano@gmail.com
    Reply-To: webmaster@localhost
    Date: Tue, 08 Oct 2019 12:26:20 -0000
    Message-ID: <20191008122620.28801.58585@d3cf85425231>


    <body>
    You have received the following notice from master.demo.geonode.org:
    <p>

    The following Dataset was updated:<br/>
    <strong>_1_SARMIENTO_ENERO_2018</strong>, owned by <i><a href="http://master.demo.geonode.org/people/profile/admin">admin</a></i><br/>
    You can visit the Dataset's detail page here: http://master.demo.geonode.org/Datasets/geonode:_1_SARMIENTO_ENERO_2018

    </p>
    <p>
    To change how you receive notifications, please go to http://master.demo.geonode.org
    </p>
    </body>

    -------------------------------------------------------------------------------
    Found geoserver resource for this Dataset: _1_SARMIENTO_ENERO_2018
    /usr/local/lib/python2.7/site-packages/geoserver/style.py:80: FutureWarning: The behavior of this method will change in future versions.  Use specific 'len(elem)' or 'elem is not None' test instead.
    if not user_style:
    /usr/local/lib/python2.7/site-packages/geoserver/style.py:84: FutureWarning: The behavior of this method will change in future versions.  Use specific 'len(elem)' or 'elem is not None' test instead.
    if user_style:
    ... Creating Default Resource Links for Layer [geonode:_1_SARMIENTO_ENERO_2018]
    -- Resource Links[Prune old links]...
    -- Resource Links[Prune old links]...done!
    -- Resource Links[Compute parameters for the new links]...
    -- Resource Links[Create Raw Data download link]...
    -- Resource Links[Create Raw Data download link]...done!
    -- Resource Links[Set download links for WMS, WCS or WFS and KML]...
    -- Resource Links[Set download links for WMS, WCS or WFS and KML]...done!
    -- Resource Links[Legend link]...
    -- Resource Links[Legend link]...done!
    -- Resource Links[Thumbnail link]...
    -- Resource Links[Thumbnail link]...done!
    -- Resource Links[OWS Links]...
    -- Resource Links[OWS Links]...done!
    [created] Layer _1_SARMIENTO_ENERO_2018 (1/1)


    Finished processing 1 Datasets in 5.0 seconds.

    1 Created Datasets
    0 Updated Datasets
    0 Failed Datasets
    5.000000 seconds per Dataset
    ```

!!! Note
    If you do not specify the `-f` option, the datasets that already exist in GeoNode are simply updated and the configuration is synchronized between GeoServer and GeoNode.

!!! Warning
    When updating **from** GeoServer, the configuration on GeoNode is changed.
