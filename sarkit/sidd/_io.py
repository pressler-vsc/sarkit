"""
Functions to read and write SIDD files.
"""

import collections
import dataclasses
import datetime
import importlib
import itertools
import logging
import os
import warnings
from typing import Final, Self, TypedDict

import lxml.etree
import numpy as np
import numpy.typing as npt

import sarkit._nitf_io
import sarkit.sicd as sksicd
import sarkit.sicd._io
import sarkit.sidd as sksidd
import sarkit.wgs84

logger = logging.getLogger(__name__)

SPECIFICATION_IDENTIFIER: Final[str] = (
    "SIDD Volume 1 Design & Implementation Description Document"
)

SCHEMA_DIR = importlib.resources.files("sarkit.sidd.schemas")


class VersionInfoType(TypedDict):
    version: str
    date: str
    schema: importlib.resources.abc.Traversable


# Keys must be in ascending order
VERSION_INFO: Final[dict[str, VersionInfoType]] = {
    "urn:SIDD:2.0.0": {
        "version": "2.0",
        "date": "2019-05-31T00:00:00Z",
        "schema": SCHEMA_DIR / "version2" / "SIDD_schema_V2.0.0_2019_05_31.xsd",
    },
    "urn:SIDD:3.0.0": {
        "version": "3.0",
        "date": "2021-11-30T00:00:00Z",
        "schema": SCHEMA_DIR / "version3" / "SIDD_schema_V3.0.0.xsd",
    },
}


# Table 2-6 NITF 2.1 Image Sub-Header Population for Supported Pixel Type
class _PixelTypeDict(TypedDict):
    IREP: str
    IREPBANDn: list[str]
    IMODE: str
    NBPP: int
    dtype: np.dtype


PIXEL_TYPES: Final[dict[str, _PixelTypeDict]] = {
    "MONO8I": {
        "IREP": "MONO",
        "IREPBANDn": ["M"],
        "IMODE": "B",
        "NBPP": 8,
        "dtype": np.dtype(np.uint8),
    },
    "MONO8LU": {
        "IREP": "MONO",
        "IREPBANDn": ["LU"],
        "IMODE": "B",
        "NBPP": 8,
        "dtype": np.dtype(np.uint8),
    },
    "MONO16I": {
        "IREP": "MONO",
        "IREPBANDn": ["M"],
        "IMODE": "B",
        "NBPP": 16,
        "dtype": np.dtype(np.uint16),
    },
    "RGB8LU": {
        "IREP": "RGB/LUT",
        "IREPBANDn": ["LU"],
        "IMODE": "B",
        "NBPP": 8,
        "dtype": np.dtype(np.uint8),
    },
    "RGB24I": {
        "IREP": "RGB",
        "IREPBANDn": ["R", "G", "B"],
        "IMODE": "P",
        "NBPP": 8,
        "dtype": np.dtype([("R", np.uint8), ("G", np.uint8), ("B", np.uint8)]),
    },
}

LI_MAX: Final[int] = 9_999_999_998
ILOC_MAX: Final[int] = 99_999


# SICD implementation happens to match, reuse it
class SiddNitfSecurityFields(sksicd.SicdNitfSecurityFields):
    __doc__ = sksicd.SicdNitfSecurityFields.__doc__


# SICD implementation happens to match, reuse it
class SiddNitfHeaderFields(sksicd.SicdNitfHeaderFields):
    __doc__ = sksicd.SicdNitfHeaderFields.__doc__


@dataclasses.dataclass(kw_only=True)
class SiddNitfImageSegmentFields:
    """NITF image header fields which are set according to a Program Specific Implementation Document

    Attributes
    ----------
    tgtid : str
        Target Identifier
    iid2 : str
        Image Identifier 2
    security : :py:class:`SiddNitfSecurityFields`
        Security Tags with "IS" prefix
    icom : list of str
        Image Comments
    """

    ## IS fields are applied to all segments
    tgtid: str = ""
    iid2: str = ""
    security: SiddNitfSecurityFields
    icom: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def _from_header(cls, image_header: sarkit._nitf_io.ImageSubHeader) -> Self:
        """Construct from a NITF ImageSubHeader object"""
        return cls(
            tgtid=image_header["TGTID"].value,
            iid2=image_header["IID2"].value,
            security=SiddNitfSecurityFields._from_nitf_fields("IS", image_header),
            icom=[val.value for val in image_header.find_all("ICOM\\d+")],
        )

    def __post_init__(self):
        if isinstance(self.security, dict):
            self.security = SiddNitfSecurityFields(**self.security)


# SICD implementation happens to match, reuse it
class SiddNitfDESegmentFields(sksicd.SicdNitfDESegmentFields):
    __doc__ = sksicd.SicdNitfDESegmentFields.__doc__


