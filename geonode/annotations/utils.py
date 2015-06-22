import codecs
from cStringIO import StringIO
import csv
import datetime


dateparts = '%Y', '%m', '%d'
timeparts = '%H', '%M', '%S'
_patterns = []
for i in xrange(len(dateparts)):
    _patterns.append('/'.join(dateparts[0:i + 1]))
    _patterns.append('-'.join(dateparts[0:i + 1]))
for i in xrange(len(timeparts)):
    time = ':'.join(timeparts[0:i + 1])
    _patterns.append('/'.join(dateparts) + 'T' + time)
    _patterns.append('-'.join(dateparts) + 'T' + time)
    _patterns.append('/'.join(dateparts) + ' ' + time)
    _patterns.append('-'.join(dateparts) + ' ' + time)
del dateparts, timeparts
_epoch = datetime.datetime.utcfromtimestamp(0)


def datetime_to_seconds(dt):
    delta = dt - _epoch
    # @todo replace with 2.7 call to total_seconds
    # return delta.total_seconds()
    return ((delta.days * 86400 + delta.seconds) * 10**6
            + delta.microseconds) / 1e6


def parse_date_time(val):
    if val is None:
        return None
    if val[0] == '-':
        raise ValueError('Alas, negative dates are not supported')
    idx = val.find('.')
    if idx > 0:
        val = val[:idx]
    for p in _patterns:
        try:
            return datetime.datetime.strptime(val, p)
        except ValueError:
            pass


def unicode_csv_dict_reader(fp):
    if isinstance(fp, basestring):
        fp = StringIO(fp)

    # guess encoding, yay
    encodings = ('utf-8', 'cp1252')
    for enc in encodings:
        fp.seek(0)
        reader = codecs.getreader(enc)(fp)
        try:
            for line in reader:
                line.encode('utf-8')
            break
        except UnicodeDecodeError:
            pass
    if not enc:
        raise UnicodeError('unable to decode CSV, invalid characters present')

    fp.seek(0)
    lines = (line.encode('utf-8') for line in codecs.getreader(enc)(fp, errors='ignore'))
    reader = csv.DictReader(lines)
    return (dict([(k, unicode(v, 'utf-8')) for k, v in row.items() if v]) for row in reader)


def make_point(x, y):
    return '{"type" : "Point", "coordinates" : [ %s, %s ]}' % (x, y)
