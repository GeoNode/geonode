from pyproj import transform, Proj


def get_lon_lat(center_x, center_y):
    wgs84 = Proj(init='epsg:4326')
    mercator = Proj(init='epsg:3857')
    lon, lat = transform(mercator, wgs84, center_x, center_y)
    return lon, lat
