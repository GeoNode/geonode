__version__= (1, 2, 0, 'alpha', 0)

class GeoNodeException(Exception):
    """Base class for exceptions in this module."""
    pass

def get_version():
    import geonode.version
    return geonode.version.get_version(__version__)
