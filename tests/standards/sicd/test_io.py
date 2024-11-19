import pathlib

import lxml.etree
import numpy as np
import pytest

import sarpy.standards.general.nitf
import sarpy.standards.sicd.io
import sarpy.standards.sicd.xml

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


def _random_image(sicd_xmltree):
    xml_helper = sarpy.standards.sicd.xml.XmlHelper(sicd_xmltree)
    rows = xml_helper.load("./{*}ImageData/{*}NumRows")
    cols = xml_helper.load("./{*}ImageData/{*}NumCols")
    shape = (rows, cols)

    assert sicd_xmltree.findtext("./{*}ImageData/{*}PixelType") == "RE32F_IM32F"

    return np.random.default_rng().random(
        shape, dtype=np.float32
    ) + 1j * np.random.default_rng().random(shape, dtype=np.float32)


@pytest.mark.parametrize(
    "sicd_xml",
    [
        DATAPATH / "example-sicd-1.1.0.xml",
        DATAPATH / "example-sicd-1.2.1.xml",
        DATAPATH / "example-sicd-1.3.0.xml",
        DATAPATH / "example-sicd-1.4.0.xml",
    ],
)
def test_roundtrip(tmp_path, sicd_xml):
    out_sicd = tmp_path / "out.sicd"
    basis_etree = lxml.etree.parse(sicd_xml)
    basis_array = _random_image(basis_etree)
    basis_version = lxml.etree.QName(basis_etree.getroot()).namespace
    schema = lxml.etree.XMLSchema(
        file=sarpy.standards.sicd.io.VERSION_INFO[basis_version]["schema"]
    )
    schema.assertValid(basis_etree)

    nitf_plan = sarpy.standards.sicd.io.SicdNitfPlan(
        sicd_xmltree=basis_etree,
        header_fields={
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
        is_fields={
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
        des_fields={
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
    with sarpy.standards.sicd.io.SicdNitfWriter(out_sicd, nitf_plan) as writer:
        half_rows, half_cols = np.asarray(basis_array.shape) // 2
        writer.write_image(basis_array[:half_rows, :half_cols], start=(0, 0))
        writer.write_image(basis_array[:half_rows, half_cols:], start=(0, half_cols))
        writer.write_image(
            basis_array[half_rows:, half_cols:], start=(half_rows, half_cols)
        )
        writer.write_image(basis_array[half_rows:, :half_cols], start=(half_rows, 0))

    with sarpy.standards.sicd.io.SicdNitfReader(out_sicd) as reader:
        read_array = reader.read_image()

    schema.assertValid(reader.sicd_xmltree)
    assert lxml.etree.tostring(
        reader.sicd_xmltree, method="c14n"
    ) == lxml.etree.tostring(nitf_plan.sicd_xmltree, method="c14n")
    assert nitf_plan.header_fields == reader.header_fields
    assert nitf_plan.is_fields == reader.is_fields
    assert nitf_plan.des_fields == reader.des_fields
    assert np.array_equal(basis_array, read_array)


def test_file_objects(tmp_path):
    sicd_xml = DATAPATH / "example-sicd-1.3.0.xml"
    basis_etree = lxml.etree.parse(sicd_xml)
    basis_array = _random_image(basis_etree)

    plan = sarpy.standards.sicd.io.SicdNitfPlan(
        sicd_xmltree=basis_etree,
        header_fields={"ostaid": "testing", "security": {"clas": "U"}},
        is_fields={
            "isorce": basis_etree.findtext(".//{*}CollectorName"),
            "security": {"clas": "U"},
        },
        des_fields={"security": {"clas": "U"}},
    )
    out_with_path = tmp_path / "filename.sicd"
    with sarpy.standards.sicd.io.SicdNitfWriter(out_with_path, plan) as writer:
        writer.write_image(basis_array)

    out_with_obj = tmp_path / "file_obj.sicd"
    with out_with_obj.open("wb") as file:
        with sarpy.standards.sicd.io.SicdNitfWriter(file, plan) as writer:
            writer.write_image(basis_array)

    with out_with_path.open("rb") as file:
        with sarpy.standards.sicd.io.SicdNitfReader(file) as path_reader:
            array_from_path = path_reader.read_image()
    with sarpy.standards.sicd.io.SicdNitfReader(out_with_obj) as obj_reader:
        array_from_obj = obj_reader.read_image()

    assert lxml.etree.tostring(
        path_reader.sicd_xmltree, method="c14n"
    ) == lxml.etree.tostring(basis_etree, method="c14n")
    assert lxml.etree.tostring(
        path_reader.sicd_xmltree, method="c14n"
    ) == lxml.etree.tostring(obj_reader.sicd_xmltree, method="c14n")
    assert path_reader.header_fields == obj_reader.header_fields
    assert path_reader.is_fields == obj_reader.is_fields
    assert path_reader.des_fields == obj_reader.des_fields
    np.testing.assert_array_equal(array_from_path, array_from_obj)


def test_nitfheaderfields_from_header():
    header = sarpy.standards.general.nitf.NITFHeader()
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

    fields = sarpy.standards.sicd.io.SicdNitfHeaderFields.from_header(header)
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
    header = sarpy.standards.general.nitf.ImageSegmentHeader(PVTYPE="INT")
    header.ISORCE = "isorce"
    header.Comments = sarpy.standards.general.nitf_elements.image.ImageComments(
        [
            sarpy.standards.general.nitf_elements.image.ImageComment(COMMENT=comment)
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

    fields = sarpy.standards.sicd.io.SicdNitfImageSegmentFields.from_header(header)
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
    header = sarpy.standards.general.nitf.DataExtensionHeader(PVTYPE="INT")
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

    fields = sarpy.standards.sicd.io.SicdNitfDESegmentFields.from_header(header)
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


def test_read_sicd_xml(tmp_path):
    sicd_xml = DATAPATH / "example-sicd-1.3.0.xml"
    basis_etree = lxml.etree.parse(sicd_xml)
    basis_array = _random_image(basis_etree)

    direct_etree = sarpy.standards.sicd.io.read_sicd_xml(sicd_xml)
    assert isinstance(direct_etree, lxml.etree._ElementTree)
    assert lxml.etree.tostring(basis_etree, method="c14n") == lxml.etree.tostring(
        direct_etree, method="c14n"
    )

    plan = sarpy.standards.sicd.io.SicdNitfPlan(
        sicd_xmltree=basis_etree,
        header_fields={"ostaid": "testing", "security": {"clas": "U"}},
        is_fields={
            "isorce": basis_etree.findtext(".//{*}CollectorName"),
            "security": {"clas": "U"},
        },
        des_fields={"security": {"clas": "U"}},
    )
    out_filename = tmp_path / "filename.sicd"
    with sarpy.standards.sicd.io.SicdNitfWriter(out_filename, plan) as writer:
        writer.write_image(basis_array)

    nitf_etree = sarpy.standards.sicd.io.read_sicd_xml(out_filename)
    assert isinstance(nitf_etree, lxml.etree._ElementTree)
    assert lxml.etree.tostring(basis_etree, method="c14n") == lxml.etree.tostring(
        nitf_etree, method="c14n"
    )


def test_version_info():
    actual_order = [x["version"] for x in sarpy.standards.sicd.io.VERSION_INFO.values()]
    expected_order = sorted(actual_order, key=lambda x: x.split("."))
    assert actual_order == expected_order

    for urn, info in sarpy.standards.sicd.io.VERSION_INFO.items():
        assert lxml.etree.parse(info["schema"]).getroot().get("targetNamespace") == urn
