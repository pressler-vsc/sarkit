.. _user_guide:

=================
SARkit User Guide
=================

:Release: |version|
:Date: |today|

SARkit contains readers and writers for SAR standards files and functions for operating on them.
This is an overview of basic SARkit functionality. For details, see the :doc:`reference/index`.

.. _installation:

Installation
============
Basic SARkit functionality relies on a small set of dependencies.
Some features require additional dependencies which can be installed using packaging extras:

.. code-block:: shell-session

   $ python -m pip install sarkit  # Install basics dependencies
   $ python -m pip install sarkit[processing]  # Install processing dependencies
   $ python -m pip install sarkit[verification]  # Install verification dependencies
   $ python -m pip install sarkit[all]  # Install all dependencies


Reading and writing files
=========================
SARkit provides reader/writer classes that are intended to be used as context managers and plan classes that are used to
describe file contents and metadata prior to writing.

.. list-table::

   * - Format
     - Reader
     - Plan
     - Writer
   * - ⛔ CRSD [Draft] ⛔
     - :py:class:`~sarkit.crsd.CrsdReader`
     - :py:class:`~sarkit.crsd.CrsdPlan`
     - :py:class:`~sarkit.crsd.CrsdWriter`
   * - CPHD
     - :py:class:`~sarkit.cphd.CphdReader`
     - :py:class:`~sarkit.cphd.CphdPlan`
     - :py:class:`~sarkit.cphd.CphdWriter`
   * - SICD
     - :py:class:`~sarkit.standards.sicd.SicdNitfReader`
     - :py:class:`~sarkit.standards.sicd.SicdNitfPlan`
     - :py:class:`~sarkit.standards.sicd.SicdNitfWriter`
   * - SIDD
     - :py:class:`~sarkit.sidd.SiddNitfReader`
     - :py:class:`~sarkit.sidd.SiddNitfPlan`
     - :py:class:`~sarkit.sidd.SiddNitfWriter`


Reading
-------

Readers are instantiated with a `file object` and file contents are accessed via format-specific attributes and methods.
In general, only the container information is accessed upon instantiation; further file access is deferred until
data access methods are called.
This pattern makes it faster to read components out of large files and is especially valuable for metadata access which
is often a small fraction of the size of a SAR data file.

.. testsetup::

   import pathlib
   import tempfile

   import lxml.etree
   import numpy as np

   import sarkit.standards.sicd.io as sarkit_sicd

   tmpdir = tempfile.TemporaryDirectory()
   tmppath = pathlib.Path(tmpdir.name)
   example_sicd = tmppath / "example.sicd"
   sec = {"security": {"clas": "U"}}
   parser = lxml.etree.XMLParser(remove_blank_text=True)
   example_sicd_xmltree = lxml.etree.parse("data/example-sicd-1.4.0.xml", parser)
   sicd_plan = sarkit_sicd.SicdNitfPlan(
       sicd_xmltree=example_sicd_xmltree,
       header_fields={"ostaid": "nowhere", "ftitle": "SARkit example SICD FTITLE"} | sec,
       is_fields={"isorce": "this sensor"} | sec,
       des_fields=sec,
   )
   with open(example_sicd, "wb") as f, sarkit_sicd.SicdNitfWriter(f, sicd_plan):
       pass  # don't currently care about the pixels


.. testcleanup::

   tmpdir.cleanup()

.. doctest::

   >>> with example_sicd.open("rb") as f, sarkit_sicd.SicdNitfReader(f) as reader:
   ...     pixels = reader.read_image()
   ...     pixels.shape
   (5727, 2362)

   # Reader attributes, but not methods, can be safely accessed outside of the
   # context manager's context

   # Access specific NITF fields that are called out in the SAR standards
   >>> reader.header_fields.ftitle
   'SARkit example SICD FTITLE'

   # XML metadata is returned as lxml.etree.ElementTree objects
   >>> (reader.sicd_xmltree.findtext(".//{*}FullImage/{*}NumRows"),
   ...  reader.sicd_xmltree.findtext(".//{*}FullImage/{*}NumCols"))
   ('5727', '2362')


