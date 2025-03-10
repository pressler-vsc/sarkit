import pathlib

import lxml.etree
import numpy as np
import pytest

import sarkit._nitf.nitf
import sarkit.sicd as sksicd

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


def _random_image(sicd_xmltree):
    xml_helper = sksicd.XmlHelper(sicd_xmltree)
    rows = xml_helper.load("./{*}ImageData/{*}NumRows")
    cols = xml_helper.load("./{*}ImageData/{*}NumCols")
    shape = (rows, cols)

    assert sicd_xmltree.findtext("./{*}ImageData/{*}PixelType") == "RE32F_IM32F"

    components = (
        2 * np.random.default_rng().random(shape + (2,), dtype=np.float32)
    ) - 1
    return components.astype(">f4").view(">c8").squeeze()


@pytest.mark.parametrize(
    "sicd_xml,pixel_type",
    [
        (DATAPATH / "example-sicd-1.1.0.xml", "RE32F_IM32F"),
        (DATAPATH / "example-sicd-1.2.1.xml", "RE16I_IM16I"),
        (DATAPATH / "example-sicd-1.3.0.xml", "AMP8I_PHS8I"),
        (DATAPATH / "example-sicd-1.4.0.xml", "RE32F_IM32F"),
    ],
)
def test_roundtrip(tmp_path, sicd_xml, pixel_type):
    out_sicd = tmp_path / "out.sicd"
    basis_etree = lxml.etree.parse(sicd_xml)
    basis_array = _random_image(basis_etree)

    dtype = sksicd.PIXEL_TYPES[pixel_type]["dtype"]
    if pixel_type == "RE16I_IM16I":
        basis_array = (
            (np.iinfo(dtype["real"]).max * basis_array.view(basis_array.real.dtype))
            .astype(dtype["real"])
            .view(dtype)
        )
    if pixel_type == "AMP8I_PHS8I":
        basis_array = (
            (
                np.iinfo(dtype["amp"]).max
                * np.abs(basis_array.view(basis_array.real.dtype))
            )
            .astype(dtype["amp"])
            .view(dtype)
        )
    basis_etree.find("{*}ImageData/{*}PixelType").text = pixel_type
    basis_version = lxml.etree.QName(basis_etree.getroot()).namespace
    schema = lxml.etree.XMLSchema(file=sksicd.VERSION_INFO[basis_version]["schema"])
    schema.assertValid(basis_etree)

    metadata = sksicd.NitfMetadata(
        xmltree=basis_etree,
        file_header_part={
            "ostaid": "ostaid",
            "ftitle": "ftitle",
            # Data is unclassified.  These fields are filled for testing purposes only.
            "security": {
                "clas": "T",
                "clsy": "US",
                "code": "code_h",
                "ctlh": "hh",
                "rel": "rel_h",
                "dctp": "DD",
                "dcdt": "20000101",
                "dcxm": "25X1",
                "dg": "C",
                "dgdt": "20000102",
                "cltx": "CW_h",
                "catp": "O",
                "caut": "caut_h",
                "crsn": "A",
                "srdt": "",
                "ctln": "ctln_h",
            },
            "oname": "oname",
            "ophone": "ophone",
        },
        im_subheader_part={
            "tgtid": "tgtid",
            "iid2": "iid2",
            # Data is unclassified.  These fields are filled for testing purposes only.
            "security": {
                "clas": "S",
                "clsy": "II",
                "code": "code_i",
                "ctlh": "ii",
                "rel": "rel_i",
                "dctp": "",
                "dcdt": "",
                "dcxm": "X2",
                "dg": "R",
                "dgdt": "20000202",
                "cltx": "RL_i",
                "catp": "D",
                "caut": "caut_i",
                "crsn": "B",
                "srdt": "20000203",
                "ctln": "ctln_i",
            },
            "isorce": "isorce",
            "icom": ["first comment", "second comment"],
        },
        de_subheader_part={
            # Data is unclassified.  These fields are filled for testing purposes only.
            "security": {
                "clas": "U",
                "clsy": "DD",
                "code": "code_d",
                "ctlh": "dd",
                "rel": "rel_d",
                "dctp": "X",
                "dcdt": "",
                "dcxm": "X3",
                "dg": "",
                "dgdt": "20000302",
                "cltx": "CH_d",
                "catp": "M",
                "caut": "caut_d",
                "crsn": "C",
                "srdt": "20000303",
                "ctln": "ctln_d",
            },
            "desshrp": "desshrp",
            "desshli": "desshli",
            "desshlin": "desshlin",
            "desshabs": "desshabs",
        },
    )
    with out_sicd.open("wb") as f:
        with sksicd.NitfWriter(f, metadata) as writer:
            half_rows, half_cols = np.asarray(basis_array.shape) // 2
            writer.write_image(basis_array[:half_rows, :half_cols], start=(0, 0))
            writer.write_image(
                basis_array[:half_rows, half_cols:], start=(0, half_cols)
            )
            writer.write_image(
                basis_array[half_rows:, half_cols:], start=(half_rows, half_cols)
            )
            writer.write_image(
                basis_array[half_rows:, :half_cols], start=(half_rows, 0)
            )

    with out_sicd.open("rb") as f, sksicd.NitfReader(f) as reader:
        read_array = reader.read_image()

    schema.assertValid(reader.metadata.xmltree)
    assert metadata == reader.metadata
    assert np.array_equal(basis_array, read_array)


