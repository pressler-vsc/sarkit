import pathlib

import lxml.etree
import numpy as np
import pytest

import sarkit._nitf.nitf
import sarkit.sidd as sksidd
import sarkit.sidd._io

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


def _random_image(sidd_xmltree):
    xml_helper = sksidd.XmlHelper(sidd_xmltree)
    rows = xml_helper.load("./{*}Measurement/{*}PixelFootprint/{*}Row")
    cols = xml_helper.load("./{*}Measurement/{*}PixelFootprint/{*}Col")
    shape = (rows, cols)

    assert xml_helper.load("./{*}Display/{*}PixelType") == "MONO8I"

    return np.random.default_rng().integers(
        0, 255, size=shape, dtype=np.uint8, endpoint=True
    )


@pytest.mark.parametrize("force_segmentation", [False, True])
@pytest.mark.parametrize(
    "sidd_xml",
    [
        DATAPATH / "example-sidd-2.0.0.xml",
        DATAPATH / "example-sidd-3.0.0.xml",
    ],
)
def test_roundtrip(force_segmentation, sidd_xml, tmp_path, monkeypatch):
    out_sidd = tmp_path / "out.sidd"
    sicd_xmltree = lxml.etree.parse(DATAPATH / "example-sicd-1.4.0.xml")
    basis_etree = lxml.etree.parse(sidd_xml)
    basis_array0 = _random_image(basis_etree)
    basis_array1 = 255 - basis_array0

    if force_segmentation:
        monkeypatch.setattr(
            sarkit.sidd._io, "LI_MAX", basis_array0.nbytes // 5
        )  # reduce the segment size limit to force segmentation

    write_metadata = sksidd.NitfMetadata(
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
        }
    )
    write_metadata.images.extend(
        [
            sksidd.NitfProductImageMetadata(
                xmltree=basis_etree,
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
            ),
            sksidd.NitfProductImageMetadata(
                xmltree=basis_etree,
                im_subheader_part={
                    "tgtid": "tgtid",
                    "iid2": "iid2",
                    "security": {
                        "clas": "U",
                    },
                },
                de_subheader_part={
                    "security": {
                        "clas": "U",
                    },
                },
            ),
        ]
    )

    write_metadata.sicd_xmls.extend(
        [
            sksidd.NitfSicdXmlMetadata(
                sicd_xmltree, de_subheader_part={"security": {"clas": "U"}}
            )
        ]
        * 2
    )

    ps_xmltree0 = lxml.etree.ElementTree(
        lxml.etree.fromstring("<product><support/></product>")
    )
    ps_xmltree1 = lxml.etree.ElementTree(
        lxml.etree.fromstring(
            '<product xmlns="https://example.com"><support/></product>'
        )
    )
    write_metadata.product_support_xmls.extend(
        [
            sksidd.NitfProductSupportXmlMetadata(
                ps_xmltree0, {"security": {"clas": "U"}}
            ),
            sksidd.NitfProductSupportXmlMetadata(
                ps_xmltree1, {"security": {"clas": "U"}}
            ),
        ]
    )

    with out_sidd.open("wb") as file:
        with sksidd.NitfWriter(file, write_metadata) as writer:
            writer.write_image(0, basis_array0)
            writer.write_image(1, basis_array1)

    num_expected_imseg = 2 * int(
        np.ceil(np.prod(basis_array0.shape) / sarkit.sidd._io.LI_MAX)
    )
    if force_segmentation:
        assert num_expected_imseg > 2  # make sure the monkeypatch caused segmentation
    with out_sidd.open("rb") as file:
        nitf_details = sarkit._nitf.nitf.NITFDetails(file)
        assert num_expected_imseg == len(nitf_details.img_headers)

    with out_sidd.open("rb") as file:
        with sksidd.NitfReader(file) as reader:
            read_metadata = reader.metadata
            assert len(read_metadata.images) == 2
            assert len(read_metadata.sicd_xmls) == 2
            assert len(read_metadata.product_support_xmls) == 2
            read_array0 = reader.read_image(0)
            read_array1 = reader.read_image(1)
            read_xmltree = read_metadata.images[0].xmltree
            read_sicd_xmltree = read_metadata.sicd_xmls[-1].xmltree
            read_ps_xmltree0 = read_metadata.product_support_xmls[0].xmltree
            read_ps_xmltree1 = read_metadata.product_support_xmls[1].xmltree

    def _normalized(xmltree):
        return lxml.etree.tostring(xmltree, method="c14n")

    assert _normalized(read_xmltree) == _normalized(basis_etree)
    assert _normalized(read_ps_xmltree0) == _normalized(ps_xmltree0)
    assert _normalized(read_ps_xmltree1) == _normalized(ps_xmltree1)
    assert _normalized(read_sicd_xmltree) == _normalized(sicd_xmltree)

    assert write_metadata.file_header_part == read_metadata.file_header_part
    assert (
        write_metadata.images[0].im_subheader_part
        == read_metadata.images[0].im_subheader_part
    )
    assert (
        write_metadata.images[0].de_subheader_part
        == read_metadata.images[0].de_subheader_part
    )
    assert np.array_equal(basis_array0, read_array0)
    assert np.array_equal(basis_array1, read_array1)


