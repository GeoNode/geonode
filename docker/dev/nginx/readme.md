Let's examine and explain the contents and roles of the mentioned files within the Nginx Docker folder. These files typically contain configuration and scripts for setting up and managing Nginx in a Docker environment for GeoNode.

### Files and Their Roles

**Explanation**:

- **FROM nginx:alpine**: Uses the lightweight Alpine version of Nginx as the base image.
- **COPY**: Copies the Nginx configuration files and entrypoint script into the container.
- **RUN chmod +x**: Makes the entrypoint script executable.
- **EXPOSE**: Exposes ports 80 and 443 for HTTP and HTTPS traffic.
- **ENTRYPOINT**: Sets the entrypoint script to be executed when the container starts.

### geonode.conf.envsubst

This Nginx configuration file is designed to set up Nginx to serve as a reverse proxy for both GeoNode and GeoServer, as well as to handle static and uploaded media files. It includes configurations for gzip compression, proxy settings, and specific configurations for handling HTTP and HTTPS requests.

Let's break down each section of the file:

### MIME Types and Charset

```nginx
include /etc/nginx/mime.types;

# This is the main geonode conf
charset     utf-8;
```

- **`include /etc/nginx/mime.types;`**: Includes the default MIME type definitions for Nginx, which map file extensions to MIME types.
- **`charset utf-8;`**: Sets the default character set to UTF-8.

### Client and Proxy Settings

```nginx
# max upload size
client_max_body_size 100G;
client_body_buffer_size 256K;
client_body_timeout 600s;
large_client_header_buffers 4 64k;

proxy_connect_timeout       600;
proxy_send_timeout          600;
proxy_read_timeout          600;
uwsgi_read_timeout          600;
send_timeout                600;

fastcgi_hide_header Set-Cookie;

etag on;
```

- **Client Settings**:

  - **`client_max_body_size 100G;`**: Sets the maximum allowed size of client request bodies to 100GB.
  - **`client_body_buffer_size 256K;`**: Sets the buffer size for reading client request bodies.
  - **`client_body_timeout 600s;`**: Sets the timeout for reading client request bodies.
  - **`large_client_header_buffers 4 64k;`**: Sets the number and size of buffers for large client headers.

- **Proxy Settings**:

  - **`proxy_connect_timeout 600;`**: Sets the timeout for establishing a connection to the proxied server.
  - **`proxy_send_timeout 600;`**: Sets the timeout for sending data to the proxied server.
  - **`proxy_read_timeout 600;`**: Sets the timeout for reading data from the proxied server.
  - **`uwsgi_read_timeout 600;`**: Sets the timeout for reading data from a uwsgi server.
  - **`send_timeout 600;`**: Sets the timeout for sending data to the client.

- **Other Settings**:
  - **`fastcgi_hide_header Set-Cookie;`**: Hides the Set-Cookie header from the response.
  - **`etag on;`**: Enables ETag headers for caching.

### Gzip Compression

```nginx
# compression
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_http_version 1.1;
gzip_disable "MSIE [1-6]\.";
gzip_buffers 16 8k;
gzip_min_length 1100;
gzip_comp_level 6;
gzip_types
        text/css
        text/javascript
        text/xml
        text/plain
        application/xml
        application/xml+rss
        application/javascript
        application/x-javascript
        application/json;
```

- **`gzip on;`**: Enables gzip compression.
- **`gzip_vary on;`**: Adds the `Vary: Accept-Encoding` header to responses.
- **`gzip_proxied any;`**: Enables gzip compression for all proxied requests.
- **`gzip_http_version 1.1;`**: Sets the minimum HTTP version for gzip compression.
- **`gzip_disable "MSIE [1-6]\.";`**: Disables gzip compression for old versions of Internet Explorer.
- **`gzip_buffers 16 8k;`**: Sets the number and size of buffers for gzip compression.
- **`gzip_min_length 1100;`**: Sets the minimum response size for gzip compression.
- **`gzip_comp_level 6;`**: Sets the gzip compression level.
- **`gzip_types`**: Specifies the MIME types to be compressed.

### Location Blocks

#### GeoServer Proxy