def test_nitfheaderfields_from_header():
    header = sarkit._nitf.nitf.NITFHeader()
    header.OSTAID = "ostaid"
    header.FTITLE = "ftitle"
    # Data is unclassified.  These fields are filled for testing purposes only.
    header.Security.CLAS = "T"
    header.Security.CLSY = "US"
    header.Security.CODE = "code_h"
    header.Security.CTLH = "hh"
    header.Security.REL = "rel_h"
    header.Security.DCTP = "DD"
    header.Security.DCDT = "20000101"
    header.Security.DCXM = "25X1"
    header.Security.DG = "C"
    header.Security.DGDT = "20000102"
    header.Security.CLTX = "CW_h"
    header.Security.CATP = "O"
    header.Security.CAUT = "caut_h"
    header.Security.CRSN = "A"
    header.Security.SRDT = ""
    header.Security.CTLN = "ctln_h"
    header.ONAME = "oname"
    header.OPHONE = "ophone"

    fields = sksicd.NitfFileHeaderPart._from_header(header)
    assert fields.ostaid == header.OSTAID
    assert fields.ftitle == header.FTITLE
    assert fields.security.clas == header.Security.CLAS
    assert fields.security.clsy == header.Security.CLSY
    assert fields.security.code == header.Security.CODE
    assert fields.security.ctlh == header.Security.CTLH
    assert fields.security.rel == header.Security.REL
    assert fields.security.dctp == header.Security.DCTP
    assert fields.security.dcxm == header.Security.DCXM
    assert fields.security.dg == header.Security.DG
    assert fields.security.dgdt == header.Security.DGDT
    assert fields.security.cltx == header.Security.CLTX
    assert fields.security.catp == header.Security.CATP
    assert fields.security.caut == header.Security.CAUT
    assert fields.security.crsn == header.Security.CRSN
    assert fields.security.srdt == header.Security.SRDT
    assert fields.security.ctln == header.Security.CTLN
    assert fields.oname == header.ONAME
    assert fields.ophone == header.OPHONE


