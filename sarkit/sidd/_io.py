"""
Functions to read and write SIDD files.
"""

import collections
import dataclasses
import datetime
import importlib
import itertools
import logging
import warnings
from typing import Final, Self, TypedDict

import lxml.etree
import numpy as np
import numpy.typing as npt

import sarkit._nitf.nitf
import sarkit._nitf.nitf_elements.des
import sarkit._nitf.nitf_elements.image
import sarkit._nitf.nitf_elements.nitf_head
import sarkit._nitf.nitf_elements.security
import sarkit._nitf.utils
import sarkit.sicd as sksicd
import sarkit.sicd._io
import sarkit.sidd._xml

logger = logging.getLogger(__name__)

SPECIFICATION_IDENTIFIER: Final[str] = (
    "SIDD Volume 1 Design & Implementation Description Document"
)

SCHEMA_DIR = importlib.resources.files("sarkit.sidd.schemas")

# Keys in ascending order
VERSION_INFO: Final[dict] = {
    "urn:SIDD:2.0.0": {
        "version": "3.0",
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
    dtype: np.dtype


PIXEL_TYPES: Final[dict[str, _PixelTypeDict]] = {
    "MONO8I": {
        "IREP": "MONO",
        "IREPBANDn": ["M"],
        "IMODE": "B",
        "dtype": np.dtype(np.uint8),
    },
    "MONO8LU": {
        "IREP": "MONO",
        "IREPBANDn": ["LU"],
        "IMODE": "B",
        "dtype": np.dtype(np.uint8),
    },
    "MONO16I": {
        "IREP": "MONO",
        "IREPBANDn": ["M"],
        "IMODE": "B",
        "dtype": np.dtype(np.uint16),
    },
    "RGB8LU": {
        "IREP": "RGB/LUT",
        "IREPBANDn": ["LU"],
        "IMODE": "B",
        "dtype": np.dtype(np.uint8),
    },
    "RGB24I": {
        "IREP": "RGB",
        "IREPBANDn": ["R", "G", "B"],
        "IMODE": "P",
        "dtype": np.dtype([("R", np.uint8), ("G", np.uint8), ("B", np.uint8)]),
    },
}

LI_MAX: Final[int] = 9_999_999_998
ILOC_MAX: Final[int] = 99_999


# SICD implementation happens to match, reuse it
class NitfSecurityFields(sksicd.SicdNitfSecurityFields):
    __doc__ = sksicd.SicdNitfSecurityFields.__doc__


# SICD implementation happens to match, reuse it
class NitfFileHeaderPart(sksicd.SicdNitfHeaderFields):
    __doc__ = sksicd.SicdNitfHeaderFields.__doc__


@dataclasses.dataclass(kw_only=True)
class NitfImSubheaderPart:
    """NITF image subheader fields which are set according to a Program Specific Implementation Document

    Attributes
    ----------
    tgtid : str
        Target Identifier
    iid2 : str
        Image Identifier 2
    security : NitfSecurityFields
        Security Tags with "IS" prefix
    icom : list of str
        Image Comments
    """

    ## IS fields are applied to all segments
    tgtid: str = ""
    iid2: str = ""
    security: NitfSecurityFields
    icom: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def _from_header(cls, image_header: sarkit._nitf.nitf.ImageSegmentHeader) -> Self:
        """Construct from a NITF ImageSegmentHeader object"""
        return cls(
            tgtid=image_header.TGTID,
            iid2=image_header.IID2,
            security=NitfSecurityFields._from_security_tags(image_header.Security),
            icom=[
                val.to_bytes().decode().rstrip() for val in image_header.Comments.values
            ],
        )

    def __post_init__(self):
        if isinstance(self.security, dict):
            self.security = NitfSecurityFields(**self.security)


# SICD implementation happens to match, reuse it
class NitfDeSubheaderPart(sksicd.SicdNitfDESegmentFields):
    __doc__ = sksicd.SicdNitfDESegmentFields.__doc__


@dataclasses.dataclass
class NitfLegendMetadata:
    """SIDD NITF legend metadata"""

    def __post_init__(self):
        raise NotImplementedError()


@dataclasses.dataclass(kw_only=True)
class NitfProductImageMetadata:
    """SIDD NITF product image metadata

    Attributes
    ----------
    xmltree : lxml.etree.ElementTree
        SIDD XML
    im_subheader_part : NitfImSubheaderPart
        NITF image subheader fields which can be set
    de_subheader_part : NitfDeSubheaderPart
        NITF DES subheader fields which can be set
    legends : list of NitfLegendMetadata
        Metadata for legend(s) attached to this image
    """

    xmltree: lxml.etree.ElementTree
    im_subheader_part: NitfImSubheaderPart
    de_subheader_part: NitfDeSubheaderPart
    legends: list[NitfLegendMetadata] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        _validate_xml(self.xmltree)
        if isinstance(self.im_subheader_part, dict):
            self.im_subheader_part = NitfImSubheaderPart(**self.im_subheader_part)
        if isinstance(self.de_subheader_part, dict):
            self.de_subheader_part = NitfDeSubheaderPart(**self.de_subheader_part)


@dataclasses.dataclass
class NitfDedMetadata:
    """SIDD NITF DED metadata"""

    def __post_init__(self):
        raise NotImplementedError()


@dataclasses.dataclass
class NitfProductSupportXmlMetadata:
    """SIDD NITF product support XML metadata

    Attributes
    ----------
    xmltree : lxml.etree.ElementTree
        SIDD product support XML
    de_subheader_part : NitfDeSubheaderPart
        NITF DES subheader fields which can be set
    """

    xmltree: lxml.etree.ElementTree
    de_subheader_part: NitfDeSubheaderPart

    def __post_init__(self):
        if isinstance(self.de_subheader_part, dict):
            self.de_subheader_part = NitfDeSubheaderPart(**self.de_subheader_part)


@dataclasses.dataclass
class NitfSicdXmlMetadata:
    """SIDD NITF SICD XML metadata

    Attributes
    ----------
    xmltree : lxml.etree.ElementTree
        SICD XML
    de_subheader_part : NitfDeSubheaderPart
        NITF DES subheader fields which can be set
    """

    xmltree: lxml.etree.ElementTree
    de_subheader_part: sksicd.SicdNitfDESegmentFields

    def __post_init__(self):
        if isinstance(self.de_subheader_part, dict):
            self.de_subheader_part = sksicd.SicdNitfDESegmentFields(
                **self.de_subheader_part
            )


@dataclasses.dataclass(kw_only=True)
class NitfMetadata:
    """Settable SIDD NITF metadata

    Attributes
    ----------
    file_header_part : NitfFileHeaderPart
        NITF file header fields which can be set
    images : list of NitfProductImageMetadata
        Settable metadata for the product image(s)
    ded : NitfDedMetadata or None
        Settable metadata for the Digital Elevation Data
    product_support_xmls : list of NitfProductSupportXmlMetadata
        Settable metadata for the product support XML(s)
    sicd_xmls : list of NitfSicdXmlMetadata
        Settable metadata for the SICD XML(s)
    """

    file_header_part: NitfFileHeaderPart
    images: list[NitfProductImageMetadata] = dataclasses.field(default_factory=list)
    ded: NitfDedMetadata | None = None
    product_support_xmls: list[NitfProductSupportXmlMetadata] = dataclasses.field(
        default_factory=list
    )
    sicd_xmls: list[NitfSicdXmlMetadata] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.file_header_part, dict):
            self.file_header_part = NitfFileHeaderPart(**self.file_header_part)


class NitfReader:
    """Read a SIDD NITF

    A NitfReader object should be used as a context manager in a ``with`` statement.
    Attributes, but not methods, can be safely accessed outside of the context manager's context.

    Parameters
    ----------
    file : `file object`
        SIDD NITF file to read

    Examples
    --------
    >>> with sidd_path.open('rb') as file, NitfReader(file) as reader:
    ...     sidd_xmltree = reader.metadata.images[0].xmltree
    ...     pixels = reader.read_image(0)

    Attributes
    ----------
    metadata : NitfMetadata
        SIDD NITF metadata

    See Also
    --------
    NitfWriter
    """

    def __init__(self, file):
        self._file = file

        self._initial_offset = self._file.tell()
        if self._initial_offset != 0:
            raise RuntimeError(
                "seek(0) must be the start of the NITF"
            )  # this is a NITFDetails limitation

        self._nitf_details = sarkit._nitf.nitf.NITFDetails(self._file)

        im_segments = {}
        for imseg_index, img_header in enumerate(self._nitf_details.img_headers):
            if img_header.IID1.startswith("SIDD"):
                if img_header.ICAT == "SAR":
                    image_number = int(img_header.IID1[4:7]) - 1
                    im_segments.setdefault(image_number, [])
                    im_segments[image_number].append(imseg_index)
                else:
                    raise NotImplementedError("Non SAR images not supported")  # TODO
            elif img_header.IID1.startswith("DED"):
                raise NotImplementedError("DED not supported")  # TODO

        image_segment_collections = {}
        for idx, imghdr in enumerate(self._nitf_details.img_headers):
            if not imghdr.IID1.startswith("SIDD"):
                continue
            image_num = int(imghdr.IID1[4:7]) - 1
            image_segment_collections.setdefault(image_num, [])
            image_segment_collections[image_num].append(idx)

        self._nitf_reader = sarkit._nitf.nitf.NITFReader(
            nitf_details=self._nitf_details,
            image_segment_collections=tuple(
                (tuple(val) for val in image_segment_collections.values())
            ),
        )

        self.header_fields = NitfFileHeaderPart._from_header(
            self._nitf_details.nitf_header
        )
        self.metadata = NitfMetadata(file_header_part=self.header_fields)

        image_number = 0
        for idx in range(self._nitf_details.des_subheader_offsets.size):
            subhead_bytes = self._nitf_details.get_des_subheader_bytes(idx)
            des_header = sarkit._nitf.nitf.DataExtensionHeader.from_bytes(
                self._nitf_details.get_des_subheader_bytes(0), 0
            )
            if subhead_bytes.startswith(b"DEXML_DATA_CONTENT"):
                des_bytes = self._nitf_details.get_des_bytes(idx)
                try:
                    xmltree = lxml.etree.fromstring(des_bytes).getroottree()
                except lxml.etree.XMLSyntaxError:
                    logger.error(f"Failed to parse DES {idx} as XML")
                    continue

                if "SIDD" in xmltree.getroot().tag:
                    nitf_de_fields = NitfDeSubheaderPart._from_header(des_header)
                    if len(self.metadata.images) < len(image_segment_collections):
                        # user settable fields should be the same for all image segments
                        im_idx = im_segments[image_number][0]
                        self.metadata.images.append(
                            NitfProductImageMetadata(
                                xmltree=xmltree,
                                im_subheader_part=NitfImSubheaderPart._from_header(
                                    self._nitf_details.img_headers[im_idx]
                                ),
                                de_subheader_part=nitf_de_fields,
                            )
                        )
                        image_number += 1
                    else:
                        # No matching product image, treat it as a product support XML
                        self.metadata.product_support_xmls.append(
                            NitfProductSupportXmlMetadata(xmltree, nitf_de_fields)
                        )
                elif "SICD" in xmltree.getroot().tag:
                    nitf_de_fields = sksicd.SicdNitfDESegmentFields._from_header(
                        des_header
                    )
                    self.metadata.sicd_xmls.append(
                        NitfSicdXmlMetadata(xmltree, nitf_de_fields)
                    )
                else:
                    nitf_de_fields = NitfDeSubheaderPart._from_header(des_header)
                    self.metadata.product_support_xmls.append(
                        NitfProductSupportXmlMetadata(xmltree, nitf_de_fields)
                    )

        # TODO Legends
        # TODO DED
        assert not any(x.legends for x in self.metadata.images)
        assert not self.metadata.ded

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
        return self._nitf_reader.read(index=image_number)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        return


class NitfWriter:
    """Write a SIDD NITF

    A NitfWriter object should be used as a context manager in a ``with`` statement.

    Parameters
    ----------
    file : `file object`
        SIDD NITF file to write
    metadata : NitfMetadata
        SIDD NITF metadata to write

    Notes
    -----
    ``metadata`` should not be modified after creation of a writer

    Examples
    --------
    Write a SIDD NITF with a single product image

    .. doctest::

        >>> import sarkit.sidd as sksidd

    Build the product image description and pixels

    .. doctest::

        >>> import lxml.etree
        >>> sidd_xml = lxml.etree.parse("data/example-sidd-3.0.0.xml")

        >>> sec = sksidd.NitfSecurityFields(clas="U")
        >>> img_meta = sksidd.NitfProductImageMetadata(
        ...     xmltree=sidd_xml,
        ...     im_subheader_part=sksidd.NitfImSubheaderPart(security=sec),
        ...     de_subheader_part=sksidd.NitfDeSubheaderPart(security=sec),
        ... )

        >>> import numpy as np
        >>> img_to_write = np.zeros(
        ...     sksidd.XmlHelper(sidd_xml).load("{*}Measurement/{*}PixelFootprint"),
        ...     dtype=sksidd.PIXEL_TYPES[sidd_xml.findtext("{*}Display/{*}PixelType")]["dtype"],
        ... )

    Place the product image in a NITF metadata object

    .. doctest::

        >>> meta = sksidd.NitfMetadata(
        ...     file_header_part=sksidd.NitfFileHeaderPart(ostaid="my station", security=sec),
        ...     images=[img_meta],
        ... )

    Write the SIDD NITF to a file

    .. doctest::

        >>> from tempfile import NamedTemporaryFile
        >>> outfile = NamedTemporaryFile()
        >>> with sksidd.NitfWriter(outfile, meta) as w:
        ...     w.write_image(0, img_to_write)

    See Also
    --------
    NitfReader
    """

    def __init__(self, file, metadata: NitfMetadata):
        self._file = file
        self._metadata = metadata
        self._images_written: set[int] = set()

        self._initial_offset = self._file.tell()
        if self._initial_offset != 0:
            raise RuntimeError(
                "seek(0) must be the start of the NITF"
            )  # this is a NITFDetails limitation

        # CLEVEL and FL will be corrected...
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        header = sarkit._nitf.nitf_elements.nitf_head.NITFHeader(
            CLEVEL=3,
            OSTAID=self._metadata.file_header_part.ostaid,
            FDT=now_dt.strftime("%Y%m%d%H%M%S"),
            FTITLE=self._metadata.file_header_part.ftitle,
            Security=self._metadata.file_header_part.security._as_security_tags(),
            ONAME=self._metadata.file_header_part.oname,
            OPHONE=self._metadata.file_header_part.ophone,
            FL=0,
        )

        image_managers = []
        image_segment_collections: dict[
            int, list[int]
        ] = {}  # image_num -> [image_segment, ...]
        image_segment_coordinates: dict[
            int, list[tuple[int, int, int, int]]
        ] = {}  # image_num -> [(first_row, last_row, first_col, last_col), ...]
        current_start_row = 0
        _, _, imhdrs = segmentation_algorithm(
            (img.xmltree for img in self._metadata.images)
        )
        for idx, imhdr in enumerate(imhdrs):
            if imhdr.ialvl == 0:
                # first segment of each SAR image is attached to the CCS
                current_start_row = 0
            image_num = int(imhdr.iid1[4:7]) - 1
            image_segment_collections.setdefault(image_num, [])
            image_segment_coordinates.setdefault(image_num, [])
            image_segment_collections[image_num].append(idx)
            image_segment_coordinates[image_num].append(
                (current_start_row, current_start_row + imhdr.nrows, 0, imhdr.ncols)
            )
            current_start_row += imhdr.nrows

            imageinfo = self._metadata.images[image_num]
            xml_helper = sarkit.sidd._xml.XmlHelper(imageinfo.xmltree)
            pixel_info = PIXEL_TYPES[xml_helper.load("./{*}Display/{*}PixelType")]

            icp = xml_helper.load("./{*}GeoData/{*}ImageCorners")
            rows = xml_helper.load("./{*}Measurement/{*}PixelFootprint/{*}Row")
            cols = xml_helper.load("./{*}Measurement/{*}PixelFootprint/{*}Col")

            subhead = sarkit._nitf.nitf_elements.image.ImageSegmentHeader(
                IID1=imhdr.iid1,
                IDATIM=xml_helper.load(
                    "./{*}ExploitationFeatures/{*}Collection/{*}Information/{*}CollectionDateTime"
                ).strftime("%Y%m%d%H%M%S"),
                TGTID=imageinfo.im_subheader_part.tgtid,
                IID2=imageinfo.im_subheader_part.iid2,
                Security=imageinfo.im_subheader_part.security._as_security_tags(),
                ISORCE=xml_helper.load(
                    "./{*}ExploitationFeatures/{*}Collection/{*}Information/{*}SensorName"
                ),
                NROWS=imhdr.nrows,
                NCOLS=imhdr.ncols,
                PVTYPE="INT",
                IREP=pixel_info["IREP"],
                ICAT="SAR",
                ABPP=pixel_info["dtype"].itemsize * 8,
                ICORDS="G",
                IGEOLO=sarkit._nitf.utils._interpolate_corner_points_string(
                    np.array(image_segment_coordinates[image_num][-1], dtype=np.int64),
                    rows,
                    cols,
                    icp,
                ),
                Comments=sarkit._nitf.nitf_elements.image.ImageComments(
                    [
                        sarkit._nitf.nitf_elements.image.ImageComment(COMMENT=comment)
                        for comment in imageinfo.im_subheader_part.icom
                    ]
                ),
                IC="NC",
                IMODE=pixel_info["IMODE"],
                NPPBH=0 if imhdr.ncols > 8192 else imhdr.ncols,
                NPPBV=0 if imhdr.nrows > 8192 else imhdr.nrows,
                NBPP=pixel_info["dtype"].itemsize * 8,
                NBPC=1,
                NBPR=1,
                IDLVL=imhdr.idlvl,
                IALVL=imhdr.ialvl,
                ILOC=imhdr.iloc,
                Bands=sarkit._nitf.nitf_elements.image.ImageBands(
                    values=[
                        sarkit._nitf.nitf_elements.image.ImageBand(
                            ISUBCAT="", IREPBAND=entry
                        )
                        for entry in pixel_info["IREPBANDn"]
                    ]
                ),
            )
            image_managers.append(sarkit._nitf.nitf.ImageSubheaderManager(subhead))

        # TODO add image_managers for legends
        assert not any(x.legends for x in self._metadata.images)
        # TODO add image_managers for DED
        assert not self._metadata.ded

        # DE Segments

        des_managers = []
        for imageinfo in self._metadata.images:
            xmlns = lxml.etree.QName(imageinfo.xmltree.getroot()).namespace
            xml_helper = sarkit.sidd._xml.XmlHelper(imageinfo.xmltree)
            icp = xml_helper.load("./{*}GeoData/{*}ImageCorners")
            desshlpg = ""
            for icp_lat, icp_lon in itertools.chain(icp, [icp[0]]):
                desshlpg += f"{icp_lat:0=+12.8f}{icp_lon:0=+13.8f}"

            deshead = sarkit._nitf.nitf_elements.des.DataExtensionHeader(
                Security=imageinfo.de_subheader_part.security._as_security_tags(),
                UserHeader=sarkit._nitf.nitf_elements.des.XMLDESSubheader(
                    DESSHSI=SPECIFICATION_IDENTIFIER,
                    DESSHSV=VERSION_INFO[xmlns]["version"],
                    DESSHSD=VERSION_INFO[xmlns]["date"],
                    DESSHTN=xmlns,
                    DESSHDT=now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    DESSHLPG=desshlpg,
                    DESSHRP=imageinfo.de_subheader_part.desshrp,
                    DESSHLI=imageinfo.de_subheader_part.desshli,
                    DESSHLIN=imageinfo.de_subheader_part.desshlin,
                    DESSHABS=imageinfo.de_subheader_part.desshabs,
                ),
            )
            des_managers.append(
                sarkit._nitf.nitf.DESSubheaderManager(
                    deshead, lxml.etree.tostring(imageinfo.xmltree)
                )
            )

        # Product Support XML DES
        for prodinfo in self._metadata.product_support_xmls:
            sidd_uh = des_managers[0].subheader.UserHeader
            xmlns = lxml.etree.QName(prodinfo.xmltree.getroot()).namespace or ""
            deshead = sarkit._nitf.nitf_elements.des.DataExtensionHeader(
                Security=prodinfo.de_subheader_part.security._as_security_tags(),
                UserHeader=sarkit._nitf.nitf_elements.des.XMLDESSubheader(
                    DESSHSI=sidd_uh.DESSHSI,
                    DESSHSV="v" + sidd_uh.DESSHSV,
                    DESSHSD=sidd_uh.DESSHSD,
                    DESSHTN=xmlns,
                    DESSHDT=now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    DESSHLPG="",
                    DESSHRP=prodinfo.de_subheader_part.desshrp,
                    DESSHLI=prodinfo.de_subheader_part.desshli,
                    DESSHLIN=prodinfo.de_subheader_part.desshlin,
                    DESSHABS=prodinfo.de_subheader_part.desshabs,
                ),
            )
            des_managers.append(
                sarkit._nitf.nitf.DESSubheaderManager(
                    deshead, lxml.etree.tostring(prodinfo.xmltree)
                )
            )

        # SICD XML DES
        for sicd_xml_info in self._metadata.sicd_xmls:
            des_managers.append(
                sarkit.sicd._io._create_des_manager(
                    sicd_xml_info.xmltree, sicd_xml_info.de_subheader_part
                )
            )

        writing_details = sarkit._nitf.nitf.NITFWritingDetails(
            header,
            image_managers=tuple(image_managers),
            image_segment_collections=tuple(
                (tuple(val) for val in image_segment_collections.values())
            ),
            image_segment_coordinates=tuple(
                (tuple(val) for val in image_segment_coordinates.values())
            ),
            des_managers=tuple(des_managers),
        )

        self._nitf_writer = sarkit._nitf.nitf.NITFWriter(
            file_object=self._file,
            writing_details=writing_details,
        )

    def write_image(self, image_number: int, array: npt.NDArray):
        """Write product pixel data to a NITF file

        Parameters
        ----------
        image_number : int
            index of SIDD Product image to write
        array : ndarray
            2D array of pixels
        """
        self._nitf_writer.write(array, index=image_number)
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
        self._nitf_writer.close()
        images_expected = set(range(len(self._metadata.images)))
        images_missing = images_expected - self._images_written
        if images_missing:
            logger.warning(
                f"SIDD Writer closed without writing all images. Missing: {images_missing}"
            )
        # TODO check legends, DED
        return


@dataclasses.dataclass(kw_only=True, frozen=True)
class SegmentationImhdr:
    """Per segment values computed by the SIDD Segmentation Algorithm"""

    idlvl: int
    ialvl: int
    iloc: str
    iid1: str
    nrows: int
    ncols: int


def segmentation_algorithm(
    sidd_xmltrees: collections.abc.Iterable[lxml.etree.ElementTree],
) -> tuple[int, list[int], list[SegmentationImhdr]]:
    """Implementation of section 2.4.2.1 Segmentation Algorithm

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
    imhdr: list of SegmentationImhdr
        Image Segment subheader information
    """
    z = 0
    fhdr_numi = 0
    fhdr_li = []
    imhdr = []

    for k, sidd_xmltree in enumerate(sidd_xmltrees):
        xml_helper = sarkit.sidd._xml.XmlHelper(sidd_xmltree)
        pixel_info = PIXEL_TYPES[xml_helper.load("./{*}Display/{*}PixelType")]
        num_rows_k = xml_helper.load("./{*}Measurement/{*}PixelFootprint/{*}Row")
        num_cols_k = xml_helper.load("./{*}Measurement/{*}PixelFootprint/{*}Col")
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
            imhdr.append(
                SegmentationImhdr(
                    idlvl=z,
                    ialvl=0,
                    iloc="0000000000",
                    iid1=f"SIDD{k + 1:03d}001",  # Document says 'm', but there is no m variable
                    nrows=num_rows_k,
                    ncols=num_cols_k,
                )
            )
        else:
            num_seg_per_image_k = int(np.ceil(num_rows_k / num_rows_limit_k))
            z += 1
            fhdr_numi += num_seg_per_image_k
            fhdr_li.append(bytes_per_pixel * num_rows_limit_k * num_cols_k)
            imhdr.append(
                SegmentationImhdr(
                    idlvl=z,
                    ialvl=0,
                    iloc="0000000000",
                    iid1=f"SIDD{k + 1:03d}001",  # Document says 'm', but there is no m variable
                    nrows=num_rows_limit_k,
                    ncols=num_cols_k,
                )
            )
            for n in range(1, num_seg_per_image_k - 1):
                z += 1
                fhdr_li.append(bytes_per_pixel * num_rows_limit_k * num_cols_k)
                imhdr.append(
                    SegmentationImhdr(
                        idlvl=z,
                        ialvl=z - 1,
                        iloc=f"{num_rows_limit_k:05d}00000",
                        iid1=f"SIDD{k + 1:03d}{n + 1:03d}",
                        nrows=num_rows_limit_k,
                        ncols=num_cols_k,
                    )
                )
            z += 1
            last_seg_rows = num_rows_k - (num_seg_per_image_k - 1) * num_rows_limit_k
            fhdr_li.append(bytes_per_pixel * last_seg_rows * num_cols_k)
            imhdr.append(
                SegmentationImhdr(
                    idlvl=z,
                    ialvl=z - 1,
                    iloc=f"{num_rows_limit_k:05d}00000",  # Document says "lastSegRows", but we need the number of rows in the previous IS
                    iid1=f"SIDD{k + 1:03d}{num_seg_per_image_k:03d}",
                    nrows=last_seg_rows,
                    ncols=num_cols_k,
                )
            )

    return fhdr_numi, fhdr_li, imhdr


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
