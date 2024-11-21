"""
=====================================
Compensated Phase History Data (CPHD)
=====================================

Python reference implementations of the suite of NGA.STND.0068 standardization
documents that define the Compensated Phase History Data (CPHD) format.

Supported Versions
==================

* `CPHD 1.0.1`_
* `CPHD 1.1.0`_

Functions
=========

Reading and Writing
-------------------

.. autosummary::
   :toctree: generated/

   CphdReader
   CphdWriter

I/O Helpers
-----------

.. autosummary::
   :toctree: generated/

   CphdPlan
   CphdFileHeaderFields

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

from .io import (
    CphdFileHeaderFields,
    CphdPlan,
    CphdReader,
    CphdWriter,
)

# IO
__all__ = [
    "CphdFileHeaderFields",
    "CphdPlan",
    "CphdReader",
    "CphdWriter",
]
