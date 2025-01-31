"""
===================================================
Compensated Phase History Data (:mod:`sarkit.cphd`)
===================================================

Python reference implementations of the suite of NGA.STND.0068 standardization
documents that define the Compensated Phase History Data (CPHD) format.

Supported Versions
==================

* `CPHD 1.0.1`_
* `CPHD 1.1.0`_

Data Structure & File Format
============================

.. autosummary::
   :toctree: generated/

   CphdFileHeaderFields
   CphdReader
   CphdPlan
   CphdWriter
   read_file_header
   get_pvp_dtype
   binary_format_string_to_dtype
   dtype_to_binary_format_string
   mask_support_array

XML Metadata
============

.. autosummary::
   :toctree: generated/

   XmlHelper
   TxtType
   EnuType
   BoolType
   XdtType
   IntType
   DblType
   HexType
   LineSampType
   XyType
   XyzType
   LatLonType
   LatLonHaeType
   PolyType
   Poly2dType
   XyzPolyType
   PvpType
   AddedPvpType
   ImageAreaCornerPointsType

Constants
=========

.. list-table::

   * - ``VERSION_INFO``
     - `dict` of {xml namespace: version-specific information}
   * - ``DEFINED_HEADER_KEYS``
     - :external:py:obj:`set` of KVP keys defined in the standard
   * - ``CPHD_SECTION_TERMINATOR``
     - Two-byte sequence that marks the end of the file header
   * - ``TRANSCODERS``
     - `dict` of {name: `sarkit.xmlhelp.Type`}

References
==========

CPHD 1.0.1
----------
.. [NGA.STND.0068-1_1.0.1_CPHD] National Center for Geospatial Intelligence Standards,
   "Compensated Phase History Data (CPHD) Design & Implementation Description Document,
   Version 1.0.1", 2018.
   https://nsgreg.nga.mil/doc/view?i=4638

.. [CPHD_schema_V1.0.1_2018_05_21.xsd] National Center for Geospatial Intelligence Standards,
   "Compensated Phase History Data (CPHD) XML Schema, Version 1.0.1", 2018.
   https://nsgreg.nga.mil/doc/view?i=4639

CPHD 1.1.0
----------
.. [NGA.STND.0068-1_1.1.0_CPHD_2021-11-30] National Center for Geospatial Intelligence Standards,
   "Compensated Phase History Data (CPHD) Design & Implementation Description Document,
   Version 1.1.0", 2021.
   https://nsgreg.nga.mil/doc/view?i=5388

.. [CPHD_schema_V1.1.0_2021_11_30_FINAL.xsd] National Center for Geospatial Intelligence Standards,
   "Compensated Phase History Data (CPHD) XML Schema, Version 1.1.0", 2021.
   https://nsgreg.nga.mil/doc/view?i=5421
"""

from sarkit.xmlhelp import (
    BoolType,
    DblType,
    EnuType,
    HexType,
    IntType,
    LatLonHaeType,
    LatLonType,
    LineSampType,
    Poly2dType,
    PolyType,
    TxtType,
    XdtType,
    XyType,
    XyzPolyType,
    XyzType,
)

from ._io import (
    CPHD_SECTION_TERMINATOR,
    DEFINED_HEADER_KEYS,
    VERSION_INFO,
    CphdFileHeaderFields,
    CphdPlan,
    CphdReader,
    CphdWriter,
    binary_format_string_to_dtype,
    dtype_to_binary_format_string,
    get_pvp_dtype,
    mask_support_array,
    read_file_header,
)
from ._xml import (
    TRANSCODERS,
    AddedPvpType,
    ImageAreaCornerPointsType,
    PvpType,
    XmlHelper,
)

__all__ = [
    "CPHD_SECTION_TERMINATOR",
    "DEFINED_HEADER_KEYS",
    "TRANSCODERS",
    "VERSION_INFO",
    "AddedPvpType",
    "BoolType",
    "CphdFileHeaderFields",
    "CphdPlan",
    "CphdReader",
    "CphdWriter",
    "DblType",
    "EnuType",
    "HexType",
    "ImageAreaCornerPointsType",
    "IntType",
    "LatLonHaeType",
    "LatLonType",
    "LineSampType",
    "Poly2dType",
    "PolyType",
    "PvpType",
    "TxtType",
    "XdtType",
    "XmlHelper",
    "XyType",
    "XyzPolyType",
    "XyzType",
    "binary_format_string_to_dtype",
    "dtype_to_binary_format_string",
    "get_pvp_dtype",
    "mask_support_array",
    "read_file_header",
]
