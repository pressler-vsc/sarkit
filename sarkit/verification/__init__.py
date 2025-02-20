"""
#########################################
Verification (:mod:`sarkit.verification`)
#########################################

Verification of SAR data in NGA standard formats.

Consistency Checking
====================

Python Interface
----------------

.. autosummary::
   :toctree: generated/
   :recursive:

   CphdConsistency
   CrsdConsistency
   SicdConsistency

In general, users will create a Consistency instance with ``from_file``, e.g.

.. doctest::

   >>> import sarkit.verification as skver
   >>> sicdcon = skver.SicdConsistency.from_file("data/example-sicd-1.4.0.xml")
   >>> sicdcon.check()
   >>> bool(sicdcon.failures())
   False
   >>> bool(sicdcon.passes())
   True

Command-Line Interface
----------------------

Each of the consistency checkers has a corresponding entry point:

.. code-block:: shell-session

   $ cphd-consistency /path/to/file
   $ crsd-consistency /path/to/file
   $ sicd-consistency /path/to/file

The command line flags for each are given below:

.. _cphd-consistency-cli:

.. autoprogram:: sarkit.verification._cphd_consistency:_parser()
   :prog: cphd-consistency

.. _crsd-consistency-cli:

.. autoprogram:: sarkit.verification._crsd_consistency:_parser()
   :prog: crsd-consistency

.. _sicd-consistency-cli:

.. autoprogram:: sarkit.verification._sicd_consistency:_parser()
   :prog: sicd-consistency
"""

from ._cphd_consistency import (
    CphdConsistency,
)
from ._crsd_consistency import (
    CrsdConsistency,
)
from ._sicd_consistency import (
    SicdConsistency,
)

__all__ = [
    "CphdConsistency",
    "CrsdConsistency",
    "SicdConsistency",
]