@dataclasses.dataclass
class SiddNitfPlanProductImageInfo:
    """Metadata necessary for describing the plan to add a product image to a SIDD

    Attributes
    ----------
    sidd_xmltree : lxml.etree.ElementTree
        SIDD product metadata XML ElementTree
    is_fields : :py:class:`SiddNitfImageSegmentFields`
        NITF Image Segment Header fields which can be set
    des_fields : :py:class:`SiddNitfDESegmentFields`
        NITF DE Segment Header fields which can be set

    See Also
    --------
    SiddNitfPlan
    SiddNitfPlanLegendInfo
    SiddNitfPlanDedInfo
    SiddNitfPlanProductSupportXmlInfo
    SiddNitfPlanSicdXmlInfo
    """

    sidd_xmltree: lxml.etree.ElementTree
    is_fields: SiddNitfImageSegmentFields
    des_fields: SiddNitfDESegmentFields

    def __post_init__(self):
        if isinstance(self.is_fields, dict):
            self.is_fields = SiddNitfImageSegmentFields(**self.is_fields)
            self.des_fields = SiddNitfDESegmentFields(**self.des_fields)


@dataclasses.dataclass
class SiddNitfPlanLegendInfo:
    """Metadata necessary for describing the plan to add a legend to a SIDD

    See Also
    --------
    SiddNitfPlan
    SiddNitfPlanProductImageInfo
    SiddNitfPlanDedInfo
    SiddNitfPlanProductSupportXmlInfo
    SiddNitfPlanSicdXmlInfo
    """

    def __post_init__(self):
        raise NotImplementedError()


@dataclasses.dataclass
class SiddNitfPlanDedInfo:
    """Metadata necessary for describing the plan to add Digital Elevation Data (DED) to a SIDD

    See Also
    --------
    SiddNitfPlan
    SiddNitfPlanProductImageInfo
    SiddNitfPlanLegendInfo
    SiddNitfPlanProductSupportXmlInfo
    SiddNitfPlanSicdXmlInfo
    """

    def __post_init__(self):
        raise NotImplementedError()


@dataclasses.dataclass
class SiddNitfPlanProductSupportXmlInfo:
    """Metadata necessary for describing the plan to add a Product Support XML to a SIDD

    See Also
    --------
    SiddNitfPlan
    SiddNitfPlanProductImageInfo
    SiddNitfPlanLegendInfo
    SiddNitfPlanDedInfo
    SiddNitfPlanSicdXmlInfo
    """

    product_support_xmltree: lxml.etree.ElementTree
    des_fields: SiddNitfDESegmentFields

    def __post_init__(self):
        if isinstance(self.des_fields, dict):
            self.des_fields = SiddNitfDESegmentFields(**self.des_fields)


@dataclasses.dataclass
class SiddNitfPlanSicdXmlInfo:
    """Metadata necessary for describing the plan to add SICD XML to a SIDD

    See Also
    --------
    SiddNitfPlan
    SiddNitfPlanProductImageInfo
    SiddNitfPlanLegendInfo
    SiddNitfPlanDedInfo
    SiddNitfPlanProductSupportXmlInfo
    """

    sicd_xmltree: lxml.etree.ElementTree
    des_fields: sksicd.SicdNitfDESegmentFields

    def __post_init__(self):
        if isinstance(self.des_fields, dict):
            self.des_fields = sksicd.SicdNitfDESegmentFields(**self.des_fields)