def test_nitfimagesegmentfields_from_header():
    comments = ["first", "second"]
    header = sarkit._nitf.nitf.ImageSegmentHeader(PVTYPE="INT")
    header.ISORCE = "isorce"
    header.Comments = sarkit._nitf.nitf_elements.image.ImageComments(
        [
            sarkit._nitf.nitf_elements.image.ImageComment(COMMENT=comment)
            for comment in comments
        ]
    )
    # Data is unclassified.  These fields are filled for testing purposes only.
    header.Security.CLAS = "T"
    header.Security.CLSY = "US"
    header.Security.CODE = "code_h"
    header.Security.CTLH = "hh"
    header.Security.REL = "rel_h"
    header.Security.DCTP = "DD"
    header.Security.DCDT = "20000101"
    header.Security.DCXM = "25X1"
    header.Security.DG = "C"
    header.Security.DGDT = "20000102"
    header.Security.CLTX = "CW_h"
    header.Security.CATP = "O"
    header.Security.CAUT = "caut_h"
    header.Security.CRSN = "A"
    header.Security.SRDT = ""
    header.Security.CTLN = "ctln_h"

    fields = sksicd.NitfImSubheaderPart._from_header(header)
    assert fields.isorce == header.ISORCE
    assert fields.icom == comments
    assert fields.security.clas == header.Security.CLAS
    assert fields.security.clsy == header.Security.CLSY
    assert fields.security.code == header.Security.CODE
    assert fields.security.ctlh == header.Security.CTLH
    assert fields.security.rel == header.Security.REL
    assert fields.security.dctp == header.Security.DCTP
    assert fields.security.dcxm == header.Security.DCXM
    assert fields.security.dg == header.Security.DG
    assert fields.security.dgdt == header.Security.DGDT
    assert fields.security.cltx == header.Security.CLTX
    assert fields.security.catp == header.Security.CATP
    assert fields.security.caut == header.Security.CAUT
    assert fields.security.crsn == header.Security.CRSN
    assert fields.security.srdt == header.Security.SRDT
    assert fields.security.ctln == header.Security.CTLN


def test_nitfdesegmentfields_from_header():
    header = sarkit._nitf.nitf.DataExtensionHeader(PVTYPE="INT")
    header.UserHeader.DESSHRP = "desshrp"
    header.UserHeader.DESSHLI = "desshli"
    header.UserHeader.DESSHLIN = "desshlin"
    header.UserHeader.DESSHABS = "desshabs"
    # Data is unclassified.  These fields are filled for testing purposes only.
    header.Security.CLAS = "T"
    header.Security.CLSY = "US"
    header.Security.CODE = "code_h"
    header.Security.CTLH = "hh"
    header.Security.REL = "rel_h"
    header.Security.DCTP = "DD"
    header.Security.DCDT = "20000101"
    header.Security.DCXM = "25X1"
    header.Security.DG = "C"
    header.Security.DGDT = "20000102"
    header.Security.CLTX = "CW_h"
    header.Security.CATP = "O"
    header.Security.CAUT = "caut_h"
    header.Security.CRSN = "A"
    header.Security.SRDT = ""
    header.Security.CTLN = "ctln_h"

    fields = sksicd.NitfDeSubheaderPart._from_header(header)
    assert fields.desshrp == header.UserHeader.DESSHRP
    assert fields.desshli == header.UserHeader.DESSHLI
    assert fields.desshlin == header.UserHeader.DESSHLIN
    assert fields.desshabs == header.UserHeader.DESSHABS
    assert fields.security.clas == header.Security.CLAS
    assert fields.security.clsy == header.Security.CLSY
    assert fields.security.code == header.Security.CODE
    assert fields.security.ctlh == header.Security.CTLH
    assert fields.security.rel == header.Security.REL
    assert fields.security.dctp == header.Security.DCTP
    assert fields.security.dcxm == header.Security.DCXM
    assert fields.security.dg == header.Security.DG
    assert fields.security.dgdt == header.Security.DGDT
    assert fields.security.cltx == header.Security.CLTX
    assert fields.security.catp == header.Security.CATP
    assert fields.security.caut == header.Security.CAUT
    assert fields.security.crsn == header.Security.CRSN
    assert fields.security.srdt == header.Security.SRDT
    assert fields.security.ctln == header.Security.CTLN


def test_version_info():
    actual_order = [x["version"] for x in sksicd.VERSION_INFO.values()]
    expected_order = sorted(actual_order, key=lambda x: x.split("."))
    assert actual_order == expected_order

    for urn, info in sksicd.VERSION_INFO.items():
        assert lxml.etree.parse(info["schema"]).getroot().get("targetNamespace") == urn
