#########################################################################
#
# Copyright (C) 2024 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import math
import logging
import numpy as np

logger = logging.getLogger("importer")


wgs84OneOverRadii = np.array([1.0 / 6378137.0, 1.0 / 6378137.0, 1.0 / 6356752.3142451793])
wgs84OneOverRadiiSquared = np.array(
    [
        1.0 / (6378137.0 * 6378137.0),
        1.0 / (6378137.0 * 6378137.0),
        1.0 / (6356752.3142451793 * 6356752.3142451793),
    ]
)
wgs84CenterToleranceSquared = 0.1
CesiumMath_EPSILON12 = 0.000000000001


def fromOrientedBoundingBox(center, halfAxes):
    u = halfAxes[:, 0]
    v = halfAxes[:, 1]
    w = halfAxes[:, 2]

    u = np.add(u, v)
    w = np.add(u, w)

    return {"center": center, "radius": np.linalg.norm(u)}


def scaleToGeodeticSurface(cartesian, oneOverRadii, oneOverRadiiSquared, centerToleranceSquared):
    # https://github.com/CesiumGS/cesium/blob/main/packages/engine/Source/Core/scaleToGeodeticSurface.js#L25
    positionX = cartesian[0]
    positionY = cartesian[1]
    positionZ = cartesian[2]

    oneOverRadiiX = oneOverRadii[0]
    oneOverRadiiY = oneOverRadii[1]
    oneOverRadiiZ = oneOverRadii[2]

    x2 = positionX * positionX * oneOverRadiiX * oneOverRadiiX
    y2 = positionY * positionY * oneOverRadiiY * oneOverRadiiY
    z2 = positionZ * positionZ * oneOverRadiiZ * oneOverRadiiZ

    squaredNorm = x2 + y2 + z2
    ratio = math.sqrt(1.0 / squaredNorm)

    intersection = cartesian * ratio

    if squaredNorm < centerToleranceSquared:
        return intersection[:3] if np.isfinite(ratio) else np.NaN

    oneOverRadiiSquaredX = oneOverRadiiSquared[0]
    oneOverRadiiSquaredY = oneOverRadiiSquared[1]
    oneOverRadiiSquaredZ = oneOverRadiiSquared[2]

    gradient = np.ones(3)
    gradient[0] = intersection[0] * oneOverRadiiSquaredX * 2.0
    gradient[1] = intersection[1] * oneOverRadiiSquaredY * 2.0
    gradient[2] = intersection[2] * oneOverRadiiSquaredZ * 2.0

    _lambda = ((1.0 - ratio) * np.linalg.norm(cartesian)) / (0.5 * np.linalg.norm(gradient))
    correction = 0.0

    while True:
        _lambda -= correction

        xMultiplier = 1.0 / (1.0 + _lambda * oneOverRadiiSquaredX)
        yMultiplier = 1.0 / (1.0 + _lambda * oneOverRadiiSquaredY)
        zMultiplier = 1.0 / (1.0 + _lambda * oneOverRadiiSquaredZ)

        xMultiplier2 = xMultiplier * xMultiplier
        yMultiplier2 = yMultiplier * yMultiplier
        zMultiplier2 = zMultiplier * zMultiplier

        xMultiplier3 = xMultiplier2 * xMultiplier
        yMultiplier3 = yMultiplier2 * yMultiplier
        zMultiplier3 = zMultiplier2 * zMultiplier

        func = x2 * xMultiplier2 + y2 * yMultiplier2 + z2 * zMultiplier2 - 1.0

        # "denominator" here refers to the use of this expression in the velocity and acceleration
        # computations in the sections to follow.
        denominator = (
            x2 * xMultiplier3 * oneOverRadiiSquaredX
            + y2 * yMultiplier3 * oneOverRadiiSquaredY
            + z2 * zMultiplier3 * oneOverRadiiSquaredZ
        )

        derivative = -2.0 * denominator
        correction = func / derivative

        if math.fabs(func) > CesiumMath_EPSILON12:
            break

    result = np.ones(3)
    result[0] = positionX * xMultiplier
    result[1] = positionY * yMultiplier
    result[2] = positionZ * zMultiplier

    return result