Plans
-----

``Plan`` objects contain everything except the data.
This includes XML instance(s) and container metadata (PDD-settable NITF fields, CPHD header fields, etc.).
SARkit relies on plans because for many of the SAR standards it is more efficient to know up front what a file will
contain before writing.

Plans can be built from their components:

.. doctest::

   >>> plan_a = sarkit_sicd.SicdNitfPlan(
   ...     sicd_xmltree=example_sicd_xmltree,
   ...     header_fields={"ostaid": "my location", "security": {"clas": "U"}},
   ...     is_fields={"isorce": "my sensor", "security": {"clas": "U"}},
   ...     des_fields={"security": {"clas": "U"}},
   ... )

Plans are also available from readers:

.. doctest::

   >>> plan_b = reader.nitf_plan


Writing
-------

Writers are instantiated with a `file object` and a ``Plan`` object.
Similar to reading, instantiating a writer sets up the file while data is written using format-specific methods.

.. warning:: Plans should not be modified after creation of a writer.

.. doctest::

   >>> written_sicd = tmppath / "written.sicd"
   >>> with written_sicd.open("wb") as f, sarkit_sicd.SicdNitfWriter(f, plan_b) as writer:
   ...     writer.write_image(pixels)

   >>> with written_sicd.open("rb") as f:
   ...     f.read(9).decode()
   'NITF02.10'

SARkit sanity checks some aspects on write but it is up to the user to ensure consistency of the plan and data:

.. doctest::

   >>> bad_sicd = tmppath / "bad.sicd"
   >>> with bad_sicd.open("wb") as f, sarkit_sicd.SicdNitfWriter(f, plan_b) as writer:
   ...     writer.write_image(pixels.view(np.uint8))
   Traceback (most recent call last):
   ValueError: Array dtype (uint8) does not match expected dtype (complex64) for PixelType=RE32F_IM32F

SARkit provides :ref:`consistency checkers <consistency_checking>` that can be used to help create self-consistent SAR
data.


Operating on XML Metadata
=========================
The parsed XML element tree is a key component in SARkit as XML is the primary metadata container for many SAR
standards.

For simple operations, `xml.etree.ElementTree` and/or `lxml` are often sufficient:

.. doctest::

   >>> reader.sicd_xmltree.findtext(".//{*}ModeType")
   'SPOTLIGHT'

For complicated metadata, SARkit provides XML helper classes that can be used to transcode between XML and more
convenient Python objects.

.. list-table::

   * - Format
     - XML Helper
   * - ⛔ CRSD [Draft] ⛔
     - :py:class:`sarkit.standards.crsd.xml.XmlHelper`
   * - CPHD
     - :py:class:`sarkit.cphd.XmlHelper`
   * - SICD
     - :py:class:`sarkit.standards.sicd.xml.XmlHelper`
   * - SIDD
     - :py:class:`sarkit.sidd.XmlHelper`

XML Helpers
-----------

XmlHelpers are instantiated with an `lxml.etree.ElementTree` which can then be manipulated using set and load methods.

.. doctest::

   >>> import sarkit.standards.sicd.xml
   >>> xmlhelp = sarkit.standards.sicd.xml.XmlHelper(reader.sicd_xmltree)
   >>> xmlhelp.load(".//{*}ModeType")
   'SPOTLIGHT'

:py:class:`~sarkit.standards.sicd.xml.XmlHelper.load_elem` and :py:class:`~sarkit.standards.sicd.xml.XmlHelper.set_elem`
can be used when you already have an element object:

.. doctest::

   >>> tcoa_poly_elem = reader.sicd_xmltree.find(".//{*}TimeCOAPoly")
   >>> xmlhelp.load_elem(tcoa_poly_elem)
   array([[1.2206226]])

   >>> xmlhelp.set_elem(tcoa_poly_elem, [[1.1, -2.2], [-3.3, 4.4]])
   >>> print(lxml.etree.tostring(tcoa_poly_elem, pretty_print=True, encoding="unicode").strip())
   <TimeCOAPoly xmlns="urn:SICD:1.4.0" order1="1" order2="1">
     <Coef exponent1="0" exponent2="0">1.1</Coef>
     <Coef exponent1="0" exponent2="1">-2.2</Coef>
     <Coef exponent1="1" exponent2="0">-3.3</Coef>
     <Coef exponent1="1" exponent2="1">4.4</Coef>
   </TimeCOAPoly>