class SiddNitfPlan:
    """Class describing the plan for creating a SIDD NITF Container

    Parameters
    ----------
    header_fields : :py:class:`SiddNitfHeaderFields`
        NITF Header fields

    Attributes
    ----------
    header_fields : :py:class:`SiddNitfHeaderFields`
        NITF File Header fields which can be set
    images : list of :py:class:`SiddNitfPlanProductImageInfo`
        List of image information
    legends : list of :py:class:`SiddNitfPlanLegendInfo`
        List of legend information
    ded : :py:class:`SiddNitfPlanDedInfo`
        DED information
    product_support_xmls : list of :py:class:`SiddNitfPlanProductSupportXmlInfo`
        List of SICD XML information
    sicd_xmls : list of :py:class:`SiddNitfPlanSicdXmlInfo`
        List of SICD XML information

    See Also
    --------
    SiddNitfReader
    SiddNitfWriter
    SiddNitfSecurityFields
    SiddNitfHeaderFields
    SiddNitfImageSegmentFields
    SiddNitfDESegmentFields
    SiddNitfPlanProductImageInfo
    SiddNitfPlanLegendInfo
    """

    def __init__(self, header_fields: SiddNitfHeaderFields | dict):
        self.header_fields = header_fields
        if isinstance(self.header_fields, dict):
            self.header_fields = SiddNitfHeaderFields(**self.header_fields)
        self._images: list[SiddNitfPlanProductImageInfo] = []
        self._legends: list[SiddNitfPlanLegendInfo] = []
        self._ded: SiddNitfPlanDedInfo | None = None
        self._product_support_xmls: list[SiddNitfPlanProductSupportXmlInfo] = []
        self._sicd_xmls: list[SiddNitfPlanSicdXmlInfo] = []

    @property
    def images(self) -> list[SiddNitfPlanProductImageInfo]:
        return self._images

    @property
    def legends(self) -> list[SiddNitfPlanLegendInfo]:
        return self._legends

    @property
    def ded(self) -> SiddNitfPlanDedInfo | None:
        return self._ded

    @property
    def product_support_xmls(self) -> list[SiddNitfPlanProductSupportXmlInfo]:
        return self._product_support_xmls

    @property
    def sicd_xmls(self) -> list[SiddNitfPlanSicdXmlInfo]:
        return self._sicd_xmls

    def add_image(
        self,
        sidd_xmltree: lxml.etree.ElementTree,
        is_fields: SiddNitfImageSegmentFields,
        des_fields: SiddNitfDESegmentFields,
    ) -> int:
        """Add a SAR product to the plan

        Parameters
        ----------
        sidd_xmltree : lxml.etree.ElementTree
            SIDD XML ElementTree
        is_fields : :py:class:`SiddNitfImageSegmentFields`
            NITF Image Segment Header fields which can be set
        des_fields : :py:class:`SiddNitfDESegmentFields`
            NITF DE Segment Header fields which can be set

        Returns
        -------
        int
            The image number of the newly added SAR image
        """
        _validate_xml(sidd_xmltree)

        self._images.append(
            SiddNitfPlanProductImageInfo(
                sidd_xmltree, is_fields=is_fields, des_fields=des_fields
            )
        )
        return len(self._images) - 1

    def add_product_support_xml(
        self, ps_xmltree: lxml.etree.ElementTree, des_fields: SiddNitfDESegmentFields
    ) -> int:
        """Add a Product Support XML to the plan

        Parameters
        ----------
        ps_xmltree : lxml.etree.ElementTree
            Product Support XML ElementTree
        des_fields : :py:class:`SiddNitfDESegmentFields`
            NITF DE Segment Header fields which can be set

        Returns
        -------
        int
            The index of the newly added Product Support XML
        """
        self.product_support_xmls.append(
            SiddNitfPlanProductSupportXmlInfo(ps_xmltree, des_fields)
        )
        return len(self.product_support_xmls) - 1

    def add_sicd_xml(
        self,
        sicd_xmltree: lxml.etree.ElementTree,
        des_fields: sksicd.SicdNitfDESegmentFields,
    ) -> int:
        """Add a SICD XML to the plan

        Parameters
        ----------
        sicd_xmltree : lxml.etree.ElementTree
            SICD XML ElementTree
        des_fields : :py:class:`sicdio.SicdNitfDESegmentFields`
            NITF DE Segment Header fields which can be set

        Returns
        -------
        int
            The index of the newly added SICD XML
        """
        self.sicd_xmls.append(SiddNitfPlanSicdXmlInfo(sicd_xmltree, des_fields))
        return len(self.sicd_xmls) - 1

    def add_legend(
        self, attached_to: int, location: tuple[int, int], shape: tuple[int, int]
    ) -> int:
        """Add a Legend to the plan

        Parameters
        ----------
        attached_to : int
            SAR image number to attach legend to
        location : tuple of int
            (row, column) of the SAR image to place first legend pixel
        shape : tuple of int
            Dimension of the legend (Number of Rows, Number of Columns)

        """
        raise NotImplementedError()

    def add_ded(self, shape: tuple[int, int]) -> int:
        """Add a DED to the plan

        Parameters
        ----------
        shape : tuple of int
            Dimension of the DED (Number of Rows, Number of Columns)

        """
        raise NotImplementedError()


