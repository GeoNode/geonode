__version__= (1, 2, 0, 'rc', 3)

def get_version():
    import geonode.utils
    return geonode.utils.get_version(__version__)
