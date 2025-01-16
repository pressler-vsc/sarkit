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


import os  # noqa: I001
import sys  # noqa: I001

print(
    "\033[93m" if sys.stdout.isatty() and not os.environ.get("NO_COLOR") else "",
    "WARNING: SARkit's CRSD modules are provisional and implement the 2024-12-30 draft\n",
    "The modules will be updated and this message will be removed when the standard is published",
    "\x1b[0m" if sys.stdout.isatty() and not os.environ.get("NO_COLOR") else "",
    file=sys.stderr,
)
