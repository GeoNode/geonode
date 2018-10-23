# Changelog

## Version 2.x

### 2.10rc4.1

- use env var instead of secrets (small benefit in terms of security not worth complexity)
- hardcode rclone S3 configuration (other provider would have to be hardcoded too)
- complete CI tests

### 2.10rc4.0

- adopted Geonode's versions number (with an additionnal level for subreleases)
- moved the setup to the main Geonode repo under `scripts/spcgeonode`, this makes it easier to use as developement setup for Geonode
- use CircleCI (mostly to avoid interfering with existing travis setup)

## Version 0.1.x (Geonode 2.10)

**WARNING** YOU CANNOT UPGRADE FROM 0.0.x to 0.1.x  
YOU NEED TO DO A FRESH INSTALL AND MANUALLY TRANSFER THE DATA

### 0.1.1

- improved nginx config (gzip and expiration header)

### 0.1.0

- targetting future 2.10
- removed elastic search container (it was unused anyways)
- removed postgres login hack and using instead Geonode-Geoserver OAuth mecanism
- prebuilt geodatadir used again and master password procedure simplified
- added django healthcheck
- if https is enabled, force redirection to https host (as geonode doesn't support multiple domain names/relative installs)
- django secret generated automatically

## Version 0.0.x (Geonode 2.6)

### 0.0.25

- undo admin users disabled again
- revert using 2.6.x branch (because of side effect - login taking ages)

### 0.0.24

- use Geonode's Geoserver .war build instead of starting from vanilla
- fix thumbnail generation (uses a custom release of Geonode)
- django admin users are again disabled on restart (so we can keep only 1 superuser)
- added travis integration test (try to deploy django then tries to create an user, upload a layer, get the thumbnail and get a tile of the layer)
- changed rclone configuration (you must now provide rclone conf file)
- removed syncthings
- make http(s) ports parametrable in case a port is already busy

### 0.0.23

- various fixes (broken pip dependencies, wrong fix for geoserver proxy, ssl certificate refreshing)

### 0.0.22

- siteurl set using HTTPS_HOST or HTTP_HOST (instead of "/" which isn't supported)

### 0.0.21

- use custom build of geonode (with some fixes not upstreamed yet)

### 0.0.18

- geoserver master password reset is cleaner (programmatically reset the password from initial datadir before first launch)
- support empty HTTP_HOST or HTTPS_HOST
- geosever 2.12.1 => 2.12.2
- cleaned up env vars
- upgrade should work

### 0.0.17

- improve nginx<->letsencrypt (nginx can work without letsencrypt service)

### 0.0.16

- put django in main directory (so it's more clear for deploy builds)

### 0.0.15

- removed rancher template from repo
- removed entryponts and command from django image to prevent what looks like a bug in rancher where empty entrypoint in docker-compose isn't taken into account

### 0.0.11

- added a second backup service using RClone (the idea is to test both syncthings and rclone then choose one)

### 0.0.10

- we don't rely on an initial geodatadir anymore, instead we start from scratch, launch geoserver once, then do our modifications
- added a backup service using Syncthings

### 0.0.9

- fix bug with rancher resolver on rancher

### 0.0.8

- allow to disable/test let's encrypt using env variables
- we use geonode users/groups table directly for geoserver's authentication

### 0.0.7

- have ssl working online
- use env variables / secrets where applicable
- publish on git and autobuild images
- make docker deploy work again
