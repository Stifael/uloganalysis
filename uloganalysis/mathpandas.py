"""
Pandas seires / dataframe manipulation
"""

import pandas as pd
import transforms3d.quaternions as quat
import transforms3d.taitbryan as tf
import numpy as np
import utm


def series_quat2euler(q0, q1, q2, q3, msg_name=""):
    """
    Given pandas series q0-q4, compute series roll, pitch, yaw
    """
    yaw, pitch, roll = np.array(
        [
            tf.quat2euler([q0i, q1i, q2i, q3i])
            for q0i, q1i, q2i, q3i in zip(q0, q1, q2, q3)
        ]
    ).T
    yaw = pd.Series(name=msg_name + "yaw", data=yaw, index=q0.index)
    pitch = pd.Series(name=msg_name + "pitch", data=pitch, index=q0.index)
    roll = pd.Series(name=msg_name + "roll", data=roll, index=q0.index)
    return roll, pitch, yaw


def angle_wrap(x):
    """wrap angle between -pi and pi"""
    return np.arcsin(np.sin(x))


def series_quatrot(x, y, z, q0, q1, q2, q3, rot_name=""):
    """
    Given pandas series x-z and quaternion q0-q4,
    compute rotated vector x_r, y_r, z_r
    """
    added_name = "_" + rot_name
    if not rot_name:
        added_name = ""

    vec = np.array(
        [
            quat.rotate_vector([xi, yi, zi], [q0i, q1i, q2i, q3i])
            for xi, yi, zi, q0i, q1i, q2i, q3i in zip(x, y, z, q0, q1, q2, q3)
        ]
    )
    x_r = pd.Series(name=x.name + added_name, data=vec[:, 0], index=x.index)
    y_r = pd.Series(name=y.name + added_name, data=vec[:, 1], index=y.index)
    z_r = pd.Series(name=z.name + added_name, data=vec[:, 2], index=z.index)
    return x_r, y_r, z_r


def series_quatrot_inverse(x, y, z, q0, q1, q2, q3, rot_name=""):
    """
    Given pandas series x-z and quaternion q0-q4,
    compute reversed rotated vector x_r, y_r, z_r
    """
    return series_quatrot(x, y, z, q0, -q1, -q2, -q3, rot_name)


def series_dot(x0, y0, z0, x1, y1, z1, dotname=""):
    """
    Given pandas series x0-z0 and x1-z1,
    compute dot product
    """
    dot = np.array(
        [
            np.dot([x0i, y0i, z0i], [x1i, y1i, z1i])
            for x0i, y0i, z0i, x1i, y1i, z1i in zip(x0, y0, z0, x1, y1, z1)
        ]
    )
    return pd.Series(name=dotname, data=dot, index=x0.index)


def series_pythagoras(x0, y0, dotname=""):
    """
    Given pandas series x0-y0,
    compute absolute horizontal distance
    """
    pythagoras = np.array(
        [np.linalg.norm([x0i, y0i], axis=0) for x0i, y0i in zip(x0, y0)]
    )
    return pd.Series(name=dotname, data=pythagoras, index=x0.index)


def series_UTM(lat, lon, msg_name=""):
    """
    Given pandas series lat/lon in degrees, compute UTM easting/northing/zone)
    """
    easting, northing, zone, letter = np.array(
        [utm.from_latlon(lati, loni) for lati, loni in zip(lat, lon)]
    ).T

    easting = pd.Series(
        name=msg_name + "easting",
        data=easting.astype(np.float),
        index=lat.index,
    )
    northing = pd.Series(
        name=msg_name + "northing",
        data=northing.astype(np.float),
        index=lat.index,
    )
    zone = pd.Series(
        name=msg_name + "zone", data=zone.astype(np.float), index=lat.index
    )
    return easting, northing, zone
