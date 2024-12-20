.. _user_guide:

=================
SARkit User Guide
=================

:Release: |version|
:Date: |today|

SARkit contains readers and writers for SAR standards files and functions for operating on them.
This is an overview of basic SARkit functionality. For details, see the :doc:`reference/index`.

Reading and writing files
=========================
SARkit provides reader/writer classes that are intended to be used as context managers and plan classes that are used to
describe file contents and metadata prior to writing.

======   =================================================     ===============================================    =================================================
Format   Reader                                                Plan                                               Writer
======   =================================================     ===============================================    =================================================
CPHD     :py:class:`~sarkit.standards.cphd.CphdReader`         :py:class:`~sarkit.standards.cphd.CphdPlan`        :py:class:`~sarkit.standards.cphd.CphdWriter`
SICD     :py:class:`~sarkit.standards.sicd.SicdNitfReader`     :py:class:`~sarkit.standards.sicd.SicdNitfPlan`    :py:class:`~sarkit.standards.sicd.SicdNitfWriter`
SIDD     :py:class:`~sarkit.standards.sidd.SiddNitfReader`     :py:class:`~sarkit.standards.sidd.SiddNitfPlan`    :py:class:`~sarkit.standards.sidd.SiddNitfWriter`
======   =================================================     ===============================================    =================================================


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

   >>> with open(example_sicd, "rb") as f:
   ...   with sarkit_sicd.SicdNitfReader(f) as reader:
   ...      pixels = reader.read_image()
   ...      pixels.shape
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
   ...   sicd_xmltree=example_sicd_xmltree,
   ...   header_fields={"ostaid": "my location", "security": {"clas": "U"}},
   ...   is_fields={"isorce": "my sensor", "security": {"clas": "U"}},
   ...   des_fields={"security": {"clas": "U"}},
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
   >>> with written_sicd.open("wb") as f:
   ...   with sarkit_sicd.SicdNitfWriter(f, plan_b) as writer:
   ...      writer.write_image(pixels)

   >>> with written_sicd.open("rb") as f:
   ...   f.read(9).decode()
   'NITF02.10'

SARkit sanity checks some aspects on write but it is up to the user to ensure consistency of the plan and data:

.. doctest::

   >>> bad_sicd = tmppath / "bad.sicd"
   >>> with bad_sicd.open("wb") as f:
   ...   with sarkit_sicd.SicdNitfWriter(f, plan_b) as writer:
   ...      writer.write_image(pixels.view(np.uint8))
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

======   ===============================================
Format   XML Helper
======   ===============================================
CPHD     :py:class:`sarkit.standards.cphd.xml.XmlHelper`
SICD     :py:class:`sarkit.standards.sicd.xml.XmlHelper`
SIDD     :py:class:`sarkit.standards.sidd.xml.XmlHelper`
======   ===============================================


XML Helpers
-----------

XMLHelpers are instantiated with an `lxml.etree.ElementTree` which can then be manipulated using set and load methods.

.. doctest::

   >>> import sarkit.standards.sicd.xml
   >>> xmlhelp = sarkit.standards.sicd.xml.XmlHelper(reader.sicd_xmltree)
   >>> xmlhelp.load(".//{*}ModeType")
   'SPOTLIGHT'

:py:class:`~sarkit.standards.xml.XmlHelper.load_elem` and :py:class:`~sarkit.standards.xml.XmlHelper.set_elem` can be
used when you already have an element object:

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

:py:class:`~sarkit.standards.xml.XmlHelper.load` / :py:class:`~sarkit.standards.xml.XmlHelper.set` are shortcuts for
``find`` + :py:class:`~sarkit.standards.xml.XmlHelper.load_elem` / :py:class:`~sarkit.standards.xml.XmlHelper.set_elem`:

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
   sarkit.standards.xml.NotTranscodableError: CollectionInfo is not transcodable


.. _consistency_checking:

Consistency Checking
====================

TODO
