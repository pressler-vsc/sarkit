"""
========
CRSD I/O
========

Functions to read and write CRSD files.
"""

import dataclasses
import importlib.resources
import logging
import os

import lxml.etree
import numpy as np
import numpy.typing as npt

import sarkit.standards.cphd.io as cphd_io

SCHEMA_DIR = importlib.resources.files("sarkit.standards.crsd.schemas")
CRSD_SECTION_TERMINATOR = b"\f\n"
DEFINED_HEADER_KEYS = {
    "XML_BLOCK_SIZE",
    "XML_BLOCK_BYTE_OFFSET",
    "SUPPORT_BLOCK_SIZE",
    "SUPPORT_BLOCK_BYTE_OFFSET",
    "PPP_BLOCK_SIZE",
    "PPP_BLOCK_BYTE_OFFSET",
    "PVP_BLOCK_SIZE",
    "PVP_BLOCK_BYTE_OFFSET",
    "SIGNAL_BLOCK_SIZE",
    "SIGNAL_BLOCK_BYTE_OFFSET",
    "CLASSIFICATION",
    "RELEASE_INFO",
}

VERSION_INFO = {
    "http://api.nsgreg.nga.mil/schema/crsd/1.0.0_NEXT": {
        # TBD
        "version": "1.0",
        "date": "2024-12-30T00:00:00Z",
        "schema": SCHEMA_DIR / "NGA.STND.0080-1_1.0_DRAFT_CRSD_DIDD_2024_12_30.xsd",
    },
}


dtype_to_binary_format_string = cphd_io.dtype_to_binary_format_string
binary_format_string_to_dtype = cphd_io.binary_format_string_to_dtype


mask_support_array = cphd_io.mask_support_array