def test_segmentation():
    """From Figure 2.5-6 SIDD 1.0 Multiple Input Image - Multiple Product Images Requiring Segmentation"""
    sidd_xmltree = lxml.etree.parse(DATAPATH / "example-sidd-3.0.0.xml")
    xml_helper = sksidd.XmlHelper(sidd_xmltree)
    assert xml_helper.load("./{*}Display/{*}PixelType") == "MONO8I"

    # Tweak SIDD size to force three image segments
    li_max = 9_999_999_998
    iloc_max = 99_999
    num_cols = li_max // (2 * iloc_max)  # set num_cols so that row limit is iloc_max
    last_rows = 24
    num_rows = iloc_max * 2 + last_rows
    xml_helper.set("./{*}Measurement/{*}PixelFootprint/{*}Row", num_rows)
    xml_helper.set("./{*}Measurement/{*}PixelFootprint/{*}Col", num_cols)
    fhdr_numi, fhdr_li, imhdrs = sksidd.segmentation_algorithm(
        [sidd_xmltree, sidd_xmltree]
    )

    assert fhdr_numi == 6
    # SIDD segmentation algorithm (2.4.2.1 in 1.0/2.0/3.0) would lead to overlaps of the last partial
    # image segment due to ILOC. This implements a scheme similar to SICD wherein "RRRRR" of ILOC matches
    # the NROWs in the previous segment.
    expected_imhdrs = [
        sksidd.SegmentationImhdr(
            iid1="SIDD001001",
            idlvl=1,
            ialvl=0,
            iloc="0" * 10,
            nrows=iloc_max,
            ncols=num_cols,
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD001002",
            idlvl=2,
            ialvl=1,
            iloc=f"{iloc_max:05d}{0:05d}",
            nrows=iloc_max,
            ncols=num_cols,
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD001003",
            idlvl=3,
            ialvl=2,
            iloc=f"{iloc_max:05d}{0:05d}",
            nrows=last_rows,
            ncols=num_cols,
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD002001",
            idlvl=4,
            ialvl=0,
            iloc="0" * 10,
            nrows=iloc_max,
            ncols=num_cols,
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD002002",
            idlvl=5,
            ialvl=4,
            iloc=f"{iloc_max:05d}{0:05d}",
            nrows=iloc_max,
            ncols=num_cols,
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD002003",
            idlvl=6,
            ialvl=5,
            iloc=f"{iloc_max:05d}{0:05d}",
            nrows=last_rows,
            ncols=num_cols,
        ),
    ]
    expected_fhdr_li = [imhdr.nrows * imhdr.ncols for imhdr in expected_imhdrs]

    assert expected_fhdr_li == fhdr_li
    assert expected_imhdrs == imhdrs


def test_version_info():
    actual_order = [x["version"] for x in sksidd.VERSION_INFO.values()]
    expected_order = sorted(actual_order, key=lambda x: x.split("."))
    assert actual_order == expected_order

    for urn, info in sksidd.VERSION_INFO.items():
        assert lxml.etree.parse(info["schema"]).getroot().get("targetNamespace") == urn
