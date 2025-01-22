import pathlib

import lxml.etree
import numpy as np

import sarkit.standards.crsd.io
import sarkit.standards.crsd.xml

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


def test_transcoders():
    used_transcoders = set()
    no_transcode_leaf = set()
    for xml_file in (DATAPATH / "syntax_only/crsd").glob("*.xml"):
        etree = lxml.etree.parse(xml_file)
        basis_version = lxml.etree.QName(etree.getroot()).namespace
        schema = lxml.etree.XMLSchema(
            file=sarkit.standards.crsd.io.VERSION_INFO[basis_version]["schema"]
        )
        schema.assertValid(etree)
        xml_helper = sarkit.standards.crsd.xml.XmlHelper(etree)
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
    unused_transcoders = sarkit.standards.crsd.xml.TRANSCODERS.keys() - used_transcoders
    assert not unused_transcoders
    assert not no_transcode_leaf
