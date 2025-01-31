import datetime

import lxml.etree
import numpy as np
import pytest

import sarkit.xmlhelp


def test_xdt_naive():
    dt = datetime.datetime.now()
    elem = sarkit.xmlhelp.XdtType().make_elem("Xdt", dt)
    assert sarkit.xmlhelp.XdtType().parse_elem(elem) == dt.replace(
        tzinfo=datetime.timezone.utc
    )


def test_xdt_aware():
    dt = datetime.datetime.now(
        tz=datetime.timezone(offset=datetime.timedelta(hours=5.5))
    )
    elem = sarkit.xmlhelp.XdtType().make_elem("Xdt", dt)
    assert sarkit.xmlhelp.XdtType().parse_elem(elem) == dt


@pytest.mark.parametrize("ndim", (1, 2))
def test_poly(ndim):
    shape = np.arange(3, 3 + ndim)
    coefs = np.arange(np.prod(shape)).reshape(shape)
    polytype = sarkit.xmlhelp.PolyNdType(ndim)
    elem = polytype.make_elem("Poly", coefs)
    assert np.array_equal(polytype.parse_elem(elem), coefs)


def test_xyzpoly():
    coefs = np.linspace(-10, 10, 33).reshape((11, 3))
    elem = sarkit.xmlhelp.XyzPolyType().make_elem("{faux-ns}XyzPoly", coefs)
    assert np.array_equal(sarkit.xmlhelp.XyzPolyType().parse_elem(elem), coefs)


def test_xyz():
    xyz = [-10.0, 10.0, 0.20]
    elem = sarkit.xmlhelp.XyzType().make_elem("{faux-ns}XyzNode", xyz)
    assert np.array_equal(sarkit.xmlhelp.XyzType().parse_elem(elem), xyz)


def test_txt():
    elem = lxml.etree.Element("{faux-ns}Node")
    assert sarkit.xmlhelp.TxtType().parse_elem(elem) == ""
    new_str = "replacement string"
    new_elem = sarkit.xmlhelp.TxtType().make_elem("Txt", new_str)
    assert sarkit.xmlhelp.TxtType().parse_elem(new_elem) == new_str


@pytest.mark.parametrize("val", (True, False))
def test_bool(val):
    elem = sarkit.xmlhelp.BoolType().make_elem("node", val)
    assert sarkit.xmlhelp.BoolType().parse_elem(elem) == val


@pytest.mark.parametrize("val", (1.23, -4.56j, 1.23 - 4.56j))
def test_cmplx(val):
    elem = sarkit.xmlhelp.CmplxType().make_elem("node", val)
    assert sarkit.xmlhelp.CmplxType().parse_elem(elem) == val


def test_line_samp():
    ls_data = [1000, 2000]
    type_obj = sarkit.xmlhelp.LineSampType()
    elem = type_obj.make_elem("{faux-ns}LsNode", ls_data)
    assert np.array_equal(type_obj.parse_elem(elem), ls_data)


def test_array():
    data = np.random.default_rng().random((3,))
    elem = lxml.etree.Element("{faux-ns}ArrayDblNode")
    type_obj = sarkit.xmlhelp.ArrayType(
        {c: sarkit.xmlhelp.DblType() for c in ("a", "b", "c")}
    )
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)
    with pytest.raises(ValueError, match="len.*does not match expected"):
        type_obj.set_elem(elem, np.tile(data, 2))


def test_xy():
    xy = [-10.0, 10.0]
    elem = sarkit.xmlhelp.XyType().make_elem("{faux-ns}XyNode", xy)
    assert np.array_equal(sarkit.xmlhelp.XyType().parse_elem(elem), xy)


def test_hex():
    hexval = b"\xba\xdd"
    elem = sarkit.xmlhelp.HexType().make_elem("{faux-ns}HexNode", hexval)
    assert np.array_equal(sarkit.xmlhelp.HexType().parse_elem(elem), hexval)


def test_parameter():
    name = "TestName"
    val = "TestVal"
    elem = sarkit.xmlhelp.ParameterType().make_elem("{faux-ns}Parameter", (name, val))
    assert sarkit.xmlhelp.ParameterType().parse_elem(elem) == (name, val)
