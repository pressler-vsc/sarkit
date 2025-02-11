"""
====================================================
Sensor Independent Derived Data (:mod:`sarkit.sidd`)
====================================================

Python reference implementations of the suite of NGA.STND.0025 standardization
documents that define the Sensor Independent Derived Data (SIDD) format.

Supported Versions
==================

* `SIDD 2.0`_
* `SIDD 3.0`_

Data Structure & File Format
============================

.. autosummary::
   :toctree: generated/

   SiddNitfHeaderFields
   SiddNitfSecurityFields
   SiddNitfImageSegmentFields
   SiddNitfDESegmentFields
   SiddNitfReader
   SiddNitfPlan
   SiddNitfPlanProductImageInfo
   SiddNitfPlanLegendInfo
   SiddNitfPlanDedInfo
   SiddNitfPlanProductSupportXmlInfo
   SiddNitfPlanSicdXmlInfo
   SiddNitfWriter
   SegmentationImhdr
   segmentation_algorithm

XML Metadata
============

.. autosummary::
   :toctree: generated/

   XmlHelper
   AngleMagnitudeType
   FilterCoefficientType
   ImageCornersType
   IntListType
   RangeAzimuthType
   RowColDblType
   SfaPointType

Constants
=========

.. list-table::

   * - ``VERSION_INFO``
     - `dict` of {xml namespace: version-specific information}
   * - ``PIXEL_TYPES``
     - `dict` of {PixelType: pixel-type-specific information}
   * - ``LI_MAX``
     - maximum NITF image segment length in bytes (:math:`10^{10}-2`)
   * - ``ILOC_MAX``
     - maximum number of rows contained in a NITF image segment (99,999)
   * - ``TRANSCODERS``
     - `dict` of {name: transcoder}

References
==========

SIDD 2.0
--------
.. [NGA.STND.0025-1_2.0] National Center for Geospatial Intelligence Standards,
   "Sensor Independent Derived Data (SIDD), Vol. 1, Design & Implementation Description Document,
   Version 2.0", 2019.
   https://nsgreg.nga.mil/doc/view?i=4906

.. [NGA.STND.0025-2_2.0] National Center for Geospatial Intelligence Standards,
   "Sensor Independent Derived Data (SIDD), Vol. 2, NITF File Format Description Document,
   Version 2.0", 2019.
   https://nsgreg.nga.mil/doc/view?i=4907

SIDD 3.0
--------
.. [NGA.STND.0025-1_3.0] National Center for Geospatial Intelligence Standards,
   "Sensor Independent Derived Data (SIDD), Vol. 1, Design & Implementation Description Document,
   Version 3.0", 2021.
   https://nsgreg.nga.mil/doc/view?i=5440

.. [NGA.STND.0025-2_3.0] National Center for Geospatial Intelligence Standards,
   "Sensor Independent Derived Data (SIDD), Vol. 2, NITF File Format Description Document,
   Version 3.0", 2021.
   https://nsgreg.nga.mil/doc/view?i=5441

"""

from ._io import (
    ILOC_MAX,
    LI_MAX,
    PIXEL_TYPES,
    VERSION_INFO,
    SegmentationImhdr,
    SiddNitfDESegmentFields,
    SiddNitfHeaderFields,
    SiddNitfImageSegmentFields,
    SiddNitfPlan,
    SiddNitfPlanDedInfo,
    SiddNitfPlanLegendInfo,
    SiddNitfPlanProductImageInfo,
    SiddNitfPlanProductSupportXmlInfo,
    SiddNitfPlanSicdXmlInfo,
    SiddNitfReader,
    SiddNitfSecurityFields,
    SiddNitfWriter,
    segmentation_algorithm,
)

# TODO: all of the other transcoder types
from ._xml import (
    TRANSCODERS,
    AngleMagnitudeType,
    FilterCoefficientType,
    ImageCornersType,
    IntListType,
    RangeAzimuthType,
    RowColDblType,
    SfaPointType,
    XmlHelper,
)

__all__ = [
    "ILOC_MAX",
    "LI_MAX",
    "PIXEL_TYPES",
    "TRANSCODERS",
    "VERSION_INFO",
    "AngleMagnitudeType",
    "FilterCoefficientType",
    "ImageCornersType",
    "IntListType",
    "RangeAzimuthType",
    "RowColDblType",
    "SegmentationImhdr",
    "SfaPointType",
    "SiddNitfDESegmentFields",
    "SiddNitfHeaderFields",
    "SiddNitfImageSegmentFields",
    "SiddNitfPlan",
    "SiddNitfPlanDedInfo",
    "SiddNitfPlanLegendInfo",
    "SiddNitfPlanProductImageInfo",
    "SiddNitfPlanProductSupportXmlInfo",
    "SiddNitfPlanSicdXmlInfo",
    "SiddNitfReader",
    "SiddNitfSecurityFields",
    "SiddNitfWriter",
    "XmlHelper",
    "segmentation_algorithm",
]