```nginx
# GeoServer
location /geoserver {
  # Using a variable is a trick to let Nginx start even if upstream host is not up yet
  # (see https://sandro-keil.de/blog/2017/07/24/let-nginx-start-if-upstream-host-is-unavailable-or-down/)
  set $upstream $GEOSERVER_LB_HOST_IP:$GEOSERVER_LB_PORT;

  proxy_set_header X-Forwarded-Host $host;
  proxy_set_header X-Forwarded-Server $host;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-Proto $HTTP_SCHEME;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_hide_header X-Frame-Options;
  proxy_pass http://$upstream;
  proxy_http_version 1.1;
  proxy_redirect http://$upstream $HTTP_SCHEME://$HTTP_HOST;
  proxy_request_buffering  off;
  client_max_body_size 0;
}
```

- **`location /geoserver`**: Defines settings for requests to `/geoserver`.
- **`set $upstream $GEOSERVER_LB_HOST_IP:$GEOSERVER_LB_PORT;`**: Sets a variable for the GeoServer upstream.
- **`proxy_set_header`**: Sets various headers for the proxied request.
- **`proxy_pass http://$upstream;`**: Forwards the request to the GeoServer upstream.
- **`proxy_http_version 1.1;`**: Uses HTTP/1.1 for proxying.
- **`proxy_redirect http://$upstream $HTTP_SCHEME://$HTTP_HOST;`**: Adjusts the `Location` header in redirects.
- **`proxy_request_buffering off;`**: Disables buffering of the request body.
- **`client_max_body_size 0;`**: Removes the limit on the size of the request body.

#### Static Files

```nginx
# GeoNode
location /static/ {
  alias $STATIC_ROOT;

  location ~* \.(?:html|js|jpg|jpeg|gif|png|css|tgz|gz|rar|bz2|doc|pdf|ppt|tar|wav|bmp|ttf|rtf|swf|ico|flv|txt|woff|woff2|svg|xml)$ {
      gzip_static always;
      expires 30d;
      access_log off;
      add_header Pragma "public";
      add_header Cache-Control "max-age=31536000, public";
  }
}
```

- **`location /static/`**: Defines settings for serving static files.
- **`alias $STATIC_ROOT;`**: Maps the URL path to the actual filesystem path defined by the `STATIC_ROOT` environment variable.
- **`location ~*`**: Matches specific file types and applies additional settings.
  - **`gzip_static always;`**: Enables gzip_static for pre-compressed files.
  - **`expires 30d;`**: Sets the expiration time for cache control.
  - **`access_log off;`**: Disables access logging for these files.
  - **`add_header`**: Adds headers for caching.

#### Uploaded Media

```nginx
location /uploaded/ {
  alias $MEDIA_ROOT;

  location ~* \.(?:html|js|jpg|jpeg|gif|png|css|tgz|gz|rar|bz2|doc|pdf|ppt|tar|wav|bmp|ttf|rtf|swf|ico|flv|txt|woff|woff2|svg|xml)$ {
      gzip_static always;
      expires 30d;
      access_log off;
      add_header Pragma "public";
      add_header Cache-Control "max-age=31536000, public";
  }
}
```

- **`location /uploaded/`**: Defines settings for serving uploaded media files.
- **`alias $MEDIA_ROOT;`**: Maps the URL path to the actual filesystem path defined by the `MEDIA_ROOT` environment variable.
- **`location ~*`**: Matches specific file types and applies additional settings (similar to the `/static/` location).

#### Proxy for Main Application

```nginx
location / {
  # Using a variable is a trick to let Nginx start even if upstream host is not up yet
  # (see https://sandro-keil.de/blog/2017/07/24/let-nginx-start-if-upstream-host-is-unavailable-or-down/)
  set $upstream $GEONODE_LB_HOST_IP:$GEONODE_LB_PORT;

  if ($request_method = OPTIONS) {
      add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, OPTIONS";
      add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept";
      add_header Access-Control-Allow-Credentials true;
      add_header Content-Length 0;
      add_header Content-Type text/plain;
      add_header Access-Control-Max-Age 1728000;
      return 200;
  }

  add_header Access-Control-Allow-Credentials false;
  add_header Access-Control-Allow-Headers "Content-Type, Accept, Authorization, Origin, User-Agent";
  add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, OPTIONS";

  proxy_redirect              off;
  proxy_set_header            Host $host;
  proxy_set_header            Origin $HTTP_SCHEME://$host;
  proxy_set_header            X-Real
```

### nginx.conf.envsubst

This Nginx configuration file sets up the basic structure and includes for handling both HTTP and HTTPS traffic, with specific provisions for Docker environments. Let's go through it step-by-step to understand its structure and purpose.

### Detailed Breakdown

#### Comment and Note on Environment Variables

```nginx
# NOTE : $VARIABLES are env variables replaced by entrypoint.sh using envsubst
# not to be mistaken for nginx variables (also starting with $, but usually lowercase)
```

