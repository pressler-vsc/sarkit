"""
======================================
Sensor Independent Derived Data (SIDD)
======================================

Python reference implementations of the suite of NGA.STND.0025 standardization
documents that define the Sensor Independent Derived Data (SIDD) format.

Supported Versions
==================

* `SIDD 2.0`_
* `SIDD 3.0`_

Functions
=========

Reading and Writing
-------------------

.. autosummary::
   :toctree: generated/

   SiddNitfReader
   SiddNitfWriter

I/O Helpers
-----------

.. autosummary::
   :toctree: generated/

   SiddNitfPlan
   SiddNitfSecurityFields
   SiddNitfHeaderFields
   SiddNitfImageSegmentFields
   SiddNitfDESegmentFields
   SiddNitfPlanProductImageInfo
   SiddNitfPlanLegendInfo
   SiddNitfPlanDedInfo
   SiddNitfPlanProductSupportXmlInfo
   SiddNitfPlanSicdXmlInfo

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

from .io import (
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
)

# IO
__all__ = [
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
]
