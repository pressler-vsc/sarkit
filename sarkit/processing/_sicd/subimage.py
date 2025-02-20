"""
Extract a subimage (chip) from a SICD
"""

import copy

import lxml.etree
import numpy as np
import numpy.typing as npt

import sarkit.sicd as sksicd
import sarkit.wgs84


def sicd_subimage(
    array: npt.NDArray,
    sicd_xmltree: lxml.etree.ElementTree,
    first_row: int,
    first_col: int,
    num_rows: int,
    num_cols: int,
) -> tuple[npt.NDArray, lxml.etree.ElementTree]:
    """Extract a subimage

    Updates the ImageData fields as expected and the GeoData/ImageCorners
    using a straight-line projection approximation to a plane.

    Parameters
    ----------
    array : ndarray
        2D array of complex pixels
    sicd_xmltree : lxml.etree.ElementTree
        SICD XML ElementTree
    first_row : int
        first row to extract, relative to ImageData/FirstRow
    first_col : int
        first column to extract, relative to ImageData/FirstCol
    num_rows : int
        number of rows to extract
    num_cols : int
        number of columns to extract

    Returns
    -------
    array_out : ndarray
        2D array of extracted complex pixels
    sicd_xmltree_out : lxml.etree.ElementTree
        Updated SICD XML ElementTree
    """
    sicd_xmltree_out = copy.deepcopy(sicd_xmltree)
    xml_helper = sksicd.XmlHelper(sicd_xmltree_out)
    first_row_abs = first_row + xml_helper.load("./{*}ImageData/{*}FirstRow")
    first_col_abs = first_col + xml_helper.load("./{*}ImageData/{*}FirstCol")

    assert first_row >= 0
    assert first_col >= 0
    end_row = first_row + num_rows
    end_col = first_col + num_cols
    assert end_row <= array.shape[0]
    assert end_col <= array.shape[1]
    array_out = array[first_row:end_row, first_col:end_col].copy()

    xml_helper.set("./{*}ImageData/{*}FirstRow", first_row_abs)
    xml_helper.set("./{*}ImageData/{*}FirstCol", first_col_abs)
    xml_helper.set("./{*}ImageData/{*}NumRows", num_rows)
    xml_helper.set("./{*}ImageData/{*}NumCols", num_cols)

    scp = xml_helper.load("./{*}GeoData/{*}SCP/{*}ECF")
    scp_llh = xml_helper.load("./{*}GeoData/{*}SCP/{*}LLH")
    urow = xml_helper.load("./{*}Grid/{*}Row/{*}UVectECF")
    ucol = xml_helper.load("./{*}Grid/{*}Col/{*}UVectECF")
    row_ss = xml_helper.load("./{*}Grid/{*}Row/{*}SS")
    col_ss = xml_helper.load("./{*}Grid/{*}Col/{*}SS")
    scp_row = xml_helper.load("./{*}ImageData/{*}SCPPixel/{*}Row")
    scp_col = xml_helper.load("./{*}ImageData/{*}SCPPixel/{*}Col")
    arp_scp_coa = xml_helper.load("./{*}SCPCOA/{*}ARPPos")
    varp_scp_coa = xml_helper.load("./{*}SCPCOA/{*}ARPVel")
    look = {"L": 1, "R": -1}[xml_helper.load("./{*}SCPCOA/{*}SideOfTrack")]

    ugpn = sarkit.wgs84.up(scp_llh)

    spn = look * np.cross(varp_scp_coa, scp - arp_scp_coa)
    uspn = spn / np.linalg.norm(spn)

    sf_proj = np.dot(uspn, ugpn)

    sicp_row = np.array(
        [
            first_row_abs,
            first_row_abs,
            first_row_abs + num_rows - 1,
            first_row_abs + num_rows - 1,
        ]
    )

    sicp_col = np.array(
        [
            first_col_abs,
            first_col_abs + num_cols - 1,
            first_col_abs + num_cols - 1,
            first_col_abs,
        ]
    )

    # The SICD Sub-Image Extraction document dated 2009-06-15 dictates a straight-line projection
    row_coord = (sicp_row - scp_row) * row_ss
    col_coord = (sicp_col - scp_col) * col_ss
    delta_ipp = row_coord[..., np.newaxis] * urow + col_coord[..., np.newaxis] * ucol
    dist_proj = 1 / sf_proj * np.inner(delta_ipp, ugpn)
    gpp = scp + delta_ipp - dist_proj[..., np.newaxis] * uspn
    gpp_llh = sarkit.wgs84.cartesian_to_geodetic(gpp)
    xml_helper.set("./{*}GeoData/{*}ImageCorners", gpp_llh[:, :-1])
    return array_out, sicd_xmltree_out
