import itertools
import pathlib

import lxml
import numpy as np
import pytest

import sarkit._nitf_io
import sarkit.sidd as sksidd
import sarkit.sidd._io as siddio

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
    basis_etree0 = lxml.etree.parse(sidd_xml)
    basis_array0 = _random_image(basis_etree0)

    basis_etree1 = lxml.etree.parse(sidd_xml)
    basis_etree1.find("./{*}Display/{*}PixelType").text = "MONO16I"
    basis_array1 = 2**16 - 1 - basis_array0.astype(np.uint16)

    basis_etree2 = lxml.etree.parse(sidd_xml)
    basis_etree2.find("./{*}Display/{*}PixelType").text = "RGB24I"
    basis_array2 = np.empty(basis_array0.shape, siddio.PIXEL_TYPES["RGB24I"]["dtype"])
    basis_array2["R"] = basis_array0
    basis_array2["G"] = basis_array0 + 1
    basis_array2["B"] = basis_array0 - 1

    # TODO MONO8LU and RGB8LU

    if force_segmentation:
        monkeypatch.setattr(
            siddio, "LI_MAX", basis_array0.nbytes // 5
        )  # reduce the segment size limit to force segmentation

    nitf_plan = sksidd.SiddNitfPlan(
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
        }
    )
    nitf_plan.add_image(
        basis_etree0,
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

    nitf_plan.add_image(
        basis_etree1,
        is_fields={
            "tgtid": "tgtid",
            "iid2": "iid2",
            "security": {
                "clas": "U",
            },
        },
        des_fields={
            "security": {
                "clas": "U",
            },
        },
    )

    nitf_plan.add_image(
        basis_etree2,
        is_fields={
            "tgtid": "tgtid",
            "iid2": "iid2",
            "security": {
                "clas": "U",
            },
        },
        des_fields={
            "security": {
                "clas": "U",
            },
        },
    )

    nitf_plan.add_sicd_xml(
        sicd_xmltree=sicd_xmltree, des_fields={"security": {"clas": "U"}}
    )

    nitf_plan.add_sicd_xml(
        sicd_xmltree=sicd_xmltree, des_fields={"security": {"clas": "U"}}
    )

    ps_xmltree0 = lxml.etree.ElementTree(
        lxml.etree.fromstring("<product><support/></product>")
    )
    nitf_plan.add_product_support_xml(
        ps_xmltree=ps_xmltree0, des_fields={"security": {"clas": "U"}}
    )
    ps_xmltree1 = lxml.etree.ElementTree(
        lxml.etree.fromstring(
            '<product xmlns="https://example.com"><support/></product>'
        )
    )
    nitf_plan.add_product_support_xml(
        ps_xmltree=ps_xmltree1, des_fields={"security": {"clas": "U"}}
    )

    with out_sidd.open("wb") as file:
        with sksidd.SiddNitfWriter(file, nitf_plan) as writer:
            writer.write_image(0, basis_array0)
            writer.write_image(1, basis_array1)
            writer.write_image(2, basis_array2)

    def _num_imseg(array):
        rows_per_seg = int(np.floor(siddio.LI_MAX / array[0].nbytes))
        return int(np.ceil(array.shape[0] / rows_per_seg))

    num_expected_imseg = (
        _num_imseg(basis_array0) + _num_imseg(basis_array1) + _num_imseg(basis_array2)
    )
    if force_segmentation:
        assert num_expected_imseg > 2  # make sure the monkeypatch caused segmentation
    with out_sidd.open("rb") as file:
        ntf = sarkit._nitf_io.Nitf()
        ntf.load(file)
        assert num_expected_imseg == len(ntf["ImageSegments"])

    with out_sidd.open("rb") as file:
        with sksidd.SiddNitfReader(file) as reader:
            assert len(reader.images) == 3
            assert len(reader.sicd_xmls) == 2
            assert len(reader.product_support_xmls) == 2
            read_array0 = reader.read_image(0)
            read_array1 = reader.read_image(1)
            read_array2 = reader.read_image(2)
            read_xmltree = reader.images[0].sidd_xmltree
            read_sicd_xmltree = reader.sicd_xmls[-1].sicd_xmltree
            read_ps_xmltree0 = reader.product_support_xmls[0].product_support_xmltree
            read_ps_xmltree1 = reader.product_support_xmls[1].product_support_xmltree

    def _normalized(xmltree):
        return lxml.etree.tostring(xmltree, method="c14n")

    assert _normalized(read_xmltree) == _normalized(basis_etree0)
    assert _normalized(read_ps_xmltree0) == _normalized(ps_xmltree0)
    assert _normalized(read_ps_xmltree1) == _normalized(ps_xmltree1)
    assert _normalized(read_sicd_xmltree) == _normalized(sicd_xmltree)

    assert nitf_plan.header_fields == reader.header_fields
    assert nitf_plan.images[0].is_fields == reader.images[0].is_fields
    assert nitf_plan.images[0].des_fields == reader.images[0].des_fields
    assert np.array_equal(basis_array0, read_array0)
    assert np.array_equal(basis_array1, read_array1)
    assert np.array_equal(basis_array2, read_array2)


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

    def _parse_dms(dms_str):
        lat_deg = int(dms_str[0:2])
        lat_min = int(dms_str[2:4])
        lat_sec = int(dms_str[4:6])
        sign = {"S": -1, "N": 1}[dms_str[6]]
        lat = sign * (lat_deg + lat_min / 60.0 + lat_sec / 3600.0)

        lon_deg = int(dms_str[7:10])
        lon_min = int(dms_str[10:12])
        lon_sec = int(dms_str[12:14])
        sign = {"W": -1, "E": 1}[dms_str[14]]
        lon = sign * (lon_deg + lon_min / 60.0 + lon_sec / 3600.0)
        return lat, lon

    outer_corners_ll = [
        _parse_dms(imhdrs[0].igeolo[:15]),
        _parse_dms(imhdrs[0].igeolo[15:30]),
        _parse_dms(imhdrs[-1].igeolo[30:45]),
        _parse_dms(imhdrs[-1].igeolo[45:60]),
    ]
    icp_latlon = xml_helper.load("./{*}GeoData/{*}ImageCorners")
    np.testing.assert_allclose(outer_corners_ll, icp_latlon, atol=0.5 / 3600)

    groups = itertools.groupby(imhdrs, key=lambda x: x.iid1[:7])
    for _, group_headers in groups:
        headers = list(group_headers)
        for idx in range(len(headers) - 1):
            assert headers[idx].igeolo[45:] == headers[idx + 1].igeolo[:15]
            assert headers[idx].igeolo[30:45] == headers[idx + 1].igeolo[15:30]

    for imhdr in imhdrs:
        imhdr.igeolo = ""

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
            igeolo="",
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD001002",
            idlvl=2,
            ialvl=1,
            iloc=f"{iloc_max:05d}{0:05d}",
            nrows=iloc_max,
            ncols=num_cols,
            igeolo="",
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD001003",
            idlvl=3,
            ialvl=2,
            iloc=f"{iloc_max:05d}{0:05d}",
            nrows=last_rows,
            ncols=num_cols,
            igeolo="",
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD002001",
            idlvl=4,
            ialvl=0,
            iloc="0" * 10,
            nrows=iloc_max,
            ncols=num_cols,
            igeolo="",
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD002002",
            idlvl=5,
            ialvl=4,
            iloc=f"{iloc_max:05d}{0:05d}",
            nrows=iloc_max,
            ncols=num_cols,
            igeolo="",
        ),
        sksidd.SegmentationImhdr(
            iid1="SIDD002003",
            idlvl=6,
            ialvl=5,
            iloc=f"{iloc_max:05d}{0:05d}",
            nrows=last_rows,
            ncols=num_cols,
            igeolo="",
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
