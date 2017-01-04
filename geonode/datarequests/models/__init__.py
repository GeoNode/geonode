from .base_request import *
from .profile_request import *
from .data_request import *

from django_cas_ng import signals as cas_signals
from django_cas_ng.backends import CASBackend

def account_authenticated(instance, **kw):
    pprint("hello there")
    for key, value in kwargs.iteritems():
        pprint("{}:{}".format(key,value))
    return
    
cas_signals.cas_user_authenticated.connect(account_authenticated, sender = CASBackend)
