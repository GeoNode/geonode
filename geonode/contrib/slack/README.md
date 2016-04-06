# SLACK Contrib App

Slack is a contrib app starting with GeoNode 2.4.  The slack contrib app is used for publishing messages to [Slack](https://slack.com/) channels.

## Settings

### Activation

To activate the slack contrib app, you need to add `geonode.contrib.slack` to `INSTALLED_APPS`.  For example, with:

```Python
GEONODE_CONTRIB_APPS = (
    'geonode.contrib.slack'
)
GEONODE_APPS = GEONODE_APPS + GEONODE_CONTRIB_APPS
```

### Configuration

The relevant section in [settings.py](https://github.com/GeoNode/geonode/blob/master/geonode/settings.py) starts at line [812](https://github.com/GeoNode/geonode/blob/master/geonode/settings.py#L812).
```Python
# Settings for Slack contrib app
SLACK_ENABLED = False
SLACK_WEBHOOK_URLS = [
    "https://hooks.slack.com/services/T000/B000/XX"
]
```

To enable the slack contrib app simply switch `SLACK_ENABLED` to `True` and replace the existing `SLACK_WEBHOOK_URLS` with the webhook urls you've gotten from your Slack incoming webhooks integration.

## Slack

Slack is a business productivity platform that replaces the need for email.  It's similar to a chatroom, but more sophisticated.  It provides a variety out of the box integrations as well as the ability to make custom integrations.  This provides new automated ways of synchronizing workflows across multiple platforms.  For instance, tracking GitHub commits, Tweets, and GeoNode posts all in one channel.

### Incoming Webhooks
[Incoming webhooks](https://api.slack.com/incoming-webhooks) are Slack's way of exposing an endpoint you can push messages through, like an email address.  You can learn more at https://api.slack.com/incoming-webhooks.  GeoNode posts a JSON payload to these urls.  Slack converts these JSON payloads into messages.  Generally speaking, it's one url per channel (you can override this though).

### Attachments
GeoNode uses Slack's [Attachments](https://api.slack.com/docs/attachments) API to build rich messages that include layer thumbnails and links to download shapefiles, view in Google Earth, etc.