- **Comment**: Explains that the `$VARIABLES` are environment variables that will be replaced by the `entrypoint.sh` script using `envsubst`. This should not be confused with Nginx variables, which typically start with `$` and are usually lowercase.

#### Worker Processes

```nginx
worker_processes auto;
```

- **`worker_processes auto;`**: Automatically sets the number of worker processes based on the number of available CPU cores. This helps optimize the performance of Nginx.

#### Events Block

```nginx
events {

}
```

- **`events`**: Defines settings related to Nginx's event-driven architecture. In this case, it's empty, which means default settings will be used.

#### HTTP Block

```nginx
http {
    server_names_hash_bucket_size  64;

    # Allow Nginx to resolve Docker host names (see https://sandro-keil.de/blog/2017/07/24/let-nginx-start-if-upstream-host-is-unavailable-or-down/)
    resolver $RESOLVER; # it seems rancher uses 169.254.169.250 instead of 127.0.0.11 which works well in docker-compose (see /etc/resolv.conf)

    # https - listens on specific name - this uses letsencrypt cert
    # this includes a symlink that links either to nginx.https.available.conf if https in enabled
    # or to an empty file if https is disabled.
    include nginx.https.enabled.conf;

    # http - listens to specific HTTP_HOST only - this is not encrypted (not ideal but admissible on LAN for instance)
    # even if not used (HTTP_HOST empty), we must keep it as it's used for internal API calls between django and geoserver
    # TODO : do not use unencrypted connection even on LAN, but is it possible to have browser not complaining about unknown authority ?
    server {
        listen              80;
        server_name         $HTTP_HOST 127.0.0.1;

        include sites-enabled/*.conf;
    }

    # Default server closes the connection (we can connect only using HTTP_HOST and HTTPS_HOST)
    server {
        listen          80 default_server;
        listen          443;
        server_name     _;
        return          444;
    }
}
```

- **`http {}`**: The main HTTP configuration block where most of the web server settings are defined.

##### `server_names_hash_bucket_size 64;`

- **`server_names_hash_bucket_size 64;`**: Sets the size of the hash table for server names. This can help optimize the performance if you have many server names.

##### `resolver $RESOLVER;`

