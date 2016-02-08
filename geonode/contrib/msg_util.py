from __future__ import print_function
# Hackish:)
import sys
from django.conf import settings


def msg(s):
    #if settings.DEBUG:
    print(s)
def dashes(d='-'): msg(40*d)
def msgd(s): dashes(); msg(s)
def msgt(s): dashes(); msg(s); dashes()
def msgn(m): msg('\n'); msg(m); dashes()
def msgx(m): msgt('Error'); msg(m); msg('Exiting...'); dashes(); #sys.exit(-1)
