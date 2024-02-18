import numpy as np


def position_to_polar(x, y):
    """
    Convert Cartesian coordinates to polar coordinates.

    Parameters:
        x (float): The x-coordinate.
        y (float): The y-coordinate.

    Returns:
        tuple: A tuple containing:
            - r (float): The radial distance from the origin to the point (x, y).
            - theta (float): The polar angle in radians, measured counterclockwise from the positive x-axis.

    """
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return r, theta


def polar_to_position(r, theta):
    """
    Convert polar coordinates to Cartesian coordinates.

    Parameters:
        r (float): The radial distance from the origin.
        theta (float): The polar angle in radians.

    Returns:
        tuple: A tuple containing:
            - x (float): The x-coordinate.
            - y (float): The y-coordinate.

    """
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y


def rad_to_deg(rad):
    """
    Convert radians to degrees.

    Parameters:
        rad (float): The angle in radians.

    Returns:
        float: The angle converted to degrees.

    """
    deg = rad * 180 / np.pi
    if deg > 180:
        deg = 360 - deg
    return deg


def deg_to_rad(deg):
    """
    Convert degrees to radians.

    Parameters:
        deg (float): The angle in degrees.

    Returns:
        float: The angle converted to radians.

    """
    rad = deg * np.pi / 180
    if rad > np.pi:
        rad = 2 * np.pi - rad
    return rad
    