# Theming your GeoNode Project

There are a range of options available to you if you want to change the default look and feel of your GeoNode project.

## Logos and graphics

GeoNode intentionally does not include a large number of graphics files in its interface.
This keeps page loading time to a minimum and makes for a more responsive interface.
That said, you are free to customize your GeoNode interface by simply changing the default logo, or by adding your own images and graphics to deliver a GeoNode experience the way you envision it.

Your GeoNode project has a directory already set up for storing your own images at `<my_geonode>/static/img`.
You should place any image files that you intend to use for your project in this directory.

Let us walk through an example of the steps necessary to change the default logo.

1. Change to the `img` directory:

    ```bash
    $ cd <my_geonode>/static/img
    ```

2. If you have not already done so, obtain your logo image. The URL below is just an example, so you need to change this URL to match the location of your file or copy it to this location:

    ```bash
    $ wget https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Service_mark.svg/500px-Service_mark.svg.png
    $ wget https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Wikimapia_logo_without_label.svg/426px-Wikimapia_logo_without_label.svg.png -O logo.png
    ```

3. Create the snippets directory:

    ```bash
    $ cd ../../..
    $ mkdir <my_geonode>/templates/geonode-mapstore-client/snippets
    $ cd <my_geonode>/templates/geonode-mapstore-client/snippets
    ```

4. Create a new HTML file named `brand_navbar.html`.

    ```bash
    $ sudo vi brand_navbar.html
    ```

    ```css
    {% extends "geonode-mapstore-client/snippets/brand_navbar.html" %}
    {% load static %}
    {% block extra_style %}
    <style>
     #gn-brand-navbar {
       background: transparent url("/static/img/500px-Service_mark.svg.png") no-repeat;
       background-size: 300px 70px;
       background-position: left center;
       background-position-x: 100px;
     }
    </style>
    {% endblock %}
    {% block logo_src %}
    {% static 'img/logo.png' %}
    {% endblock %}
    ```

5. Restart your GeoNode project and look at the page in your browser:

    ```bash
    $ cd /home/geonode
    $ sudo rm -Rf geonode/geonode/static_root/*
    $ cd my_geonode
    $ python manage.py collectstatic
    $ sudo service apache2 restart
    ```

    !!! Note
        It is a good practice to clean up the `static_folder` and the browser cache before reloading in order to be sure that the changes have been correctly taken and displayed on the screen.

Visit your site at `http://localhost/` or the remote URL for your site.

![](img/logo_override.png){ align=center }
/// caption
*Custom logo*
///

In the following sections you will learn how to customize this header to make it look the way you want.

!!! Note
    You should commit these changes to your repository as you progress through this section, and get into the habit of committing early and often so that you and others can track your project on GitHub.
    Making many atomic commits and staying in sync with a remote repository makes it easier to collaborate with others on your project.

## Cascading Style Sheets

In the last section you already learned how to override GeoNode’s default CSS rules to include your own logo.
You are able to customize any aspect of GeoNode’s appearance this way.
In the last screenshot, you saw that the main area on the homepage is covered up by the expanded header.

First, we walk through the steps necessary to displace it downward so it is no longer hidden, then change the background color of the header to match the color in our logo graphic.

1. Reopen `<my_geonode>/static/css/brand_navbar.html` in your editor:

    ```bash
    $ cd <my_geonode>/templates/geonode-mapstore-client/snippets
    $ sudo vi brand_navbar.html
    ```

2. Append a rule to change the background color of the header to match the logo graphic:

    ```css
    #gn-brand-navbar {
        ....
        background-color: #ff0000 !important;
    }
    ```

3. Create a new file to manipulate the *hero* section:

    ```bash
    $ cd <my_geonode>/templates/geonode-mapstore-client/snippets
    $ sudo vi hero.html
    ```

