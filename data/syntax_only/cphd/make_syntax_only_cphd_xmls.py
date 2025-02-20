import argparse
import contextlib
import filecmp
import functools
import pathlib
import tempfile

import lxml.builder
import lxml.etree

import sarkit.cphd as skcphd

STUB_DIR = pathlib.Path(__file__).parent / "stubs"


def update_1_0_1_to_1_1_0(etree):
    version_ns = "http://api.nsgreg.nga.mil/schema/cphd/1.1.0"
    em = lxml.builder.ElementMaker(namespace=version_ns, nsmap={None: version_ns})
    for chanparam in etree.findall("{*}Channel/{*}Parameters"):
        chanparam.find("./{*}Polarization/{*}TxPol").text = "S"
        chanparam.find("./{*}Polarization/{*}RcvPol").text = "E"
        chanparam.find("./{*}Polarization").extend(
            (
                em.TxPolRef(em.AmpH("0.0"), em.AmpV("1.0"), em.PhaseV("0.24")),
                em.RcvPolRef(em.AmpH("0.0"), em.AmpV("1.0"), em.PhaseV("0.24")),
            )
        )
        chanparam.find("./{*}DwellTimes").extend(
            (
                em.DTAId("DTAIdentifier!"),
                em.UseDTA("false"),
            )
        )
    etree.find("./{*}PVP/{*}SIGNAL").addnext(_get_stub("PVP.TxAntenna.xml", version_ns))
    etree.find("./{*}PVP/{*}TxAntenna").addnext(
        _get_stub("PVP.RcvAntenna.xml", version_ns)
    )
    etree.find("./{*}SupportArray/{*}AddedSupportArray").addprevious(
        _get_stub("DwellTimeArray.xml", version_ns)
    )
    etree.find("./{*}Antenna/{*}AntCoordFrame").append(em.UseACFPVP("false"))
    apat = etree.find("./{*}Antenna/{*}AntPattern")
    apat.find("./{*}EBFreqShift").addnext(
        em.EBFreqShiftSF(em.DCXSF("0.1"), em.DCYSF("0.2"))
    )
    apat.find("./{*}MLFreqDilation").addnext(
        em.MLFreqDilationSF(em.DCXSF("0.1"), em.DCYSF("0.2"))
    )
    apat.find("./{*}GainBSPoly").addnext(
        em.AntPolRef(em.AmpX("0.0"), em.AmpY("1.0"), em.PhaseY("-0.24"))
    )
    apat.find("./{*}EB").append(em.UseEBPVP("false"))
    apat.find("./{*}Array").append(em.AntGPId("array_id"))
    apat.find("./{*}Element").append(em.AntGPId("elem_id"))

    for cfsf in etree.findall(
        "./{*}ErrorParameters/{*}Bistatic//{*}RadarSensor/{*}ClockFreqSF"
    ):
        cfsf.addprevious(em.DelayBias("0.123"))

    for elem in etree.iter():
        elem.tag = f"{{{version_ns}}}{lxml.etree.QName(elem).localname}"


def update_version(etree, urn):
    converter = {
        "http://api.nsgreg.nga.mil/schema/cphd/1.0.1": lambda x: x,
        "http://api.nsgreg.nga.mil/schema/cphd/1.1.0": update_1_0_1_to_1_1_0,
    }[urn]
    return converter(etree)


def _remove(etree, pattern):
    if (elem := etree.find(pattern)) is not None:
        elem.getparent().remove(elem)


def _get_stub(stub_name, version_ns):
    new_elem = lxml.etree.parse(STUB_DIR / stub_name).getroot()
    for elem in new_elem.iter():
        elem.tag = f"{{{version_ns}}}{lxml.etree.QName(elem).localname}"
    return new_elem


def monostatic_or_bistatic(etree, mono_or_bi):
    version_ns = lxml.etree.QName(etree.getroot()).namespace
    em = lxml.builder.ElementMaker(namespace=version_ns, nsmap={None: version_ns})

    etree.find("{*}CollectionID/{*}CollectType").text = mono_or_bi.upper()

    _remove(etree, "{*}CollectionID/{*}IlluminatorName")
    if mono_or_bi.upper() == "BISTATIC":
        etree.find("{*}CollectionID/{*}CollectorName").addnext(
            em.IlluminatorName("DifferentThanCollector")
        )

    _remove(etree, "{*}ReferenceGeometry/{*}Monostatic")
    _remove(etree, "{*}ReferenceGeometry/{*}Bistatic")
    etree.find("{*}ReferenceGeometry").append(
        _get_stub(f"ReferenceGeometry.{mono_or_bi.capitalize()}.xml", version_ns)
    )

    err_elem = etree.find("{*}ErrorParameters")
    err_elem[:] = []
    err_elem.append(
        _get_stub(f"ErrorParameters.{mono_or_bi.capitalize()}.xml", version_ns)
    )


def set_ref_surface(etree, planar_or_hae):
    version_ns = lxml.etree.QName(etree.getroot()).namespace
    em = lxml.builder.ElementMaker(namespace=version_ns, nsmap={None: version_ns})

    if planar_or_hae.upper() == "PLANAR":
        new_elem = em.Planar(
            em.uIAX(em.X("0.0"), em.Y("0.0"), em.Z("1.0")),
            em.uIAY(em.X("0.0"), em.Y("1.0"), em.Z("0.0")),
        )
    else:
        new_elem = em.HAE(
            em.uIAXLL(em.Lat("0.1"), em.Lon("0.2")),
            em.uIAYLL(em.Lat("0.3"), em.Lon("0.4")),
        )

    etree.find("./{*}SceneCoordinates/{*}ReferenceSurface")[:] = [new_elem]


def set_version_collecttype_refsurf(etree, urn, mono_or_bi, planar_or_hae):
    monostatic_or_bistatic(etree, mono_or_bi)
    set_ref_surface(etree, planar_or_hae)
    update_version(etree, urn)


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Don't write the files, just return the status. Return code 0 means nothing would change.",
    )
    config = parser.parse_args(args)

    with (
        tempfile.TemporaryDirectory()
        if config.check
        else contextlib.nullcontext(config.output_dir)
    ) as outdir:
        outdir = pathlib.Path(outdir)

        for index, mods in enumerate(
            (
                functools.partial(
                    set_version_collecttype_refsurf,
                    urn="http://api.nsgreg.nga.mil/schema/cphd/1.1.0",
                    mono_or_bi="BISTATIC",
                    planar_or_hae="HAE",
                ),
            )
        ):
            etree = lxml.etree.parse(
                pathlib.Path(__file__).parent
                / "manual-syntax-only-cphd-mono-1.0.1.xml",
            )
            mods(etree)
            version_ns = lxml.etree.QName(etree.getroot()).namespace
            lxml.etree.cleanup_namespaces(etree, top_nsmap={None: version_ns})
            version_info = skcphd.VERSION_INFO[version_ns]
            schema = lxml.etree.XMLSchema(file=version_info["schema"])
            schema.assertValid(etree)
            lxml.etree.indent(etree, space=" " * 4)
            etree.write(
                outdir / f"{index:04d}-syntax-only-cphd-{version_info['version']}.xml",
                pretty_print=True,
            )

        if config.check:
            diff = filecmp.dircmp(pathlib.Path(__file__).parent, outdir)
            checks_out = not bool(
                diff.diff_files
                or {
                    pathlib.Path(__file__).name,
                    "manual-syntax-only-cphd-mono-1.0.1.xml",
                    "stubs",
                }.symmetric_difference(diff.left_only)
            )
            return not checks_out


if __name__ == "__main__":
    exit(main())
