__version__= (1, 2, 0, 'alpha', 1)

def get_version():
    from geonode.utils import get_version
    return get_version(__version__)
