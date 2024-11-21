import pathlib

import lxml.etree
import numpy as np
import pytest

import sarkit.standards.cphd.io as cphd_io
import sarkit.standards.cphd.xml as cphd_xml

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


def test_version_info():
    actual_order = [x["version"] for x in cphd_io.VERSION_INFO.values()]
    expected_order = sorted(actual_order, key=lambda x: x.split("."))
    assert actual_order == expected_order

    for urn, info in cphd_io.VERSION_INFO.items():
        assert lxml.etree.parse(info["schema"]).getroot().get("targetNamespace") == urn


def test_dtype_to_binary_format():
    # Basic types
    assert cphd_io.dtype_to_binary_format_string(np.int8) == "I1"
    assert cphd_io.dtype_to_binary_format_string(np.int16) == "I2"
    assert cphd_io.dtype_to_binary_format_string(np.int32) == "I4"
    assert cphd_io.dtype_to_binary_format_string(np.int64) == "I8"
    assert cphd_io.dtype_to_binary_format_string(np.uint8) == "U1"
    assert cphd_io.dtype_to_binary_format_string(np.uint16) == "U2"
    assert cphd_io.dtype_to_binary_format_string(np.uint32) == "U4"
    assert cphd_io.dtype_to_binary_format_string(np.uint64) == "U8"
    assert cphd_io.dtype_to_binary_format_string(np.float32) == "F4"
    assert cphd_io.dtype_to_binary_format_string(np.float64) == "F8"
    assert cphd_io.dtype_to_binary_format_string(np.complex64) == "CF8"
    assert cphd_io.dtype_to_binary_format_string(np.complex128) == "CF16"
    dt = np.dtype([("real", np.int8), ("imag", np.int8)])
    assert cphd_io.dtype_to_binary_format_string(dt) == "real=I1;imag=I1;"
    dt = np.dtype([("real", np.int16), ("imag", np.int16)])
    assert cphd_io.dtype_to_binary_format_string(dt) == "real=I2;imag=I2;"
    dt = np.dtype([("real", np.int32), ("imag", np.int32)])
    assert cphd_io.dtype_to_binary_format_string(dt) == "real=I4;imag=I4;"
    dt = np.dtype([("I", np.int64), ("Q", np.int64)])
    assert cphd_io.dtype_to_binary_format_string(dt) == "I=I8;Q=I8;"
    dt = np.dtype("S30")
    assert cphd_io.dtype_to_binary_format_string(dt) == "S30"

    # Special handling
    dt = np.dtype(("f8", 2))
    assert cphd_io.dtype_to_binary_format_string(dt) == "DCX=F8;DCY=F8;"

    dt = np.dtype(("f8", 3))
    assert cphd_io.dtype_to_binary_format_string(dt) == "X=F8;Y=F8;Z=F8;"

    dt = np.dtype([("a", "i8"), ("b", "f8"), ("c", "f8")])
    assert cphd_io.dtype_to_binary_format_string(dt) == "a=I8;b=F8;c=F8;"

    with pytest.raises(ValueError):
        cphd_io.dtype_to_binary_format_string(np.dtype(("f8", 4)))

    with pytest.raises(ValueError):
        dt = np.dtype([("a", "i8"), ("b", ("f8", 3)), ("c", "f8")])
        cphd_io.dtype_to_binary_format_string(dt)


def test_binary_format_to_dtype():
    # Basic types
    assert cphd_io.binary_format_string_to_dtype("I1") == np.int8
    assert cphd_io.binary_format_string_to_dtype("I2") == np.int16
    assert cphd_io.binary_format_string_to_dtype("I4") == np.int32
    assert cphd_io.binary_format_string_to_dtype("I8") == np.int64
    assert cphd_io.binary_format_string_to_dtype("U1") == np.uint8
    assert cphd_io.binary_format_string_to_dtype("U2") == np.uint16
    assert cphd_io.binary_format_string_to_dtype("U4") == np.uint32
    assert cphd_io.binary_format_string_to_dtype("U8") == np.uint64
    assert cphd_io.binary_format_string_to_dtype("F4") == np.float32
    assert cphd_io.binary_format_string_to_dtype("F8") == np.float64
    assert cphd_io.binary_format_string_to_dtype("CF8") == np.complex64
    assert cphd_io.binary_format_string_to_dtype("CF16") == np.complex128
    dt = np.dtype([("real", np.int8), ("imag", np.int8)])
    assert cphd_io.binary_format_string_to_dtype("real=I1;imag=I1;") == dt
    dt = np.dtype([("real", np.int16), ("imag", np.int16)])
    assert cphd_io.binary_format_string_to_dtype("real=I2;imag=I2;") == dt
    dt = np.dtype([("real", np.int32), ("imag", np.int32)])
    assert cphd_io.binary_format_string_to_dtype("real=I4;imag=I4;") == dt
    dt = np.dtype([("I", np.int64), ("Q", np.int64)])
    assert cphd_io.binary_format_string_to_dtype("I=I8;Q=I8;") == dt
    dt = np.dtype("S30")
    assert cphd_io.binary_format_string_to_dtype("S30") == dt

    # Special handling
    dt = np.dtype([("a", "i8"), ("b", "f8"), ("c", "f8")])
    assert cphd_io.binary_format_string_to_dtype("a=I8;b=F8;c=F8;") == dt

    dt = np.dtype(("f8", 3))
    assert cphd_io.binary_format_string_to_dtype("X=F8;Y=F8;Z=F8;") == dt

    dt = np.dtype(("f8", 2))
    assert cphd_io.binary_format_string_to_dtype("DCX=F8;DCY=F8;") == dt


