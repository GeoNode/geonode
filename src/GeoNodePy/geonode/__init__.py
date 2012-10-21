__version__= (1, 2, 0, 'final', 0)

def get_version():
    import geonode.utils
    return geonode.utils.get_version(__version__)