@dataclasses.dataclass(kw_only=True)
class CrsdFileHeaderFields:
    """CRSD header fields which are set per program specific Product Design Document

    Attributes
    ----------
    classification : str
        File classification
    release_info : str
        File release info
    additional_kvps : dict of {str : str}, optional
        Dictionary with additional key-value pairs
    """

    classification: str
    release_info: str
    additional_kvps: dict[str, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        if self.additional_kvps is None:
            self.additional_kvps = {}


@dataclasses.dataclass(kw_only=True)
class CrsdPlan:
    """Class describing the plan for creating a CRSD file

    Attributes
    ----------
    file_header : :py:class:`CrsdFileHeaderFields`
        CRSD File Header fields which can be set
    crsd_xmltree : lxml.etree.ElementTree
        CRSD XML ElementTree

    See Also
    --------
    CrsdReader
    CrsdWriter
    CrsdFileHeaderFields
    """

    file_header: CrsdFileHeaderFields
    crsd_xmltree: lxml.etree.ElementTree


read_file_header = cphd_io.read_file_header


def _get_pxp_dtype(pxp_node):
    """Get PXP dtype.

    Parameters
    ----------
    pxp_elem: lxml.etree.Element
        The root element of the PXP data descriptor in the CRSD XML

    Returns
    -------
    numpy.dtype
    """

    bytes_per_word = 8
    names = []
    formats = []
    offsets = []

    def handle_field(field_node):
        node_name = lxml.etree.QName(field_node).localname
        if node_name in ("AddedPVP", "AddedPPP"):
            names.append(field_node.find("./{*}Name").text)
        else:
            names.append(node_name)

        formats.append(
            binary_format_string_to_dtype(field_node.find("./{*}Format").text)
        )
        offsets.append(int(field_node.find("./{*}Offset").text) * bytes_per_word)

    for pnode in pxp_node:
        handle_field(pnode)

    dtype = np.dtype({"names": names, "formats": formats, "offsets": offsets})
    return dtype


def get_ppp_dtype(crsd_xmltree):
    """Get PPP dtype.

    Parameters
    ----------
    crsd_xmltree : lxml.etree.ElementTree
        CRSD XML ElementTree

    Returns
    -------
    numpy.dtype
    """
    return _get_pxp_dtype(crsd_xmltree.find("./{*}PPP"))


def get_pvp_dtype(crsd_xmltree):
    """Get PVP dtype.

    Parameters
    ----------
    crsd_xmltree : lxml.etree.ElementTree
        CRSD XML ElementTree

    Returns
    -------
    numpy.dtype
    """
    return _get_pxp_dtype(crsd_xmltree.find("./{*}PVP"))


class CrsdReader:
    """Read a CRSD file

    A CrsdReader object can be used as a context manager in a ``with`` statement.
    Attributes, but not methods, can be safely accessed outside of the context manager's context.

    Parameters
    ----------
    file : `file object`
        CRSD file to read

    Examples
    --------
    >>> with crsd_path.open('rb') as file, CrsdReader(file) as reader:
    ...     crsd_xmltree = reader.crsd_xmltree
    ...     signal, pvp = reader.read_channel(<chan_id>)

    Attributes
    ----------
    file_header : :py:class:`CrsdFileHeaderFields`
       CRSD header dataclass
    crsd_xmltree : lxml.etree.ElementTree
        CRSD XML ElementTree
    plan : :py:class:`CrsdPlan`
        A CrsdPlan object suitable for use in a CrsdWriter
    xml_block_size : int
    xml_block_byte_offset : int
    ppp_block_size : int or None
    ppp_block_byte_offset : int or None
    pvp_block_size : int or None
    pvp_block_byte_offset : int or None
    signal_block_size : int or None
    signal_block_byte_offset : int or None
    support_block_size : int
    support_block_byte_offset : int

    See Also
    --------
    CrsdPlan
    CrsdWriter
    """

    def __init__(self, file):
        self._file_object = file

        # skip the version line and read header
        _, self._kvp_list = read_file_header(self._file_object)

        extra_header_keys = set(self._kvp_list.keys()) - DEFINED_HEADER_KEYS
        additional_kvps = {key: self._kvp_list[key] for key in extra_header_keys}

        self.file_header = CrsdFileHeaderFields(
            classification=self._kvp_list["CLASSIFICATION"],
            release_info=self._kvp_list["RELEASE_INFO"],
            additional_kvps=additional_kvps,
        )
        self._file_object.seek(self.xml_block_byte_offset)
        xml_bytes = self._file_object.read(int(self._kvp_list["XML_BLOCK_SIZE"]))
        self.crsd_xmltree = lxml.etree.fromstring(xml_bytes).getroottree()

        self.plan = CrsdPlan(
            crsd_xmltree=self.crsd_xmltree,
            file_header=self.file_header,
        )

    @property
    def xml_block_byte_offset(self) -> int:
        """Offset to the XML block"""
        return int(self._kvp_list["XML_BLOCK_BYTE_OFFSET"])

    @property
    def xml_block_size(self) -> int:
        """Size of the XML block"""
        return int(self._kvp_list["XML_BLOCK_SIZE"])

    @property
    def pvp_block_byte_offset(self) -> int | None:
        """Offset to the PVP block"""
        if (n := self._kvp_list.get("PVP_BLOCK_BYTE_OFFSET")) is not None:
            return int(n)
        return None

    @property
    def pvp_block_size(self) -> int | None:
        """Size of the PVP block"""
        if (n := self._kvp_list.get("PVP_BLOCK_SIZE")) is not None:
            return int(n)
        return None

    @property
    def ppp_block_byte_offset(self) -> int | None:
        """Offset to the PPP block"""
        if (n := self._kvp_list.get("PPP_BLOCK_BYTE_OFFSET")) is not None:
            return int(n)
        return None

    @property
    def ppp_block_size(self) -> int | None:
        """Size of the PPP block"""
        if (n := self._kvp_list.get("PPP_BLOCK_SIZE")) is not None:
            return int(n)
        return None

    @property
    def signal_block_byte_offset(self) -> int | None:
        """Offset to the Signal block"""
        if (n := self._kvp_list.get("SIGNAL_BLOCK_BYTE_OFFSET")) is not None:
            return int(n)
        return None

    @property
    def signal_block_size(self) -> int | None:
        """Size of the Signal block"""
        if (n := self._kvp_list.get("SIGNAL_BLOCK_SIZE")) is not None:
            return int(n)
        return None

    @property
    def support_block_byte_offset(self) -> int:
        """Offset to the Support block"""
        return int(self._kvp_list["SUPPORT_BLOCK_BYTE_OFFSET"])

    @property
    def support_block_size(self) -> int:
        """Size of the Support block"""
        return int(self._kvp_list["SUPPORT_BLOCK_SIZE"])

    def read_signal(self, channel_identifier: str) -> npt.NDArray:
        """Read signal data from a CRSD file

        Parameters
        ----------
        channel_identifier : str
            Channel unique identifier

        Returns
        -------
        ndarray
            2D array of complex samples

        """
        channel_info = self.crsd_xmltree.find(
            f"{{*}}Data/{{*}}Receive/{{*}}Channel[{{*}}Identifier='{channel_identifier}']"
        )
        num_vect = int(channel_info.find("./{*}NumVectors").text)
        num_samp = int(channel_info.find("./{*}NumSamples").text)
        shape = (num_vect, num_samp)

        signal_offset = int(channel_info.find("./{*}SignalArrayByteOffset").text)
        assert self.signal_block_byte_offset is not None  # placate mypy
        self._file_object.seek(signal_offset + self.signal_block_byte_offset)

        signal_dtype = binary_format_string_to_dtype(
            self.crsd_xmltree.find("./{*}Data/{*}Receive/{*}SignalArrayFormat").text
        ).newbyteorder("B")

        return np.fromfile(
            self._file_object, signal_dtype, count=np.prod(shape)
        ).reshape(shape)

    def read_pvps(self, channel_identifier: str) -> npt.NDArray:
        """Read pvp data from a CRSD file

        Parameters
        ----------
        channel_identifier : str
            Channel unique identifier

        Returns
        -------
        ndarray
            CRSD PVP array

        """
        channel_info = self.crsd_xmltree.find(
            f"{{*}}Data/{{*}}Receive/{{*}}Channel[{{*}}Identifier='{channel_identifier}']"
        )
        num_vect = int(channel_info.find("./{*}NumVectors").text)

        pvp_offset = int(channel_info.find("./{*}PVPArrayByteOffset").text)
        assert self.pvp_block_byte_offset is not None  # placate mypy
        self._file_object.seek(pvp_offset + self.pvp_block_byte_offset)

        pvp_dtype = get_pvp_dtype(self.crsd_xmltree).newbyteorder("B")
        return np.fromfile(self._file_object, pvp_dtype, count=num_vect)

    def read_channel(self, channel_identifier: str) -> tuple[npt.NDArray, npt.NDArray]:
        """Read signal and pvp data from a CRSD file channel

        Parameters
        ----------
        channel_identifier : str
            Channel unique identifier

        Returns
        -------
        signal_array : ndarray
            Signal array for channel = channel_identifier
        pvp_array : ndarray
            PVP array for channel = channel_identifier

        """
        return self.read_signal(channel_identifier), self.read_pvps(channel_identifier)

    def read_ppps(self, sequence_identifier: str) -> npt.NDArray:
        """Read ppp data from a CRSD file

        Parameters
        ----------
        sequence_identifier : str
            Transmit sequence unique identifier

        Returns
        -------
        ndarray
            CRSD PPP array

        """
        channel_info = self.crsd_xmltree.find(
            f"{{*}}Data/{{*}}Transmit/{{*}}TxSequence[{{*}}Identifier='{sequence_identifier}']"
        )
        num_pulse = int(channel_info.find("./{*}NumPulses").text)

        ppp_offset = int(channel_info.find("./{*}PPPArrayByteOffset").text)
        assert self.ppp_block_byte_offset is not None  # placate mypy
        self._file_object.seek(ppp_offset + self.ppp_block_byte_offset)

        ppp_dtype = get_ppp_dtype(self.crsd_xmltree).newbyteorder("B")
        return np.fromfile(self._file_object, ppp_dtype, count=num_pulse)

    def _read_support_array(self, sa_identifier):
        elem_format = self.crsd_xmltree.find(
            f"{{*}}SupportArray/*[{{*}}Identifier='{sa_identifier}']/{{*}}ElementFormat"
        )
        dtype = binary_format_string_to_dtype(elem_format.text).newbyteorder("B")

        sa_info = self.crsd_xmltree.find(
            f"{{*}}Data/{{*}}Support/{{*}}SupportArray[{{*}}Identifier='{sa_identifier}']"
        )
        num_rows = int(sa_info.find("./{*}NumRows").text)
        num_cols = int(sa_info.find("./{*}NumCols").text)
        shape = (num_rows, num_cols)

        sa_offset = int(sa_info.find("./{*}ArrayByteOffset").text)
        self._file_object.seek(sa_offset + self.support_block_byte_offset)
        assert dtype.itemsize == int(sa_info.find("./{*}BytesPerElement").text)
        array = np.fromfile(self._file_object, dtype, count=np.prod(shape)).reshape(
            shape
        )
        return array

    def read_support_array(self, sa_identifier, masked=True):
        """Read SupportArray"""
        array = self._read_support_array(sa_identifier)
        if not masked:
            return array
        nodata = self.crsd_xmltree.findtext(
            f"{{*}}SupportArray/*[{{*}}Identifier='{sa_identifier}']/{{*}}NODATA"
        )
        return mask_support_array(array, nodata)

    def done(self):
        "Indicates to the reader that the user is done with it"
        self._file_object = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.done()


class CrsdWriter:
    """Write a CRSD file

    A CrsdWriter object can be used as a context manager in a ``with`` statement.

    Parameters
    ----------
    file : `file object`
        CRSD file to write
    plan : :py:class:`CrsdPlan`
        A CrsdPlan object

    Notes
    -----
    plan should not be modified after creation of a writer

    Examples
    --------
    >>> with output_path.open('wb') as file, CrsdWriter(file, plan) as writer:
    ...     writer.write_signal("1", signal)
    ...     writer.write_pvp("1", pvp)

    See Also
    --------
    CrsdPlan
    CrsdReader
    """

    def __init__(self, file, plan):
        align_to = 64
        self._file_object = file

        self._plan = plan

        xml_block_body = lxml.etree.tostring(plan.crsd_xmltree, encoding="utf-8")

        self._sequence_size_offsets = {}
        if plan.crsd_xmltree.find("./{*}Data/{*}Transmit") is not None:
            ppp_itemsize = int(
                plan.crsd_xmltree.find("./{*}Data/{*}Transmit/{*}NumBytesPPP").text
            )
            for seq_node in plan.crsd_xmltree.findall(
                "./{*}Data/{*}Transmit/{*}TxSequence"
            ):
                sequence_identifier = seq_node.find("./{*}Identifier").text
                sequence_ppp_offset = int(seq_node.find("./{*}PPPArrayByteOffset").text)
                sequence_ppp_size = (
                    int(seq_node.find("./{*}NumPulses").text) * ppp_itemsize
                )
                self._sequence_size_offsets[sequence_identifier] = {
                    "ppp_offset": sequence_ppp_offset,
                    "ppp_size": sequence_ppp_size,
                }

        self._channel_size_offsets = {}
        if plan.crsd_xmltree.find("./{*}Data/{*}Receive") is not None:
            signal_itemsize = binary_format_string_to_dtype(
                plan.crsd_xmltree.find("./{*}Data/{*}Receive/{*}SignalArrayFormat").text
            ).itemsize
            pvp_itemsize = int(
                plan.crsd_xmltree.find("./{*}Data/{*}Receive/{*}NumBytesPVP").text
            )
            for chan_node in plan.crsd_xmltree.findall(
                "./{*}Data/{*}Receive/{*}Channel"
            ):
                channel_identifier = chan_node.find("./{*}Identifier").text
                channel_signal_offset = int(
                    chan_node.find("./{*}SignalArrayByteOffset").text
                )
                channel_signal_size = (
                    int(chan_node.find("./{*}NumVectors").text)
                    * int(chan_node.find("./{*}NumSamples").text)
                    * signal_itemsize
                )

                channel_pvp_offset = int(chan_node.find("./{*}PVPArrayByteOffset").text)
                channel_pvp_size = (
                    int(chan_node.find("./{*}NumVectors").text) * pvp_itemsize
                )

                self._channel_size_offsets[channel_identifier] = {
                    "signal_offset": channel_signal_offset,
                    "signal_size": channel_signal_size,
                    "pvp_offset": channel_pvp_offset,
                    "pvp_size": channel_pvp_size,
                }

        self._sa_size_offsets = {}
        for sa_node in plan.crsd_xmltree.findall(
            "./{*}Data/{*}Support/{*}SupportArray"
        ):
            sa_identifier = sa_node.find("./{*}Identifier").text
            sa_offset = int(sa_node.find("./{*}ArrayByteOffset").text)
            sa_size = (
                int(sa_node.find("./{*}NumRows").text)
                * int(sa_node.find("./{*}NumCols").text)
                * int(sa_node.find("./{*}BytesPerElement").text)
            )

            self._sa_size_offsets[sa_identifier] = {
                "offset": sa_offset,
                "size": sa_size,
            }

        support_block_size = max(
            sa["size"] + sa["offset"] for sa in self._sa_size_offsets.values()
        )

        def _align(val):
            return int(np.ceil(float(val) / align_to) * align_to)

        self._file_header_kvp = {
            "CLASSIFICATION": plan.file_header.classification,
            "RELEASE_INFO": plan.file_header.release_info,
            "XML_BLOCK_SIZE": len(xml_block_body),
            "XML_BLOCK_BYTE_OFFSET": np.iinfo(np.uint64).max,  # placeholder
        }
        if self._sequence_size_offsets:
            ppp_block_size = max(
                seq["ppp_size"] + seq["ppp_offset"]
                for seq in self._sequence_size_offsets.values()
            )
            self._file_header_kvp.update(
                {
                    "PPP_BLOCK_SIZE": ppp_block_size,
                    "PPP_BLOCK_BYTE_OFFSET": np.iinfo(np.uint64).max,  # placeholder
                }
            )
        if self._channel_size_offsets:
            signal_block_size = max(
                chan["signal_size"] + chan["signal_offset"]
                for chan in self._channel_size_offsets.values()
            )
            pvp_block_size = max(
                chan["pvp_size"] + chan["pvp_offset"]
                for chan in self._channel_size_offsets.values()
            )

            self._file_header_kvp.update(
                {
                    "PVP_BLOCK_SIZE": pvp_block_size,
                    "PVP_BLOCK_BYTE_OFFSET": np.iinfo(np.uint64).max,  # placeholder
                    "SIGNAL_BLOCK_SIZE": signal_block_size,
                    "SIGNAL_BLOCK_BYTE_OFFSET": np.iinfo(np.uint64).max,  # placeholder
                }
            )
        self._file_header_kvp["SUPPORT_BLOCK_SIZE"] = support_block_size
        self._file_header_kvp["SUPPORT_BLOCK_BYTE_OFFSET"] = (
            np.iinfo(np.uint64).max,
        )  # placeholder

        self._file_header_kvp.update(plan.file_header.additional_kvps)

        def _serialize_header():
            version = VERSION_INFO[
                lxml.etree.QName(plan.crsd_xmltree.getroot()).namespace
            ]["version"]
            if self._sequence_size_offsets and self._channel_size_offsets:
                file_type = "CRSDsar"
            elif self._channel_size_offsets:
                file_type = "CRSDrcv"
            elif self._sequence_size_offsets:
                file_type = "CRSDtx"
            else:
                raise ValueError("Must have transmit sequences and/or receive channels")
            header_str = f"{file_type}/{version}\n"
            header_str += "".join(
                (f"{key} := {value}\n" for key, value in self._file_header_kvp.items())
            )
            return header_str.encode() + CRSD_SECTION_TERMINATOR

        next_offset = _align(len(_serialize_header()))

        self._file_header_kvp["XML_BLOCK_BYTE_OFFSET"] = next_offset
        next_offset = _align(
            next_offset
            + self._file_header_kvp["XML_BLOCK_SIZE"]
            + len(CRSD_SECTION_TERMINATOR)
        )

        self._file_header_kvp["SUPPORT_BLOCK_BYTE_OFFSET"] = next_offset
        next_offset = _align(next_offset + self._file_header_kvp["SUPPORT_BLOCK_SIZE"])

        if self._sequence_size_offsets:
            self._file_header_kvp["PPP_BLOCK_BYTE_OFFSET"] = next_offset
            next_offset = _align(next_offset + self._file_header_kvp["PPP_BLOCK_SIZE"])

        if self._channel_size_offsets:
            self._file_header_kvp["PVP_BLOCK_BYTE_OFFSET"] = next_offset
            next_offset = _align(next_offset + self._file_header_kvp["PVP_BLOCK_SIZE"])
            self._file_header_kvp["SIGNAL_BLOCK_BYTE_OFFSET"] = next_offset
            next_offset = _align(
                next_offset + self._file_header_kvp["SIGNAL_BLOCK_SIZE"]
            )

        self._file_object.seek(0)
        self._file_object.write(_serialize_header())
        self._file_object.seek(self._file_header_kvp["XML_BLOCK_BYTE_OFFSET"])
        self._file_object.write(xml_block_body + CRSD_SECTION_TERMINATOR)

        self._signal_arrays_written = set()
        self._pvp_arrays_written = set()
        self._ppp_arrays_written = set()
        self._support_arrays_written = set()

    def write_signal(self, channel_identifier: str, signal_array: npt.NDArray):
        """Write signal data to a CRSD file

        Parameters
        ----------
        channel_identifier : str
            Channel unique identifier
        signal_array : ndarray
            2D array of complex samples

        """
        assert (
            signal_array.nbytes
            == self._channel_size_offsets[channel_identifier]["signal_size"]
        )

        self._signal_arrays_written.add(channel_identifier)
        self._file_object.seek(self._file_header_kvp["SIGNAL_BLOCK_BYTE_OFFSET"])
        self._file_object.seek(
            self._channel_size_offsets[channel_identifier]["signal_offset"], os.SEEK_CUR
        )
        output_dtype = signal_array.dtype.newbyteorder(">")
        signal_array.astype(output_dtype, copy=False).tofile(self._file_object)

        # TODO Add support for partial CRSD writing
        return

    def write_pvp(self, channel_identifier: str, pvp_array: npt.NDArray):
        """Write pvp data to a CRSD file

        Parameters
        ----------
        channel_identifier : str
            Channel unique identifier
        pvp_array : ndarray
            Array of PVPs

        """
        assert (
            pvp_array.nbytes
            == self._channel_size_offsets[channel_identifier]["pvp_size"]
        )

        self._pvp_arrays_written.add(channel_identifier)
        self._file_object.seek(self._file_header_kvp["PVP_BLOCK_BYTE_OFFSET"])
        self._file_object.seek(
            self._channel_size_offsets[channel_identifier]["pvp_offset"], os.SEEK_CUR
        )
        output_dtype = pvp_array.dtype.newbyteorder(">")
        pvp_array.astype(output_dtype, copy=False).tofile(self._file_object)
        return

    def write_ppp(self, sequence_identifier: str, ppp_array: npt.NDArray):
        """Write ppp data to a CRSD file

        Parameters
        ----------
        sequence_identifier : str
            Sequence unique identifier
        ppp_array : ndarray
            Array of PPPs

        """
        assert (
            ppp_array.nbytes
            == self._sequence_size_offsets[sequence_identifier]["ppp_size"]
        )

        self._ppp_arrays_written.add(sequence_identifier)
        self._file_object.seek(self._file_header_kvp["PPP_BLOCK_BYTE_OFFSET"])
        self._file_object.seek(
            self._sequence_size_offsets[sequence_identifier]["ppp_offset"], os.SEEK_CUR
        )
        output_dtype = ppp_array.dtype.newbyteorder(">")
        ppp_array.astype(output_dtype, copy=False).tofile(self._file_object)
        return

    def write_support_array(
        self, support_array_identifier: str, support_array: npt.NDArray
    ):
        """Write support array data to a CRSD file

        Parameters
        ----------
        support_array_identifier : str
            Unique support array identifier
        support_array : ndarray
            Array of support data

        """
        assert (
            support_array.nbytes
            == self._sa_size_offsets[support_array_identifier]["size"]
        )

        self._support_arrays_written.add(support_array_identifier)
        self._file_object.seek(self._file_header_kvp["SUPPORT_BLOCK_BYTE_OFFSET"])
        self._file_object.seek(
            self._sa_size_offsets[support_array_identifier]["offset"], os.SEEK_CUR
        )
        output_dtype = support_array.dtype.newbyteorder(">")
        support_array.astype(output_dtype, copy=False).tofile(self._file_object)

    def done(self):
        """Warn about unwritten arrays declared in the XML"""
        channel_names = set(
            node.text
            for node in self._plan.crsd_xmltree.findall(
                "./{*}Data/{*}Receive/{*}Channel/{*}Identifier"
            )
        )
        missing_signal_channels = channel_names - self._signal_arrays_written
        if missing_signal_channels:
            logging.warning(
                f"Not all Signal Arrays written.  Missing {missing_signal_channels}"
            )

        missing_pvp_channels = channel_names - self._pvp_arrays_written
        if missing_pvp_channels:
            logging.warning(
                f"Not all PVP Arrays written.  Missing {missing_pvp_channels}"
            )

        sequence_names = set(
            node.text
            for node in self._plan.crsd_xmltree.findall(
                "./{*}Data/{*}Transmit/{*}TxSequence/{*}Identifier"
            )
        )
        missing_ppp_sequences = sequence_names - self._ppp_arrays_written
        if missing_ppp_sequences:
            logging.warning(
                f"Not all PPP Arrays written.  Missing {missing_ppp_sequences}"
            )

        sa_names = set(
            node.text
            for node in self._plan.crsd_xmltree.findall(
                "./{*}Data/{*}SupportArray/{*}Identifier"
            )
        )
        missing_sa = sa_names - self._support_arrays_written
        if missing_sa:
            logging.warning(f"Not all Support Arrays written.  Missing {missing_sa}")

        self._file_object = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.done()
