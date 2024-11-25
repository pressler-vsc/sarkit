import importlib
import pathlib

import lxml.etree
import numpy as np

import sarkit.standards.sidd.xml

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


def test_anglemagnitude():
    data = np.random.default_rng().random((2,))
    elem = lxml.etree.Element("{faux-ns}AngleMagnitude")
    type_obj = sarkit.standards.sidd.xml.AngleMagnitudeType(child_ns="urn:SICommon:1.0")
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)


def test_filtercoefficient():
    data = np.random.default_rng().random((4, 7))
    elem = lxml.etree.Element("{faux-ns}FilterCoefficients")
    type_obj = sarkit.standards.sidd.xml.FilterCoefficientType("rowcol")
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)
    type_obj = sarkit.standards.sidd.xml.FilterCoefficientType("phasingpoint")
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)


def test_intlist():
    data = np.random.default_rng().integers(256, size=11)
    elem = lxml.etree.Element("{faux-ns}IntList")
    type_obj = sarkit.standards.sidd.xml.IntListType()
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)


def test_image_corners_type():
    data = np.array(
        [
            [-1.23, -4.56],
            [-7.89, -10.11],
            [16.17, 18.19],
            [12.13, 14.15],
        ]
    )
    elem = lxml.etree.Element("{faux-ns}ImageCorners")
    type_obj = sarkit.standards.sidd.xml.ImageCornersType()
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)


def test_rangeazimuth():
    data = np.random.default_rng().random((2,))
    elem = lxml.etree.Element("{faux-ns}RangeAzimuth")
    type_obj = sarkit.standards.sidd.xml.RangeAzimuthType(child_ns="urn:SICommon:1.0")
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)


def test_rowcoldble():
    data = np.random.default_rng().random((2,))
    elem = lxml.etree.Element("{faux-ns}RowColDbl")
    type_obj = sarkit.standards.sidd.xml.RowColDblType(child_ns="urn:SICommon:1.0")
    type_obj.set_elem(elem, data)
    assert np.array_equal(type_obj.parse_elem(elem), data)


def test_sfapointtype():
    data = [1.1, 1.2, 1.3]
    elem = sarkit.standards.sidd.xml.SfaPointType().make_elem("{ns}SfaPoint", data)
    assert np.array_equal(
        sarkit.standards.sidd.xml.SfaPointType().parse_elem(elem), data
    )
    sarkit.standards.sidd.xml.SfaPointType().set_elem(elem, data[:-1])
    assert np.array_equal(
        sarkit.standards.sidd.xml.SfaPointType().parse_elem(elem), data[:-1]
    )


def test_transcoders():
    used_transcoders = set()
    no_transcode_leaf = set()
    schema_dir = importlib.resources.files("sarkit.standards.sidd.schemas.version3")
    schema_file = schema_dir / "SIDD_schema_V3.0.0.xsd"
    for xml_file in (DATAPATH / "syntax_only/sidd").glob("*.xml"):
        etree = lxml.etree.parse(xml_file)
        schema = lxml.etree.XMLSchema(file=schema_file)
        schema.assertValid(etree)
        xml_helper = sarkit.standards.sidd.xml.XmlHelper(etree)
        for elem in reversed(list(xml_helper.element_tree.iter())):
            try:
                val = xml_helper.load_elem(elem)
                xml_helper.set_elem(elem, val)
                schema.assertValid(xml_helper.element_tree)
                np.testing.assert_equal(xml_helper.load_elem(elem), val)
                used_transcoders.add(xml_helper.get_transcoder_name(elem))
            except sarkit.standards.xml.NotTranscodableError:
                if len(elem) == 0:
                    no_transcode_leaf.add(xml_helper.element_tree.getelementpath(elem))
    unused_transcoders = sarkit.standards.sidd.xml.TRANSCODERS.keys() - used_transcoders
    assert not unused_transcoders

    todos = {xmlpath for xmlpath in no_transcode_leaf if "Classification" in xmlpath}
    assert not (no_transcode_leaf - todos)