- **`resolver $RESOLVER;`**: Configures Nginx to use a specific DNS resolver. `$RESOLVER` is an environment variable that will be replaced by the actual DNS resolver IP address (for example, Docker's internal DNS server). This is useful for resolving Docker host names.

##### `include nginx.https.enabled.conf;`

- **`include nginx.https.enabled.conf;`**: Includes an additional configuration file for handling HTTPS. This file is either a symlink to a valid HTTPS configuration or an empty file if HTTPS is disabled.

##### HTTP Server Block

```nginx
server {
    listen              80;
    server_name         $HTTP_HOST 127.0.0.1;

    include sites-enabled/*.conf;
}
```

- **`server {}`**: Defines a server block that listens on port 80 (HTTP).
  - **`listen 80;`**: Specifies that this server block listens on port 80.
  - **`server_name $HTTP_HOST 127.0.0.1;`**: Defines the server names for this block, including the environment variable `$HTTP_HOST` and `127.0.0.1`.
  - **`include sites-enabled/*.conf;`**: Includes all configuration files from the `sites-enabled` directory. This is where specific site configurations are typically placed.

##### Default Server Block

```nginx
server {
    listen          80 default_server;
    listen          443;
    server_name     _;
    return          444;
}
```

- **`server {}`**: Defines a default server block.
  - **`listen 80 default_server;`**: Specifies that this server block listens on port 80 and acts as the default server.
  - **`listen 443;`**: Specifies that this server block also listens on port 443 (HTTPS).
  - **`server_name _;`**: The `_` is a wildcard that matches any server name not caught by other `server_name` directives.
  - **`return 444;`**: Immediately closes the connection with a 444 status code, which tells Nginx to drop the connection without sending a response to the client.

### Summary

- **Environment Variable Substitution**: The configuration uses placeholders for environment variables, which are replaced by the `entrypoint.sh` script using `envsubst` before Nginx starts.
- **Worker Processes**: Configured to automatically use the optimal number of worker processes.
- **DNS Resolver**: Configures a DNS resolver to resolve Docker hostnames.
- **HTTPS Configuration**: Conditional inclusion of HTTPS settings based on the presence of environment variables.
- **HTTP Server Block**: Handles unencrypted HTTP traffic and includes specific site configurations.
- **Default Server Block**: Catches all other traffic and drops connections not specifically handled by other server blocks.

This configuration ensures that Nginx can dynamically adjust based on the provided environment variables, allowing it to handle both HTTP and HTTPS traffic efficiently while integrating seamlessly with Docker-based infrastructure.

### nginx.conf.envsubst FEAT nginx.https.available.conf.envsubst

The two files are used together, but they serve different purposes within the Nginx configuration. Here’s a clearer explanation of how they are used and their roles:

### Main Configuration (`nginx.conf.envsubst`)

This is the primary configuration file that sets up the overall structure and basic settings for Nginx. It includes the necessary directives and conditionally includes other configuration files based on the environment.

#### Key Responsibilities:

- **Overall Structure**: Defines the main structure for Nginx, including worker processes, events, and HTTP settings.
- **Conditional Inclusions**: Includes additional configuration files conditionally, such as the HTTPS-specific configuration if HTTPS is enabled.
- **Default Server Blocks**: Sets up default server blocks to handle connections not specifically addressed by other server blocks.

### HTTPS-Specific Configuration (`nginx.https.available.conf.envsubst`)

This file contains detailed settings for SSL/TLS and handles the redirection of HTTP traffic to HTTPS. It is included by the main configuration file when HTTPS is enabled.

#### Key Responsibilities:

- **SSL/TLS Settings**: Configures SSL/TLS settings, including certificates, protocols, and ciphers.
- **HTTP to HTTPS Redirection**: Redirects HTTP traffic to HTTPS to ensure secure communication.

### How They Work Together

1. **Main Configuration (`nginx.conf.envsubst`)**:

   - This file is processed first and sets up the foundational configuration for Nginx.
   - It includes the HTTPS-specific configuration file conditionally based on the presence of the `HTTPS_HOST` environment variable.
   - Example of including the HTTPS-specific configuration:
     ```nginx
     include nginx.https.enabled.conf;
     ```

2. **HTTPS-Specific Configuration (`nginx.https.available.conf.envsubst`)**:
   - This file is included in the main configuration file when HTTPS is enabled.
   - It provides detailed settings for handling HTTPS traffic and redirects HTTP traffic to HTTPS.
   - This inclusion ensures that all HTTPS-specific settings are applied if HTTPS is enabled.

### Example Workflow

- **Step 1**: Nginx starts and processes the `nginx.conf.envsubst` file.
- **Step 2**: The `entrypoint.sh` script uses `envsubst` to replace environment variables in `nginx.conf.envsubst` and other related files.
- **Step 3**: The main configuration file includes `nginx.https.enabled.conf` if the `HTTPS_HOST` environment variable is set.
- **Step 4**: The included `nginx.https.enabled.conf` file applies SSL/TLS settings and sets up HTTP to HTTPS redirection.

### Example Combined Configuration

Here is how the configuration files might be combined during execution:

#### `nginx.conf.envsubst`

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    server_names_hash_bucket_size 64;

    resolver $RESOLVER;

    include nginx.https.enabled.conf;

    server {
        listen 80;
        server_name $HTTP_HOST 127.0.0.1;

        include sites-enabled/*.conf;
    }

    server {
        listen 80 default_server;
        listen 443;
        server_name _;
        return 444;
    }
}
```

#### `nginx.https.available.conf.envsubst`

```nginx
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

server {
    listen 443 ssl;
    server_name $HTTPS_HOST;
    keepalive_timeout 70;

    ssl_certificate /certificate_symlink/fullchain.pem;
    ssl_certificate_key /certificate_symlink/privkey.pem;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers HIGH:!aNULL:!MD5;

    include sites-enabled/*.conf;
}

server {
    listen 80;
    server_name $HTTPS_HOST $HTTP_HOST;

    location /.well-known {
        alias /geonode-certificates/.well-known;
        include /etc/nginx/mime.types;
    }

    location / {
        return 302 https://$HTTPS_HOST$request_uri;
    }
}
```

### Summary

- **Main Configuration (`nginx.conf.envsubst`)**: Sets up the overall server structure and includes the HTTPS-specific configuration conditionally.
- **HTTPS-Specific Configuration (`nginx.https.available.conf.envsubst`)**: Provides SSL/TLS settings and handles HTTP to HTTPS redirection.

The files are used together to provide a flexible and secure Nginx configuration that can adapt to different environments (e.g., whether HTTPS is enabled or not). This modular approach makes the configuration easier to manage and maintain.
