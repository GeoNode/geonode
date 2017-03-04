import django.dispatch


announcement_created = django.dispatch.Signal(providing_args=["announcement", "request"])
announcement_updated = django.dispatch.Signal(providing_args=["announcement", "request"])
announcement_deleted = django.dispatch.Signal(providing_args=["announcement", "request"])
