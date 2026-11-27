# Volume permissions

The GeoNode containers are moving from root to normal users. Volumes created by older versions are owned by root, so a non-root service could not write to them. The `permissions-init` service fixes the ownership of the volumes once, as root, before the other services start.

## Concepts

**permissions-init**: a short-lived service of `docker-compose.yml`. It uses the GeoNode image, runs `docker/permissions/fix-permissions.sh` as root, then exits. The other services start only after it exits successfully.

**Marker file**: when a volume is fixed, the script writes `.geonode-permissions-v1` in its root folder. Later starts skip that volume, so the work is done only once.

**Group 0**: all GeoNode containers share group 0. Membership gives no special rights, it is the group Kubernetes and OpenShift also give to containers running with a random user ID.

## Ownership

| Volume | Owner : group | Access |
| --- | --- | --- |
| statics, geoserver-data-dir, backup-restore | 1000 : 0 | group can write |
| nginx-confd, nginx-certificates | 101 : 0 | group can write |
| dbdata, dbbackups | 70 : 70 | owner only |

For volumes owned by group 0, folders get the setgid bit (new files keep group 0) and are group-writable, files are group-readable and group-writable.

The script only changes the files and folders that do not already have the expected owner and group: a volume that is already correct is only read. It never follows symbolic links out of a volume.

An empty volume gets no marker file: Docker copies the image content only into an empty volume, and PostgreSQL refuses to initialize a data folder that is not empty.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `PERMISSIONS_INIT_SKIP` | empty | Comma-separated volume names to leave untouched, for example `geoserver-data-dir,dbdata` |
| `PERMISSIONS_INIT_FORCE` | `false` | Fix the volumes again even if they carry the marker file |

Set them in the `.env` file used by `docker compose`.

## Run it by hand

```bash
# fix the volumes, skipping the ones already marked
docker compose run --rm permissions-init

# fix them again, for example after the services ran as root for a while
docker compose run --rm -e PERMISSIONS_INIT_FORCE=true permissions-init

# leave a very large volume to be handled separately
docker compose run --rm -e PERMISSIONS_INIT_SKIP=geoserver-data-dir permissions-init
```

The script prints, for each volume, the owner it applied and how long it took.

The time depends on the number of files, not on their size. To estimate it, count the files first:

```bash
docker compose run --rm --no-deps --entrypoint sh permissions-init -c 'find /volumes/geoserver-data-dir | wc -l'
```

!!! note
    If a volume is replaced by a host folder (bind mount) in `docker-compose.yml`, `permissions-init` changes the owner of that host folder too. Add it to `PERMISSIONS_INIT_SKIP` to keep the host ownership.

## Run the services as non-root

Until GeoNode 5.2.0 the services still run as root by default. To try non-root users earlier, set in `.env`:

| Variable | Value | Services |
| --- | --- | --- |
| `GEONODE_UID_GID` | `1000:0` | django, celery |
| `DB_UID_GID` | `70:70` | db |

If a service then stops with `cannot write to ...`, run `docker compose run --rm -e PERMISSIONS_INIT_FORCE=true permissions-init` and start it again.

## Kubernetes

The same script can run in an init container: run it as root with the GeoNode image, mount each volume under `/volumes/<name>`, and set the entrypoint to `bash /usr/src/geonode/docker/permissions/fix-permissions.sh`.

Alternatively, `securityContext.fsGroup: 0` makes Kubernetes give group 0 to the mounted volumes, which covers the group ownership. Use `fsGroupChangePolicy: OnRootMismatch` so large volumes are not walked again on every start.
