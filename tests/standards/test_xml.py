import datetime

import lxml.etree
import numpy as np
import pytest

import sarkit.standards.xml


def test_xdt_naive():
    dt = datetime.datetime.now()
    elem = sarkit.standards.xml.XdtType().make_elem("Xdt", dt)
    assert sarkit.standards.xml.XdtType().parse_elem(elem) == dt.replace(
        tzinfo=datetime.timezone.utc
    )


def test_xdt_aware():
    dt = datetime.datetime.now(
        tz=datetime.timezone(offset=datetime.timedelta(hours=5.5))
    )
    elem = sarkit.standards.xml.XdtType().make_elem("Xdt", dt)
    assert sarkit.standards.xml.XdtType().parse_elem(elem) == dt


@pytest.mark.parametrize("ndim", (1, 2))
def test_poly(ndim):
    shape = np.arange(3, 3 + ndim)
    coefs = np.arange(np.prod(shape)).reshape(shape)
    polytype = sarkit.standards.xml.PolyType(ndim)
    elem = polytype.make_elem("Poly", coefs)
    assert np.array_equal(polytype.parse_elem(elem), coefs)


def test_xyzpoly():
    coefs = np.linspace(-10, 10, 33).reshape((11, 3))
    elem = sarkit.standards.xml.XyzPolyType().make_elem("{faux-ns}XyzPoly", coefs)
    assert np.array_equal(sarkit.standards.xml.XyzPolyType().parse_elem(elem), coefs)


def test_xyz():
    xyz = [-10.0, 10.0, 0.20]
    elem = sarkit.standards.xml.XyzType().make_elem("{faux-ns}XyzNode", xyz)
    assert np.array_equal(sarkit.standards.xml.XyzType().parse_elem(elem), xyz)


def test_txt():
    elem = lxml.etree.Element("{faux-ns}Node")
    assert sarkit.standards.xml.TxtType().parse_elem(elem) == ""
    new_str = "replacement string"
    new_elem = sarkit.standards.xml.TxtType().make_elem("Txt", new_str)
    assert sarkit.standards.xml.TxtType().parse_elem(new_elem) == new_str


@pytest.mark.parametrize("val", (True, False))
def test_bool(val):
    elem = sarkit.standards.xml.BoolType().make_elem("node", val)
    assert sarkit.standards.xml.BoolType().parse_elem(elem) == val


@pytest.mark.parametrize("val", (1.23, -4.56j, 1.23 - 4.56j))
def test_cmplx(val):
    elem = sarkit.standards.xml.CmplxType().make_elem("node", val)
    assert sarkit.standards.xml.CmplxType().parse_elem(elem) == val


def test_line_samp():
    ls_data = [1000, 2000]
    type_obj = sarkit.standards.xml.LineSampType()
    elem = type_obj.make_elem("{faux-ns}LsNode", ls_data)
    assert np.array_equal(type_obj.parse_elem(elem), ls_data)


def test_array():
    data = np.random.default_rng().random((3,))
    elem = lxml.etree.Element("{faux-ns}ArrayDblNode")
    type_obj = sarkit.standards.xml.ArrayType(
        {c: sarkit.standards.xml.DblType() for c in ("a", "b", "c")}
    )
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)
    with pytest.raises(ValueError, match="len.*does not match expected"):
        type_obj.set_elem(elem, np.tile(data, 2))


def test_xy():
    xy = [-10.0, 10.0]
    elem = sarkit.standards.xml.XyType().make_elem("{faux-ns}XyNode", xy)
    assert np.array_equal(sarkit.standards.xml.XyType().parse_elem(elem), xy)


def test_hex():
    hexval = b"\xba\xdd"
    elem = sarkit.standards.xml.HexType().make_elem("{faux-ns}HexNode", hexval)
    assert np.array_equal(sarkit.standards.xml.HexType().parse_elem(elem), hexval)


def test_parameter():
    name = "TestName"
    val = "TestVal"
    elem = sarkit.standards.xml.ParameterType().make_elem(
        "{faux-ns}Parameter", (name, val)
    )
    assert sarkit.standards.xml.ParameterType().parse_elem(elem) == (name, val)
