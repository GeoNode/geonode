# Letsencrypt service for Geonode

This service generates SSL certificates to be used by Nginx.

## Let's Encrypt

Upon startup, it generates one SSL certificate from Let's Encrypt using Certbot. It then starts cron (in foreground) to renew the certificates using Certbot renew.

If for some reason getting the certificate fails, a placeholder certificate is generated. This certificate is invalid, but still allows to encrypt the data and to start the webserver.

To avoid hitting Let's Encrypt very low rate limits when developping or doing tests, LETSENCRYPT_MODE env var can be set to "disabled" (which will completely bypass Let'sEncrypt, simulating a failure) or to "staging" (using Let'sEncrypt test certificates with higher rates).

## Autoissued

An auto-issued certificate is also generate to be used on the LAN if needed. It is also renewed every now and then using the same cron process than above.
