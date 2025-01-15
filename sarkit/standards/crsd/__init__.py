"""
====================================
Compensated Radar Signal Data (CRSD)
====================================

Python reference implementations of the suite of NGA.STND.0080 standardization
documents that define the Compensated Radar Signal Data (CRSD) format.

Supported Versions
==================

* `CRSD 1.0.0`_

Functions
=========

Reading and Writing
-------------------

.. autosummary::
   :toctree: generated/

   CrsdReader
   CrsdWriter

I/O Helpers
-----------

.. autosummary::
   :toctree: generated/

   CrsdPlan
   CrsdFileHeaderFields

References
==========

CRSD 1.0.0
----------
TBD

"""

from .io import (
    CrsdFileHeaderFields,
    CrsdPlan,
    CrsdReader,
    CrsdWriter,
)

# IO
__all__ = [
    "CrsdFileHeaderFields",
    "CrsdPlan",
    "CrsdReader",
    "CrsdWriter",
]
