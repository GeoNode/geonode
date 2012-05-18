__all__ = ('__version__', '__build__', '__docformat__', 'get_revision')
__version__= (1, 2, 0, 'alpha', 0)

def get_version():
    from geonode.utils import get_version
    return get_version(__version__)