4. Add the following code to change the background image and font for the *hero* section:

    ```css
    {% extends "geonode-mapstore-client/snippets/hero.html" %}
    {% block extra_style %}
      <style>
        #gn-hero {
          background-image: url('https://cdn.pixabay.com/photo/2017/09/16/16/09/sea-2755908_960_720.jpg');
          background-size: cover;
          background-position: center center;
          background-repeat: no-repeat;
          background-color: rgb(156, 156, 156);
          background-blend-mode: multiply;
          background-size: 100%;
        }
        .msgapi .gn-hero .jumbotron .gn-hero-description h1 {
          font-weight: lighter;
          word-break: break-word;
          font-style: oblique;
          font-family: orbitron;
          font-size: 3.4rem;
        }
      </style>
    {% endblock %}
    ```

5. Collect the static files into `STATIC_ROOT`, restart the development server and reload the page:

    ```bash
    $ python manage.py collectstatic
    $ sudo service apache2 restart
    ```

    ![](img/css_override.png){ align=center }
    /// caption
    *CSS override*
    ///

You can continue adding rules to this file to override the styles that are in the GeoNode base CSS file which is built from [base.less](https://github.com/GeoNode/geonode/blob/master/geonode/static/geonode/less/base.less).

!!! Note
    You may find it helpful to use your browser's development tools to inspect elements of your site that you want to override to determine which rules are already applied. See the screenshot below.

![](img/inspect_element.png){ align=center }
/// caption
*Screenshot of using browser debugger to inspect the CSS overrides*
///

## Modify GeoNode Homepage

So far we learned how to modify some template sections of your GeoNode main page.
You can do it individually per section template, adding a new page under `<my_geonode>/templates/geonode-mapstore-client/snippets` with the section name, for example `brand_navbar.html`, or by extending the base template file `custom_theme.html` where you can add different theme settings in one place.

1. Remove the previous `hero` section `hero.html` file:

    ```bash
    $ rm <my_geonode>/templates/geonode-mapstore-client/snippets/hero.html
    ```

2. Create a new `custom_theme.html` file:

    ```bash
    $ cd <my_geonode>/templates/geonode-mapstore-client/snippets
    $ sudo vi custom_theme.html
    ```

3. Add the following content to this page:

    ```css
    {% load static %}
    {% block content %}
    <style>
        .msgapi .gn-theme {
            --gn-primary: #df7656;
            --gn-primary-contrast: #e3dcdc;
            --gn-link-color: #fcd823;
            --gn-focus-color: rgba(57, 122, 171, 0.4);
            --gn-footer-bg: #dbb051;
        }

        #gn-hero {
          background: url('https://cdn.pixabay.com/photo/2017/09/16/16/09/sea-2755908_960_720.jpg');
          background-position: center center;
          background-repeat: no-repeat;
          background-blend-mode: multiply;
          background-size: 100%;
        }

        .msgapi .gn-hero .jumbotron .gn-hero-description h1 {
          font-weight: bolder;
          word-break: break-word;
          font-style: oblique;
          font-family: orbitron;
          font-size: 3.4rem;
        }

        .msgapi .gn-hero .jumbotron .gn-hero-description p {
          font-weight: lighter;
          word-break: break-word;
          font-style: oblique;
          font-family: orbitron;
          font-size: 2.2rem;
        }

    </style>
    {% endblock %}
    ```

4. Restart the httpd server:

    ```bash
    $ python manage.py collectstatic
    $ sudo service apache2 restart
    ```

5. Your customized layout should be similar to the next picture:

    ![](img/customized_geonode_project_home.png){ align=center }

6. Edit title and intro message

Login as administrator on GeoNode and go to the `Admin` page:

![](img/admin_menu.png){ align=center }

Create a new theme under `GeoNode Themes Library` and `Themes`:

![](img/themes_admin_section.png){ align=center }

Add a `Name`, `Description`, and turn on the `Is enabled` option.
At the bottom, add a `Jumbotron title` and `Jumbotron content`.
This overrides the default GeoNode welcome title and message.
Click `Save` at the bottom in the end.

![](img/theme_admin_1.png){ align=center }

![](img/theme_admin_2.png){ align=center }

After this, reload your GeoNode homepage. The output should be similar to this:

![](img/custom_home.png){ align=center }
