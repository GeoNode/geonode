from __future__ import absolute_import
from django import dispatch

cas_user_authenticated = dispatch.Signal(
    providing_args=['user', 'created', 'attributes', 'ticket', 'service'],
)

cas_user_logout = dispatch.Signal(
    providing_args=['user', 'session', 'ticket'],
)