def fromCartesian(cartesian):
    # https://github.com/CesiumGS/cesium/blob/main/packages/engine/Source/Core/Cartographic.js#L116
    p = scaleToGeodeticSurface(
        cartesian,
        wgs84OneOverRadii,
        wgs84OneOverRadiiSquared,
        wgs84CenterToleranceSquared,
    )

    n = p * wgs84OneOverRadiiSquared
    n = n / np.linalg.norm(n)

    h = cartesian[:3] - p
    longitude = math.atan2(n[1], n[0])
    latitude = math.asin(n[2])

    height = math.copysign(1, h.dot(cartesian[:3])) * np.linalg.norm(h)

    return {"longitude": longitude, "latitude": latitude, "height": height}


def getScale(matrix):
    """
    Cesium.Matrix4.getScale()
    Extracts the non-uniform scale assuming the matrix is an affine transformation
    # https://github.com/CesiumGS/cesium/blob/1.118/packages/engine/Source/Core/Matrix4.js#L1596-L1612
    """

    # check the type of the matrix
    if not isinstance(matrix, np.ndarray):
        print("Please define a NumPy array object")

    x = np.linalg.norm([matrix[0][0], matrix[0][1], matrix[0][2]])
    y = np.linalg.norm([matrix[1][0], matrix[1][1], matrix[1][2]])
    z = np.linalg.norm([matrix[2][0], matrix[2][1], matrix[2][2]])

    result = np.array([x, y, z])

    return result


def box_to_wgs84(box_raw, transform_raw):
    box = box_raw
    transform_raw = transform_raw or [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    # transform_raw = transform_raw if transform_raw else range[12]

    transform = np.array(
        [
            transform_raw[0:4],
            transform_raw[4:8],
            transform_raw[8:12],
            transform_raw[12:16],
        ]
    )

    point = np.array([box[0], box[1], box[2], 1])
    center = point.dot(transform)  # Cesium.Matrix4.multiplyByPoint
    rotationScale = transform[:3, :3]  # Cesium.Matrix4.getMatrix3
    halfAxes = np.multiply(
        rotationScale,
        np.array(
            [
                [box[3], box[4], box[5]],
                [box[6], box[7], box[8]],
                [box[9], box[10], box[11]],
            ]
        ),
    )

    sphere = fromOrientedBoundingBox(center, halfAxes)
    cartographic = fromCartesian(sphere["center"])

    lng = math.degrees(cartographic["longitude"])
    lat = math.degrees(cartographic["latitude"])

    # https://github.com/geosolutions-it/MapStore2/blob/master/web/client/utils/MapUtils.js#L51C16-L51C34
    radiusDegrees = sphere["radius"] / 111194.87428468118

    return {
        "minx": lng - radiusDegrees,
        "miny": lat - radiusDegrees,
        "maxx": lng + radiusDegrees,
        "maxy": lat + radiusDegrees,
    }


def sphere_to_wgs84(sphere_raw, transform_raw):

    transform_raw = transform_raw or [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

    transform = np.array(
        [
            transform_raw[0:4],
            transform_raw[4:8],
            transform_raw[8:12],
            transform_raw[12:16],
        ]
    )

    centerPoint = np.array([sphere_raw[0], sphere_raw[1], sphere_raw[2], 1])

    radius = sphere_raw[3]

    # Sphere center after the transformation
    center = centerPoint.dot(transform)  # Cesium.Matrix4.multiplyByPoint

    scale = getScale(transform)
    uniformScale = np.max(scale)
    radiusDegrees = (radius * uniformScale) / 111194.87428468118  # degrees of one meter

    cartographic = fromCartesian(center)

    if not cartographic:
        return None

    lng = math.degrees(cartographic["longitude"])
    lat = math.degrees(cartographic["latitude"])

    return {
        "minx": lng - radiusDegrees,
        "miny": lat - radiusDegrees,
        "maxx": lng + radiusDegrees,
        "maxy": lat + radiusDegrees,
    }