class SiddNitfReader:
    """Read a SIDD NITF

    A SiddNitfReader object should be used as a context manager in a ``with`` statement.
    Attributes, but not methods, can be safely accessed outside of the context manager's context.

    Parameters
    ----------
    file : `file object`
        SIDD NITF file to read

    Examples
    --------
    >>> with sidd_path.open('rb') as file, SiddNitfReader(file) as reader:
    ...     sidd_xmltree = reader.images[0].sidd_xmltree
    ...     pixels = reader.read_image(0)

    Attributes
    ----------
    images : list of :py:class:`SiddNitfPlanProductImageInfo`
    header_fields : :py:class:`SiddNitfHeaderFields`
    product_support_xmls : list of :py:class:`SiddNitfPlanProductSupportXmlInfo`
    sicd_xmls : list of :py:class:`SiddNitfPlanSicdXmlInfo`
    plan : :py:class:`SiddNitfPlan`
        A SiddNitfPlan object suitable for use in a SiddNitfWriter

    See Also
    --------
    SiddNitfPlan
    SiddNitfWriter
    """

    def __init__(self, file):
        self._file_object = file

        self._ntf = sarkit._nitf_io.Nitf().load(file)

        im_segments = {}
        for imseg_index, imseg in enumerate(self._ntf["ImageSegments"]):
            img_header = imseg["SubHeader"]
            if img_header["IID1"].value.startswith("SIDD"):
                if img_header["ICAT"].value == "SAR":
                    image_number = int(img_header["IID1"].value[4:7]) - 1
                    im_segments.setdefault(image_number, [])
                    im_segments[image_number].append(imseg_index)
                else:
                    raise NotImplementedError("Non SAR images not supported")  # TODO
            elif img_header["IID1"].value.startswith("DED"):
                raise NotImplementedError("DED not supported")  # TODO

        image_segment_collections = {}
        for idx, imseg in enumerate(self._ntf["ImageSegments"]):
            imghdr = imseg["SubHeader"]
            if not imghdr["IID1"].value.startswith("SIDD"):
                continue
            image_num = int(imghdr["IID1"].value[4:7]) - 1
            image_segment_collections.setdefault(image_num, [])
            image_segment_collections[image_num].append(idx)

        self.header_fields = SiddNitfHeaderFields._from_header(self._ntf["FileHeader"])
        self.plan = SiddNitfPlan(header_fields=self.header_fields)

        image_number = 0
        for idx, deseg in enumerate(self._ntf["DESegments"]):
            des_header = deseg["SubHeader"]
            if des_header["DESID"].value == "XML_DATA_CONTENT":
                file.seek(deseg["DESDATA"].get_offset(), os.SEEK_SET)
                try:
                    xmltree = lxml.etree.fromstring(
                        file.read(deseg["DESDATA"].size)
                    ).getroottree()
                except lxml.etree.XMLSyntaxError:
                    logger.error(f"Failed to parse DES {idx} as XML")
                    continue

                if "SIDD" in xmltree.getroot().tag:
                    nitf_de_fields = SiddNitfDESegmentFields._from_header(des_header)
                    if len(self.plan.images) < len(image_segment_collections):
                        # user settable fields should be the same for all image segments
                        im_idx = im_segments[image_number][0]
                        im_fields = SiddNitfImageSegmentFields._from_header(
                            self._ntf["ImageSegments"][im_idx]["SubHeader"]
                        )
                        self.plan.add_image(
                            sidd_xmltree=xmltree,
                            is_fields=im_fields,
                            des_fields=nitf_de_fields,
                        )
                        image_number += 1
                    else:
                        # No matching product image, treat it as a product support XML
                        self.plan.add_product_support_xml(xmltree, nitf_de_fields)
                elif "SICD" in xmltree.getroot().tag:
                    nitf_de_fields = sksicd.SicdNitfDESegmentFields._from_header(
                        des_header
                    )
                    self.plan.add_sicd_xml(xmltree, nitf_de_fields)
                else:
                    nitf_de_fields = SiddNitfDESegmentFields._from_header(des_header)
                    self.plan.add_product_support_xml(xmltree, nitf_de_fields)

        # TODO Legends
        # TODO DED
        assert not self.plan.legends
        assert not self.plan.ded

    @property
    def images(self) -> list[SiddNitfPlanProductImageInfo]:
        """List of images contained in the SIDD"""
        return self.plan.images

    def read_image(self, image_number: int) -> npt.NDArray:
        """Read the entire pixel array

        Parameters
        ----------
        image_number : int
            index of SIDD Product image to read

        Returns
        -------
        ndarray
            SIDD image array
        """
        self._file_object.seek(0)
        xml_helper = sksidd.XmlHelper(self.images[image_number].sidd_xmltree)
        shape = xml_helper.load("{*}Measurement/{*}PixelFootprint")
        dtype = PIXEL_TYPES[xml_helper.load("{*}Display/{*}PixelType")][
            "dtype"
        ].newbyteorder(">")

        imsegs = sorted(
            [
                imseg
                for imseg in self._ntf["ImageSegments"]
                if imseg["SubHeader"]["IID1"].value.startswith(
                    f"SIDD{image_number + 1:03d}"
                )
            ],
            key=lambda seg: seg["SubHeader"]["IID1"].value,
        )

        image_pixels = np.empty(shape, dtype)
        imseg_sizes = np.asarray([imseg["Data"].size for imseg in imsegs])
        imseg_offsets = np.asarray([imseg["Data"].get_offset() for imseg in imsegs])
        splits = np.cumsum(imseg_sizes // (shape[-1] * dtype.itemsize))[:-1]
        for split, sz, offset in zip(
            np.array_split(image_pixels, splits, axis=0), imseg_sizes, imseg_offsets
        ):
            this_os = offset - self._file_object.tell()
            split[...] = np.fromfile(
                self._file_object, dtype, count=sz // dtype.itemsize, offset=this_os
            ).reshape(split.shape)

        return image_pixels

    @property
    def product_support_xmls(self) -> list[SiddNitfPlanProductSupportXmlInfo]:
        """List of Product Support XML instances contained in the SIDD"""
        return self.plan.product_support_xmls

    @property
    def sicd_xmls(self) -> list[SiddNitfPlanSicdXmlInfo]:
        """List of SICD XML contained in the SIDD"""
        return self.plan.sicd_xmls

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        return


class SiddNitfWriter:
    """Write a SIDD NITF

    A SiddNitfWriter object should be used as a context manager in a ``with`` statement.

    Parameters
    ----------
    file : `file object`
        SIDD NITF file to write
    nitf_plan : :py:class:`SiddNitfPlan`
        NITF plan object

    Notes
    -----
    nitf_plan should not be modified after creation of a writer

    Examples
    --------
    >>> plan = SiddNitfPlan(header_fields=SiddNitfHeaderFields(ostaid='my location',
    ...                                                        security=SiddNitfSecurityFields(clas='U')))
    >>> image_index = plan.add_image(is_fields=SiddNitfImageSegmentFields(security=SiddNitfSecurityFields(clas='U')),
    ...                              des_fields=SiddNitfDESegmentFields(security=SiddNitfSecurityFields(clas='U')))
    >>> with output_path.open('wb') as file, SiddNitfWriter(file, plan) as writer:
    ...     writer.write_image(image_index, pixel_array)

    See Also
    --------
    SiddNitfPlan
    SiddNitfReader
    """

    def __init__(self, file, nitf_plan):
        self._file_object = file
        self._nitf_plan = nitf_plan

        self._images_written = set()
        now_dt = datetime.datetime.now(datetime.timezone.utc)

        self._ntf = sarkit._nitf_io.Nitf()
        self._ntf["FileHeader"]["OSTAID"].value = self._nitf_plan.header_fields.ostaid
        self._ntf["FileHeader"]["FTITLE"].value = self._nitf_plan.header_fields.ftitle
        self._nitf_plan.header_fields.security._set_nitf_fields(
            "FS", self._ntf["FileHeader"]
        )
        self._ntf["FileHeader"]["ONAME"].value = self._nitf_plan.header_fields.oname
        self._ntf["FileHeader"]["OPHONE"].value = self._nitf_plan.header_fields.ophone

        image_segment_collections = {}  # image_num -> [image_segment, ...]
        image_segment_coordinates = {}  # image_num -> [(first_row, last_row, first_col, last_col), ...]
        current_start_row = 0
        _, _, seginfos = segmentation_algorithm(
            (img.sidd_xmltree for img in self._nitf_plan.images)
        )
        self._ntf["FileHeader"]["NUMI"].value = len(
            seginfos
        )  # TODO + num DES + num LEG

        for idx, seginfo in enumerate(seginfos):
            subhdr = self._ntf["ImageSegments"][idx]["SubHeader"]
            if seginfo.ialvl == 0:
                # first segment of each SAR image is attached to the CCS
                current_start_row = 0
            image_num = int(seginfo.iid1[4:7]) - 1
            image_segment_collections.setdefault(image_num, [])
            image_segment_coordinates.setdefault(image_num, [])
            image_segment_collections[image_num].append(idx)
            image_segment_coordinates[image_num].append(
                (current_start_row, current_start_row + seginfo.nrows, 0, seginfo.ncols)
            )
            current_start_row += seginfo.nrows

            imageinfo = self._nitf_plan.images[image_num]
            xml_helper = sksidd.XmlHelper(imageinfo.sidd_xmltree)
            pixel_info = PIXEL_TYPES[xml_helper.load("./{*}Display/{*}PixelType")]

            icp = xml_helper.load("./{*}GeoData/{*}ImageCorners")

            subhdr["IID1"].value = seginfo.iid1
            subhdr["IDATIM"].value = xml_helper.load(
                "./{*}ExploitationFeatures/{*}Collection/{*}Information/{*}CollectionDateTime"
            ).strftime("%Y%m%d%H%M%S")
            subhdr["TGTID"].value = imageinfo.is_fields.tgtid
            subhdr["IID2"].value = imageinfo.is_fields.iid2
            imageinfo.is_fields.security._set_nitf_fields("IS", subhdr)
            subhdr["ISORCE"].value = xml_helper.load(
                "./{*}ExploitationFeatures/{*}Collection/{*}Information/{*}SensorName"
            )
            subhdr["NROWS"].value = seginfo.nrows
            subhdr["NCOLS"].value = seginfo.ncols
            subhdr["PVTYPE"].value = "INT"
            subhdr["IREP"].value = pixel_info["IREP"]
            subhdr["ICAT"].value = "SAR"
            subhdr["ABPP"].value = pixel_info["NBPP"]
            subhdr["PJUST"].value = "R"
            subhdr["ICORDS"].value = "G"
            subhdr["IGEOLO"].value = seginfo.igeolo
            subhdr["IC"].value = "NC"
            subhdr["NICOM"].value = len(imageinfo.is_fields.icom)
            for icomidx, icom in enumerate(imageinfo.is_fields.icom):
                subhdr[f"ICOM{icomidx + 1}"].value = icom
            subhdr["NBANDS"].value = len(pixel_info["IREPBANDn"])
            for bandnum, irepband in enumerate(pixel_info["IREPBANDn"]):
                subhdr[f"IREPBAND{bandnum + 1:05d}"].value = irepband
            subhdr["IMODE"].value = pixel_info["IMODE"]
            subhdr["NBPR"].value = 1
            subhdr["NBPC"].value = 1

            if subhdr["NCOLS"].value > 8192:
                subhdr["NPPBH"].value = 0
            else:
                subhdr["NPPBH"].value = subhdr["NCOLS"].value

            if subhdr["NROWS"].value > 8192:
                subhdr["NPPBV"].value = 0
            else:
                subhdr["NPPBV"].value = subhdr["NROWS"].value

            subhdr["NBPP"].value = pixel_info["NBPP"]
            subhdr["IDLVL"].value = seginfo.idlvl
            subhdr["IALVL"].value = seginfo.ialvl
            subhdr["ILOC"].value = (int(seginfo.iloc[:5]), int(seginfo.iloc[5:]))
            subhdr["IMAG"].value = "1.0 "

            self._ntf["ImageSegments"][idx]["Data"].size = (
                # No compression, no masking, no blocking
                subhdr["NROWS"].value
                * subhdr["NCOLS"].value
                * subhdr["NBANDS"].value
                * subhdr["NBPP"].value
                // 8
            )

        # TODO image segments for legends
        assert not self._nitf_plan.legends
        # TODO image segments for DED
        assert not self._nitf_plan.ded

        # DE Segments
        self._ntf["FileHeader"]["NUMDES"].value = (
            len(self._nitf_plan.images)
            + len(self._nitf_plan.product_support_xmls)
            + len(self._nitf_plan.sicd_xmls)
        )

        desidx = 0
        to_write = []
        for imageinfo in self._nitf_plan.images:
            xmlns = lxml.etree.QName(imageinfo.sidd_xmltree.getroot()).namespace
            xml_helper = sksidd.XmlHelper(imageinfo.sidd_xmltree)

            deseg = self._ntf["DESegments"][desidx]
            subhdr = deseg["SubHeader"]
            subhdr["DESID"].value = "XML_DATA_CONTENT"
            subhdr["DESVER"].value = 1
            imageinfo.des_fields.security._set_nitf_fields("DES", subhdr)
            subhdr["DESSHL"].value = 773
            subhdr["DESSHF"]["DESCRC"].value = 99999
            subhdr["DESSHF"]["DESSHFT"].value = "XML"
            subhdr["DESSHF"]["DESSHDT"].value = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            subhdr["DESSHF"]["DESSHRP"].value = imageinfo.des_fields.desshrp
            subhdr["DESSHF"]["DESSHSI"].value = SPECIFICATION_IDENTIFIER
            subhdr["DESSHF"]["DESSHSV"].value = VERSION_INFO[xmlns]["version"]
            subhdr["DESSHF"]["DESSHSD"].value = VERSION_INFO[xmlns]["date"]
            subhdr["DESSHF"]["DESSHTN"].value = xmlns

            icp = xml_helper.load("./{*}GeoData/{*}ImageCorners")
            desshlpg = ""
            for icp_lat, icp_lon in itertools.chain(icp, [icp[0]]):
                desshlpg += f"{icp_lat:0=+12.8f}{icp_lon:0=+13.8f}"
            subhdr["DESSHF"]["DESSHLPG"].value = desshlpg
            subhdr["DESSHF"]["DESSHLI"].value = imageinfo.des_fields.desshli
            subhdr["DESSHF"]["DESSHLIN"].value = imageinfo.des_fields.desshlin
            subhdr["DESSHF"]["DESSHABS"].value = imageinfo.des_fields.desshabs

            xml_bytes = lxml.etree.tostring(imageinfo.sidd_xmltree)
            deseg["DESDATA"].size = len(xml_bytes)
            to_write.append((deseg["DESDATA"].get_offset(), xml_bytes))

            desidx += 1

        # Product Support XML DES
        for prodinfo in self._nitf_plan.product_support_xmls:
            deseg = self._ntf["DESegments"][desidx]
            subhdr = deseg["SubHeader"]
            sidd_uh = self._ntf["DESegments"][0]["SubHeader"]["DESSHF"]

            xmlns = (
                lxml.etree.QName(prodinfo.product_support_xmltree.getroot()).namespace
                or ""
            )

            subhdr["DESID"].value = "XML_DATA_CONTENT"
            subhdr["DESVER"].value = 1
            prodinfo.des_fields.security._set_nitf_fields("DES", subhdr)
            subhdr["DESSHL"].value = 773
            subhdr["DESSHF"]["DESCRC"].value = 99999
            subhdr["DESSHF"]["DESSHFT"].value = "XML"
            subhdr["DESSHF"]["DESSHDT"].value = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            subhdr["DESSHF"]["DESSHRP"].value = prodinfo.des_fields.desshrp
            subhdr["DESSHF"]["DESSHSI"].value = sidd_uh["DESSHSI"].value
            subhdr["DESSHF"]["DESSHSV"].value = "v" + sidd_uh["DESSHSV"].value
            subhdr["DESSHF"]["DESSHSD"].value = sidd_uh["DESSHSD"].value
            subhdr["DESSHF"]["DESSHTN"].value = xmlns
            subhdr["DESSHF"]["DESSHLPG"].value = ""
            subhdr["DESSHF"]["DESSHLI"].value = prodinfo.des_fields.desshli
            subhdr["DESSHF"]["DESSHLIN"].value = prodinfo.des_fields.desshlin
            subhdr["DESSHF"]["DESSHABS"].value = prodinfo.des_fields.desshabs

            xml_bytes = lxml.etree.tostring(prodinfo.product_support_xmltree)
            deseg["DESDATA"].size = len(xml_bytes)
            to_write.append((deseg["DESDATA"].get_offset(), xml_bytes))

            desidx += 1

        # SICD XML DES
        for sicd_xml_info in self._nitf_plan.sicd_xmls:
            deseg = self._ntf["DESegments"][desidx]
            sksicd.SicdNitfWriter._set_de_segment(
                deseg, sicd_xml_info.sicd_xmltree, sicd_xml_info.des_fields
            )

            xml_bytes = lxml.etree.tostring(sicd_xml_info.sicd_xmltree)
            deseg["DESDATA"].size = len(xml_bytes)
            to_write.append((deseg["DESDATA"].get_offset(), xml_bytes))

            desidx += 1

        self._ntf.finalize()  # compute lengths, CLEVEL, etc...
        self._ntf.dump(file)
        for offset, xml_bytes in to_write:
            file.seek(offset, os.SEEK_SET)
            file.write(xml_bytes)

    def write_image(
        self,
        image_number: int,
        array: npt.NDArray,
        start: None | tuple[int, int] = None,
    ):
        """Write product pixel data to a NITF file

        Parameters
        ----------
        image_number : int
            index of SIDD Product image to write
        array : ndarray
            2D array of pixels
        start : tuple of ints, optional
            The start index (first_row, first_col) of `array` in the SIDD image.
            If not given, `array` must be the full SIDD image.
        """

        xml_helper = sksidd.XmlHelper(self._nitf_plan.images[image_number].sidd_xmltree)
        pixel_type = xml_helper.load("./{*}Display/{*}PixelType")
        if PIXEL_TYPES[pixel_type]["dtype"] != array.dtype.newbyteorder("="):
            raise ValueError(
                f"Array dtype ({array.dtype}) does not match expected dtype ({PIXEL_TYPES[pixel_type]['dtype']}) "
                f"for PixelType={pixel_type}"
            )

        shape = xml_helper.load("{*}Measurement/{*}PixelFootprint")

        if start is None:
            # require array to be full image
            if np.any(array.shape != shape):
                raise ValueError(
                    f"Array shape {array.shape} does not match SIDD shape {shape}."
                    "If writing only a portion of the image, use the 'start' argument"
                )
            start = (0, 0)
        else:
            raise NotImplementedError("start argument not yet supported")

        startarr = np.asarray(start)

        if not np.issubdtype(startarr.dtype, np.integer):
            raise ValueError(f"Start index must be integers {startarr=}")

        if np.any(startarr < 0):
            raise ValueError(f"Start index must be non-negative {startarr=}")

        stop = startarr + array.shape
        if np.any(stop > shape):
            raise ValueError(
                f"array goes beyond end of image. start + array.shape = {stop} image shape={shape}"
            )

        imsegs = sorted(
            [
                imseg
                for imseg in self._ntf["ImageSegments"]
                if imseg["SubHeader"]["IID1"].value.startswith(
                    f"SIDD{image_number + 1:03d}"
                )
            ],
            key=lambda seg: seg["SubHeader"]["IID1"].value,
        )
        first_rows = np.cumsum(
            [0] + [imseg["SubHeader"]["NROWS"].value for imseg in imsegs[:-1]]
        )

        if pixel_type == "RGB24I":
            assert array.dtype.names is not None  # placate mypy
            raw_dtype = array.dtype[array.dtype.names[0]]
            input_array = array.view((raw_dtype, 3))
        else:
            raw_dtype = PIXEL_TYPES[pixel_type]["dtype"].newbyteorder(">")
            input_array = array

        for imseg, first_row in zip(imsegs, first_rows):
            self._file_object.seek(imseg["Data"].get_offset(), os.SEEK_SET)

            # Could break this into blocks to reduce memory usage from byte swapping
            raw_array = input_array[
                first_row : first_row + imseg["SubHeader"]["NROWS"].value
            ]
            raw_array = raw_array.astype(raw_dtype.newbyteorder(">"), copy=False)
            raw_array.tofile(self._file_object)

        self._images_written.add(image_number)

    def write_legend(self, legend_number, array):
        """Write legend pixel data to a NITF file

        Parameters
        ----------
        legend_number : int
            index of legend to write
        array : ndarray
            2D array of pixels
        """
        raise NotImplementedError()

    def write_ded(self, array):
        """Write DED data to a NITF file

        Parameters
        ----------
        array : ndarray
            2D array of pixels
        """
        raise NotImplementedError()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        images_expected = set(range(len(self._nitf_plan.images)))
        images_missing = images_expected - self._images_written
        if images_missing:
            logger.warning(
                f"SIDD Writer closed without writing all images. Missing: {images_missing}"
            )
        # TODO check legends, DED
        return


@dataclasses.dataclass(kw_only=True)
class SegmentationImhdr:
    """Per segment values computed by the SIDD Segmentation Algorithm"""

    idlvl: int
    ialvl: int
    iloc: str
    iid1: str
    nrows: int
    ncols: int
    igeolo: str


def segmentation_algorithm(
    sidd_xmltrees: collections.abc.Iterable[lxml.etree.ElementTree],
) -> tuple[int, list[int], list[SegmentationImhdr]]:
    """Implementation of section 2.4.2.1 Segmentation Algorithm and 2.4.2.2 Image Segment Corner Coordinate Parameters

    Parameters
    ----------
    sicd_xmltrees : iterable of lxml.etree.ElementTree
        SIDD XML Metadata instances

    Returns
    -------
    fhdr_numi: int
        Number of NITF image segments
    fhdr_li: list of int
        Length of each NITF image segment
    seginfos: list of :py:class:`SegmentationImhdr`
        Image Segment subheader information
    """
    z = 0
    fhdr_numi = 0
    fhdr_li = []
    seginfos = []

    for k, sidd_xmltree in enumerate(sidd_xmltrees):
        xml_helper = sksidd.XmlHelper(sidd_xmltree)
        pixel_info = PIXEL_TYPES[xml_helper.load("./{*}Display/{*}PixelType")]
        num_rows_k = xml_helper.load("./{*}Measurement/{*}PixelFootprint/{*}Row")
        num_cols_k = xml_helper.load("./{*}Measurement/{*}PixelFootprint/{*}Col")

        pcc = xml_helper.load(
            "./{*}GeoData/{*}ImageCorners"
        )  # Document says /SIDD/GeographicAndTarget/GeogrpahicCoverage/Footprint, but that was renamed in v2.0

        bytes_per_pixel = pixel_info[
            "dtype"
        ].itemsize  # Document says NBANDS, but that doesn't work for 16bit
        bytes_per_row = (
            bytes_per_pixel * num_cols_k
        )  # Document says NumRows(k), but that doesn't make sense
        num_rows_limit_k = min(LI_MAX // bytes_per_row, ILOC_MAX)

        product_size = bytes_per_pixel * num_rows_k * num_cols_k
        if product_size <= LI_MAX:
            z += 1
            fhdr_numi += 1
            fhdr_li.append(product_size)
            seginfos.append(
                SegmentationImhdr(
                    idlvl=z,
                    ialvl=0,
                    iloc="0000000000",
                    iid1=f"SIDD{k + 1:03d}001",  # Document says 'm', but there is no m variable
                    nrows=num_rows_k,
                    ncols=num_cols_k,
                    igeolo=sarkit.sicd._io._format_igeolo(pcc),
                )
            )
        else:
            num_seg_per_image_k = int(np.ceil(num_rows_k / num_rows_limit_k))
            z += 1
            fhdr_numi += num_seg_per_image_k
            fhdr_li.append(bytes_per_pixel * num_rows_limit_k * num_cols_k)
            this_image_seginfos = []
            this_image_seginfos.append(
                SegmentationImhdr(
                    idlvl=z,
                    ialvl=0,
                    iloc="0000000000",
                    iid1=f"SIDD{k + 1:03d}001",  # Document says 'm', but there is no m variable
                    nrows=num_rows_limit_k,
                    ncols=num_cols_k,
                    igeolo="",
                )
            )
            for n in range(1, num_seg_per_image_k - 1):
                z += 1
                fhdr_li.append(bytes_per_pixel * num_rows_limit_k * num_cols_k)
                this_image_seginfos.append(
                    SegmentationImhdr(
                        idlvl=z,
                        ialvl=z - 1,
                        iloc=f"{num_rows_limit_k:05d}00000",
                        iid1=f"SIDD{k + 1:03d}{n + 1:03d}",
                        nrows=num_rows_limit_k,
                        ncols=num_cols_k,
                        igeolo="",
                    )
                )
            z += 1
            last_seg_rows = num_rows_k - (num_seg_per_image_k - 1) * num_rows_limit_k
            fhdr_li.append(bytes_per_pixel * last_seg_rows * num_cols_k)
            this_image_seginfos.append(
                SegmentationImhdr(
                    idlvl=z,
                    ialvl=z - 1,
                    iloc=f"{num_rows_limit_k:05d}00000",  # Document says "lastSegRows", but we need the number of rows in the previous IS
                    iid1=f"SIDD{k + 1:03d}{num_seg_per_image_k:03d}",
                    nrows=last_seg_rows,
                    ncols=num_cols_k,
                    igeolo="",
                )
            )
            seginfos.extend(this_image_seginfos)

            pcc_ecef = sarkit.wgs84.geodetic_to_cartesian(
                np.hstack((pcc, [[0], [0], [0], [0]]))
            )
            for geo_z, seginfo in enumerate(this_image_seginfos):
                wgt1 = geo_z * num_rows_limit_k / num_rows_k
                wgt2 = 1 - wgt1
                wgt3 = (geo_z * num_rows_limit_k + seginfo.nrows) / num_rows_k
                wgt4 = 1 - wgt3
                iscc_ecef = [
                    wgt2 * pcc_ecef[0] + wgt1 * pcc_ecef[3],
                    wgt2 * pcc_ecef[1] + wgt1 * pcc_ecef[2],
                    wgt4 * pcc_ecef[1] + wgt3 * pcc_ecef[2],
                    wgt4 * pcc_ecef[0] + wgt3 * pcc_ecef[3],
                ]
                iscc = sarkit.wgs84.cartesian_to_geodetic(iscc_ecef)[:, :2]
                seginfo.igeolo = sarkit.sicd._io._format_igeolo(iscc)

    return fhdr_numi, fhdr_li, seginfos


def _validate_xml(sidd_xmltree):
    """Validate a SIDD XML tree against the schema"""

    xmlns = lxml.etree.QName(sidd_xmltree.getroot()).namespace
    if xmlns not in VERSION_INFO:
        latest_xmlns = list(VERSION_INFO.keys())[-1]
        logger.warning(f"Unknown SIDD namespace {xmlns}, assuming {latest_xmlns}")
        xmlns = latest_xmlns
    schema = lxml.etree.XMLSchema(file=VERSION_INFO[xmlns]["schema"])
    valid = schema.validate(sidd_xmltree)
    if not valid:
        warnings.warn(str(schema.error_log))
    return valid
