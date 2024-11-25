import pathlib

import lxml.etree
import numpy as np
import pytest

import sarkit.standards.cphd.io
import sarkit.standards.cphd.xml

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


def test_pvp():
    pvp_dict = {"Offset": 11, "Size": 1, "dtype": np.dtype("float64")}
    elem = sarkit.standards.cphd.xml.PvpType().make_elem("{faux-ns}PvpNode", pvp_dict)
    assert sarkit.standards.cphd.xml.PvpType().parse_elem(elem) == pvp_dict

    with pytest.raises(TypeError):
        pvp_dict = {"Offset": 11, "Size": 1, "dtype": "F8"}
        sarkit.standards.cphd.xml.PvpType().set_elem(elem, pvp_dict)

    with pytest.raises(ValueError):
        added_pvp_dict = {
            "Name": "ADDED_PVP",
            "Offset": 11,
            "Size": 1,
            "dtype": np.dtype("float64"),
        }
        sarkit.standards.cphd.xml.PvpType().set_elem(elem, added_pvp_dict)


def test_addedpvp():
    added_pvp_dict = {
        "Name": "ADDED_PVP",
        "Offset": 11,
        "Size": 1,
        "dtype": np.dtype("float64"),
    }
    elem = sarkit.standards.cphd.xml.AddedPvpType().make_elem(
        "{faux-ns}AddedPvpNode", added_pvp_dict
    )
    assert sarkit.standards.cphd.xml.AddedPvpType().parse_elem(elem) == added_pvp_dict


def test_transcoders():
    used_transcoders = set()
    no_transcode_leaf = set()
    for xml_file in (DATAPATH / "syntax_only/cphd").glob("*.xml"):
        etree = lxml.etree.parse(xml_file)
        basis_version = lxml.etree.QName(etree.getroot()).namespace
        schema = lxml.etree.XMLSchema(
            file=sarkit.standards.cphd.io.VERSION_INFO[basis_version]["schema"]
        )
        schema.assertValid(etree)
        xml_helper = sarkit.standards.cphd.xml.XmlHelper(etree)
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
    unused_transcoders = sarkit.standards.cphd.xml.TRANSCODERS.keys() - used_transcoders
    assert not unused_transcoders
    assert not no_transcode_leaf