def test_roundtrip(tmp_path):
    basis_etree = lxml.etree.parse(DATAPATH / "example-cphd-1.0.1.xml")
    basis_version = lxml.etree.QName(basis_etree.getroot()).namespace
    schema = lxml.etree.XMLSchema(file=cphd_io.VERSION_INFO[basis_version]["schema"])
    schema.assertValid(basis_etree)
    xmlhelp = cphd_xml.XmlHelper(basis_etree)
    channel_ids = [
        x.text for x in basis_etree.findall("./{*}Channel/{*}Parameters/{*}Identifier")
    ]
    assert len(channel_ids) == 1
    rng = np.random.default_rng()

    def _random_array(shape, dtype, reshape=True):
        retval = np.frombuffer(
            rng.bytes(np.prod(shape) * dtype.itemsize), dtype=dtype
        ).copy()
        if dtype.names is None:
            retval[~np.isfinite(retval)] = 0
        else:
            for name in dtype.names:
                retval[name][~np.isfinite(retval[name])] = 0
        return retval.reshape(shape) if reshape else retval

    signal_dtype = cphd_io.binary_format_string_to_dtype(
        basis_etree.findtext("./{*}Data/{*}SignalArrayFormat")
    )
    num_vectors = xmlhelp.load("./{*}Data/{*}Channel/{*}NumVectors")
    num_samples = xmlhelp.load(".//{*}Data/{*}Channel/{*}NumSamples")
    basis_signal = _random_array((num_vectors, num_samples), signal_dtype)

    pvps = np.zeros(num_vectors, dtype=cphd_io.get_pvp_dtype(basis_etree))
    for f, (dt, _) in pvps.dtype.fields.items():
        pvps[f] = _random_array(num_vectors, dtype=dt, reshape=False)

    support_arrays = {}
    for data_sa_elem in basis_etree.findall("./{*}Data/{*}SupportArray"):
        sa_id = xmlhelp.load_elem(data_sa_elem.find("./{*}Identifier"))
        nrows = xmlhelp.load_elem(data_sa_elem.find("./{*}NumRows"))
        ncols = xmlhelp.load_elem(data_sa_elem.find("./{*}NumCols"))
        format_str = basis_etree.findtext(
            f"./{{*}}SupportArray//{{*}}Identifier[.='{sa_id}']/../{{*}}ElementFormat"
        )
        dt = cphd_io.binary_format_string_to_dtype(format_str)
        support_arrays[sa_id] = _random_array((nrows, ncols), dt)

    cphd_plan = cphd_io.CphdPlan(
        file_header=cphd_io.CphdFileHeaderFields(
            classification="UNCLASSIFIED",
            release_info="UNRESTRICTED",
            additional_kvps={"k1": "v1", "k2": "v2"},
        ),
        cphd_xmltree=basis_etree,
    )
    out_cphd = tmp_path / "out.cphd"
    with open(out_cphd, "wb") as f:
        with cphd_io.CphdWriter(f, cphd_plan) as writer:
            writer.write_signal(channel_ids[0], basis_signal)
            writer.write_pvp(channel_ids[0], pvps)
            for k, v in support_arrays.items():
                writer.write_support_array(k, v)

    with open(out_cphd, "rb") as f, cphd_io.CphdReader(f) as reader:
        read_sig, read_pvp = reader.read_channel(channel_ids[0])
        read_support_arrays = {}
        for sa_id in reader.cphd_xmltree.findall("./{*}SupportArray/*/{*}Identifier"):
            read_support_arrays[sa_id.text] = reader.read_support_array(sa_id.text)

    assert cphd_plan.file_header == reader.file_header
    assert np.array_equal(basis_signal, read_sig)
    assert np.array_equal(pvps, read_pvp)
    assert support_arrays.keys() == read_support_arrays.keys()
    assert all(
        np.array_equal(support_arrays[f], read_support_arrays[f])
        for f in support_arrays
    )
    assert lxml.etree.tostring(
        reader.cphd_xmltree, method="c14n"
    ) == lxml.etree.tostring(basis_etree, method="c14n")