:py:class:`~sarkit.standards.sicd.xml.XmlHelper.load` / :py:class:`~sarkit.standards.sicd.xml.XmlHelper.set` are
shortcuts for ``find`` + :py:class:`~sarkit.standards.sicd.xml.XmlHelper.load_elem` /
:py:class:`~sarkit.standards.sicd.xml.XmlHelper.set_elem`:

.. doctest::

   # find + set_elem/load_elem
   >>> elem = reader.sicd_xmltree.find("{*}ImageData/{*}SCPPixel")
   >>> xmlhelp.set_elem(elem, [123, 456])
   >>> xmlhelp.load_elem(elem)
   array([123, 456])

   # equivalent methods using set/load
   >>> xmlhelp.set("{*}ImageData/{*}SCPPixel", [321, 654])
   >>> xmlhelp.load("{*}ImageData/{*}SCPPixel")
   array([321, 654])

.. note:: Similar to writers, XMLHelpers only prevent basic errors. Users are responsible for ensuring metadata is
   accurate and compliant with the standard/schema.


What is transcodable?
---------------------

Every leaf in the supported SAR standards' XML trees has a transcoder, but parent nodes generally only have them for
standard-defined complex types (e.g. XYZ, LL, LLH, POLY, 2D_POLY, etc.).
Select parent nodes also have them when a straightforward mapping is apparent (e.g. polygons).

.. doctest::

   # this leaf has a transcoder
   >>> xmlhelp.load("{*}CollectionInfo/{*}CollectorName")
   'SyntheticCollector'

   # this parent node does not have a transcoder
   >>> xmlhelp.load("{*}CollectionInfo")
   Traceback (most recent call last):
   LookupError: CollectionInfo is not transcodable


.. _consistency_checking:

Consistency Checking
====================

.. warning:: Consistency checkers require the ``verification`` :ref:`extra <installation>`.

SARkit provides checkers that can be used to identify inconsistencies in SAR standards files.

.. list-table::

   * - Format
     - Consistency Checker
   * - ⛔ CRSD [Draft] ⛔
     - :py:class:`~sarkit.verification.crsd_consistency`
   * - CPHD
     - :py:class:`~sarkit.verification.cphd_consistency`
   * - SICD
     - :py:class:`~sarkit.verification.sicd_consistency`
   * - SIDD
     - To be added

Each consistency checker provides a command line interface for checking SAR data/metadata files.
When there are no inconsistencies, no output is produced.

.. code-block:: shell-session

   $ python -m sarkit.verification.sicd_consistency good.sicd
   $

The same command can be used to run a subset of the checks against the XML.

.. code-block:: shell-session

   $ python -m sarkit.verification.sicd_consistency good.sicd.xml
   $

When a file is inconsistent, failed checks are printed.

.. code-block:: shell-session

   $ python -m sarkit.verification.sicd_consistency bad.sicd
   check_image_formation_timeline: Checks that the slow time span for data processed to form
   the image is within collect.
      [Error] Need: 0 <= TStartProc < TEndProc <= CollectDuration

For further details about consistency checker results, increase the output verbosity.
The ``-v`` flag is additive and can be used up to 4 times.

.. code-block::

   -v       # display details in failed checks
   -vv      # display passed asserts in failed checks
   -vvv     # display passed checks
   -vvvv    # display details in skipped checks

For example:

.. code-block:: shell-session

   $ python -m sarkit.verification.sicd_consistency good.sicd -vvv
   check_against_schema: Checks against schema.
      [Pass] Need: XML passes schema
      [Pass] Need: Schema available for checking xml whose root tag = {urn:SICD:1.2.1}SICD
   ...
