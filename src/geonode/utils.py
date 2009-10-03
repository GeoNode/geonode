import pkg_resources
from UserDict import DictMixin
from ConfigParser import ConfigParser


def path_extrapolate(stub, pkg='GeoNode'):
    req = pkg_resources.Requirement.parse(pkg)
    return pkg_resources.resource_filename(req,  stub)

class SectionConfigMap(DictMixin):

    def __init__(self, parser):
        self.parser = parser
        self.sects = parser.sections()

    def __iter__(self):
        for sname in self.sects:
            yield sname
            
    def __getitem__(self, idx):
        return dict(self.parser.items(idx))

    def __setitem__(self, idx, val):
        for item in val.items():
            self.parser.set(*(idx,) + item)

    def __delitem__(self, idx):
        self.parser.remove_section(idx)

    def keys(self):
        return self.parser.sections()

    def write(self, fn):
        self.parser.write(fn)

    @classmethod
    def load(cls, fname):
        parser = ConfigParser()
        parser.read(fname)
        return cls(parser)
