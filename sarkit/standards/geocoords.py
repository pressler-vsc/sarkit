"""
==========================================================
Geographic Coordinates (:mod:`sarkit.standards.geocoords`)
==========================================================

Global Coordinate Systems
-------------------------

.. autosummary::

   ecf_to_geodetic
   geodetic_to_ecf

Local Coordinate Systems
------------------------

.. autosummary::

   east
   north
   up

"""

import numpy as np
import numpy.typing as npt

# WGS-84 parameters and related derived parameters
_A = 6378137.0  # Semi-major radius (m)
_F = 1 / 298.257223563  # Flattening
_B = _A - _F * _A  # 6356752.3142, Semi-minor radius (m)
_A2 = _A * _A
_B2 = _B * _B
_E2 = (_A2 - _B2) / _A2  # 6.69437999014E-3, First eccentricity squared
_E4 = _E2 * _E2
_OME2 = 1.0 - _E2
_EB2 = (_A2 - _B2) / _B2


def ecf_to_geodetic(ecf: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """Converts WGS 84 cartesian coordinates to geodetic coordinates.

    Parameters
    ----------
    ecf : (..., 3) array_like
        Array of cartesian coordinates with X, Y, Z components in meters in the last dimension.

    Returns
    -------
    (..., 3) ndarray
        Array of geodetic coordinates with [latitude (deg), longitude (deg), and ellipsoidal height (m)] in the last
        dimension.

    """
    ecf = np.asarray(ecf)
    x = ecf[..., 0]
    y = ecf[..., 1]
    z = ecf[..., 2]

    llh = np.full(ecf.shape, np.nan, dtype=np.float64)

    r = np.sqrt((x * x) + (y * y))

    # Check for invalid solution
    valid = (_A * r) * (_A * r) + (_B * z) * (_B * z) > (_A2 - _B2) * (_A2 - _B2)

    # calculate intermediates
    f = 54.0 * _B2 * z * z  # not the WGS 84 flattening parameter
    g = r * r + _OME2 * z * z - _E2 * (_A2 - _B2)
    c = _E4 * f * r * r / (g * g * g)
    s = (1.0 + c + np.sqrt(c * c + 2 * c)) ** (1.0 / 3)
    p = f / (3.0 * (g * (s + 1.0 / s + 1.0)) ** 2)
    q = np.sqrt(1.0 + 2.0 * _E4 * p)
    r0 = -p * _E2 * r / (1.0 + q) + np.sqrt(
        np.abs(
            0.5 * _A2 * (1.0 + 1 / q)
            - p * _OME2 * z * z / (q * (1.0 + q))
            - 0.5 * p * r * r
        )
    )
    t = r - _E2 * r0
    u = np.sqrt(t * t + z * z)
    v = np.sqrt(t * t + _OME2 * z * z)
    z0 = _B2 * z / (_A * v)

    # calculate latitude
    llh[valid, 0] = np.rad2deg(np.arctan2(z[valid] + _EB2 * z0[valid], r[valid]))
    # calculate longitude
    llh[valid, 1] = np.rad2deg(np.arctan2(y[valid], x[valid]))
    # calculate ellipsoidal height
    llh[valid, 2] = u[valid] * (1.0 - _B2 / (_A * v[valid]))
    return llh


def geodetic_to_ecf(latlonhae: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """Converts WGS 84 geodetic coordinates to cartesian coordinates.

    Parameters
    ----------
    latlonhae : (..., 3) array_like
        Array of geodetic coordinates with [latitude (deg), longitude (deg), and ellipsoidal height (m)] in the last
        dimension.

    Returns
    -------
    (..., 3) ndarray
        Array of cartesian coordinates with X, Y, Z components in meters in the last dimension.

    """
    latlonhae = np.asarray(latlonhae)
    lat = np.deg2rad(latlonhae[..., 0])
    lon = np.deg2rad(latlonhae[..., 1])
    hae = latlonhae[..., 2]

    out = np.full(latlonhae.shape, np.nan, dtype=np.float64)
    # calculate distance to surface of ellipsoid
    r = _A / np.sqrt(1.0 - _E2 * np.sin(lat) * np.sin(lat))

    # calculate coordinates
    out[..., 0] = (r + hae) * np.cos(lat) * np.cos(lon)
    out[..., 1] = (r + hae) * np.cos(lat) * np.sin(lon)
    out[..., 2] = (r + hae - _E2 * r) * np.sin(lat)
    return out


def up(latlonhae: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """Compute local up unit vectors from WGS 84 geodetic coordinates.

    Parameters
    ----------
    latlonhae : (..., 3) array_like
        Array of geodetic coordinates with [latitude (deg), longitude (deg), and ellipsoidal height (m)] in the last
        dimension.

    Returns
    -------
    (..., 3) ndarray
        Array of local up unit vectors perpendicular to the local WGS-84 inflated ellipsoid with X, Y, Z components
        in meters in the last dimension.

    """
    latlonhae = np.asarray(latlonhae)
    lat = np.deg2rad(latlonhae[..., 0])
    lon = np.deg2rad(latlonhae[..., 1])
    return np.stack(
        [
            np.cos(lat) * np.cos(lon),
            np.cos(lat) * np.sin(lon),
            np.sin(lat),
        ],
        axis=-1,
    )


def north(latlonhae: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """Compute local north unit vectors from WGS 84 geodetic coordinates.

    Parameters
    ----------
    latlonhae : (..., 3) array_like
        Array of geodetic coordinates with [latitude (deg), longitude (deg), and ellipsoidal height (m)] in the last
        dimension.

    Returns
    -------
    (..., 3) ndarray
        Array of local north unit vectors with X, Y, Z components in meters in the last dimension.

    """
    latlonhae = np.asarray(latlonhae)
    lat = np.deg2rad(latlonhae[..., 0])
    lon = np.deg2rad(latlonhae[..., 1])
    return np.stack(
        [
            -np.sin(lat) * np.cos(lon),
            -np.sin(lat) * np.sin(lon),
            np.cos(lat),
        ],
        axis=-1,
    )


def east(latlonhae: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """Compute local east unit vectors from WGS 84 geodetic coordinates.

    Parameters
    ----------
    latlonhae : (..., 3) array_like
        Array of geodetic coordinates with [latitude (deg), longitude (deg), and ellipsoidal height (m)] in the last
        dimension.

    Returns
    -------
    (..., 3) ndarray
        Array of local east unit vectors with X, Y, Z components in meters in the last dimension.

    """
    latlonhae = np.asarray(latlonhae)
    lon = np.deg2rad(latlonhae[..., 1])
    return np.stack(
        [
            -np.sin(lon),
            np.cos(lon),
            np.zeros_like(lon),
        ],
        axis=-1,
    )
