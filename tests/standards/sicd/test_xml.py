import copy
import pathlib

import lxml.etree
import numpy as np
import pytest

import sarpy.standards.sicd.io
import sarpy.standards.sicd.xml

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


def test_image_corners_type():
    etree = lxml.etree.parse(DATAPATH / "example-sicd-1.3.0.xml")
    xml_helper = sarpy.standards.sicd.xml.XmlHelper(etree)
    schema = lxml.etree.XMLSchema(
        file=sarpy.standards.sicd.io.VERSION_INFO["urn:SICD:1.3.0"]["schema"]
    )
    schema.assertValid(etree)

    new_corner_coords = np.array(
        [
            [-1.23, -4.56],
            [-7.89, -10.11],
            [16.17, 18.19],
            [12.13, 14.15],
        ]
    )
    xml_helper.set("./{*}GeoData/{*}ImageCorners", new_corner_coords)
    schema.assertValid(xml_helper.element_tree)
    assert np.array_equal(
        xml_helper.load("./{*}GeoData/{*}ImageCorners"), new_corner_coords
    )

    new_elem = sarpy.standards.sicd.xml.ImageCornersType().make_elem(
        "FauxIC", new_corner_coords
    )
    assert np.array_equal(
        sarpy.standards.sicd.xml.ImageCornersType().parse_elem(new_elem),
        new_corner_coords,
    )


def test_mtx_type():
    data = np.arange(np.prod(6)).reshape((2, 3))
    type_obj = sarpy.standards.sicd.xml.MtxType(data.shape)
    elem = type_obj.make_elem("{faux-ns}MtxNode", data)
    assert np.array_equal(type_obj.parse_elem(elem), data)

    with pytest.raises(ValueError, match="shape.*does not match expected"):
        type_obj.set_elem(elem, np.tile(data, 2))


def test_transcoders():
    used_transcoders = set()
    no_transcode_leaf = set()
    for xml_file in (DATAPATH / "syntax_only/sicd").glob("*.xml"):
        etree = lxml.etree.parse(xml_file)
        basis_version = lxml.etree.QName(etree.getroot()).namespace
        schema = lxml.etree.XMLSchema(
            file=sarpy.standards.sicd.io.VERSION_INFO[basis_version]["schema"]
        )
        schema.assertValid(etree)
        xml_helper = sarpy.standards.sicd.xml.XmlHelper(etree)
        for elem in reversed(list(xml_helper.element_tree.iter())):
            try:
                val = xml_helper.load_elem(elem)
                xml_helper.set_elem(elem, val)
                schema.assertValid(xml_helper.element_tree)
                np.testing.assert_equal(xml_helper.load_elem(elem), val)
                used_transcoders.add(xml_helper.get_transcoder_name(elem))
            except sarpy.standards.xml.NotTranscodableError:
                if len(elem) == 0:
                    no_transcode_leaf.add(xml_helper.element_tree.getelementpath(elem))
    unused_transcoders = sarpy.standards.sicd.xml.TRANSCODERS.keys() - used_transcoders
    assert not unused_transcoders
    assert not no_transcode_leaf


def _replace_scpcoa(sicd_xmltree):
    scpcoa = sarpy.standards.sicd.xml.compute_scp_coa(sicd_xmltree)
    sicd_xmltree.getroot().replace(sicd_xmltree.find(".//{*}SCPCOA"), scpcoa)
    basis_version = lxml.etree.QName(sicd_xmltree.getroot()).namespace
    schema = lxml.etree.XMLSchema(
        file=sarpy.standards.sicd.io.VERSION_INFO[basis_version]["schema"]
    )
    schema.assertValid(sicd_xmltree)
    return scpcoa


@pytest.mark.parametrize("xml_file", DATAPATH.glob("example-sicd*.xml"))
def test_compute_scp_coa(xml_file):
    _replace_scpcoa(lxml.etree.parse(xml_file))


def test_compute_scp_coa_bistatic():
    etree = lxml.etree.parse(DATAPATH / "example-sicd-1.3.0.xml")
    # Monostatic
    assert etree.findtext("./{*}CollectionInfo/{*}CollectType") == "MONOSTATIC"
    scpcoa_mono = _replace_scpcoa(copy.deepcopy(etree))
    assert scpcoa_mono.find(".//{*}Bistatic") is None

    # Bistatic
    etree_bistatic = copy.deepcopy(etree)
    for elem in etree_bistatic.iter():
        elem.tag = f"{{urn:SICD:1.4.0}}{lxml.etree.QName(elem).localname}"
    xmlhelp_bistatic = sarpy.standards.sicd.xml.XmlHelper(etree_bistatic)
    xmlhelp_bistatic.set("./{*}CollectionInfo/{*}CollectType", "BISTATIC")
    scpcoa_bistatic_diff = _replace_scpcoa(etree_bistatic)
    assert scpcoa_bistatic_diff.find(".//{*}Bistatic") is not None