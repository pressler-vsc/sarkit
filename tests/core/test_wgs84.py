import numpy as np
import pytest

import sarkit.wgs84

EQUATORIAL_RADIUS = 6378137
POLAR_RADIUS = 6356752.314245179
TOLERANCE = 1e-8

TESTPOINTS = {
    "llh": np.array([[0, 0, 0], [0, 180, 0], [90, 0, 0], [-90, 0, 0], [0, 90, 0]]),
    "ecf": np.array(
        [
            [EQUATORIAL_RADIUS, 0, 0],
            [-EQUATORIAL_RADIUS, 0, 0],
            [0, 0, POLAR_RADIUS],
            [0, 0, -POLAR_RADIUS],
            [0, EQUATORIAL_RADIUS, 0],
        ]
    ),
}


def test_ecf_to_geodetic():
    out = sarkit.wgs84.cartesian_to_geodetic(TESTPOINTS["ecf"])
    assert out == pytest.approx(TESTPOINTS["llh"], abs=TOLERANCE)


def test_geodetic_to_ecf():
    out = sarkit.wgs84.geodetic_to_cartesian(TESTPOINTS["llh"])
    assert out == pytest.approx(TESTPOINTS["ecf"], abs=TOLERANCE)


def test_values_both_ways():
    shp = (8, 7, 5)
    rand_llh = np.empty(shp + (3,), dtype=np.float64)
    rng = np.random.default_rng(314159)
    rand_llh[..., 0] = 180 * (rng.random(shp) - 0.5)
    rand_llh[..., 1] = 360 * (rng.random(shp) - 0.5)
    rand_llh[..., 2] = 1e5 * rng.random(shp)

    rand_ecf = sarkit.wgs84.geodetic_to_cartesian(rand_llh)
    rand_llh2 = sarkit.wgs84.cartesian_to_geodetic(rand_ecf)
    rand_ecf2 = sarkit.wgs84.geodetic_to_cartesian(rand_llh2)

    # llh match
    assert rand_llh == pytest.approx(rand_llh2, abs=TOLERANCE)

    # ecf match
    assert rand_ecf == pytest.approx(rand_ecf2, abs=TOLERANCE)


def test_up():
    assert sarkit.wgs84.up([0, 0, 0]) == pytest.approx([1, 0, 0], abs=1e-10)
    assert sarkit.wgs84.up([0, 90, 0]) == pytest.approx([0, 1, 0], abs=1e-10)
    assert sarkit.wgs84.up([90, 0, 0]) == pytest.approx([0, 0, 1], abs=1e-10)
    assert sarkit.wgs84.up([45, 45, 0]) == pytest.approx(
        [0.5, 0.5, 1.0 / np.sqrt(2)], abs=1e-10
    )


def test_north():
    assert sarkit.wgs84.north((0, 0, 0)) == pytest.approx([0, 0, 1], abs=1e-10)
    assert sarkit.wgs84.north((0, 90, 0)) == pytest.approx([0, 0, 1], abs=1e-10)
    assert sarkit.wgs84.north((45, 0, 0)) == pytest.approx(
        [-np.sqrt(2) / 2.0, 0, np.sqrt(2) / 2.0], abs=1e-10
    )


def test_east():
    assert sarkit.wgs84.east((0, 0, 0)) == pytest.approx([0, 1, 0], abs=1e-10)
    assert sarkit.wgs84.east((45, 0, 0)) == pytest.approx([0, 1, 0], abs=1e-10)
    assert sarkit.wgs84.east((0, 90, 0)) == pytest.approx([-1, 0, 0], abs=1e-10)
    assert sarkit.wgs84.east((45, 90, 0)) == pytest.approx([-1, 0, 0], abs=1e-10)
