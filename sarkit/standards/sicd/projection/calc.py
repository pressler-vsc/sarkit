"""Calculations from SICD Volume 3 Image Projections Description Document"""

import numpy as np
import numpy.polynomial.polynomial as npp
import numpy.typing as npt

import sarkit.constants
import sarkit.standards.geocoords

from . import params


def _xyzpolyval(x, c):
    """Similar to polyval but moves xyz to last dim."""
    assert c.ndim == 2
    assert c.shape[1] == 3
    return np.moveaxis(npp.polyval(x, c), 0, -1)


def image_grid_to_image_plane_point(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
) -> npt.NDArray:
    """Convert image pixel grid locations to corresponding image plane positions.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    image_grid_locations : (..., 2) array_like
        N-D array of image coordinates with xrow/ycol in meters in the last dimension.

    Returns
    -------
    (..., 3) ndarray
        Array of image plane points with ECEF (WGS 84 cartesian) X, Y, Z components in meters
        in the last dimension.

    """
    image_grid_locations = np.asarray(image_grid_locations)
    xrow = image_grid_locations[..., 0]
    ycol = image_grid_locations[..., 1]
    # Compute displacement from SCP to image plane points
    delta_ip_pts = (
        xrow[..., np.newaxis] * proj_metadata.uRow
        + ycol[..., np.newaxis] * proj_metadata.uCol
    )

    # Compute image plane point positions
    return proj_metadata.SCP + delta_ip_pts


def image_plane_point_to_image_grid(
    proj_metadata: params.MetadataParams,
    image_plane_points: npt.ArrayLike,
) -> npt.NDArray:
    """Convert image plane positions to corresponding image pixel grid locations.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    image_plane_points : (..., 3) array_like
        Array of image plane points with ECEF (WGS 84 cartesian) X, Y, Z components in meters
        in the last dimension.

    Returns
    -------
    (..., 2) ndarray
        Array of image coordinates with xrow/ycol in meters in the last dimension.

    """
    # Compute cosine and sine of angle between uRow and uCol and 2x2 matrix.
    cos_theta_col = np.dot(proj_metadata.uRow, proj_metadata.uCol)
    sin_theta_col = np.sqrt(1 - cos_theta_col**2)
    m_il_ippt = (sin_theta_col ** (-2)) * np.array(
        [[1.0, -cos_theta_col], [-cos_theta_col, 1.0]]
    )

    # Compute displacement vector from SCP to image plane points. Compute image grid locations.
    delta_ip_pt = np.asarray(image_plane_points) - proj_metadata.SCP
    il = (
        m_il_ippt
        @ np.stack(
            [
                (delta_ip_pt * proj_metadata.uRow).sum(axis=-1),
                (delta_ip_pt * proj_metadata.uCol).sum(axis=-1),
            ],
            axis=-1,
        )[..., np.newaxis]
    )
    return il[..., 0]  # remove residual dimension from matrix multiply


def compute_coa_time(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
) -> npt.NDArray:
    """Compute Center of Aperture times for specified image grid locations.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    image_grid_locations : (..., 2) array_like
        N-D array of image coordinates with xrow/ycol in meters in the last dimension.

    Returns
    -------
    ndarray
        Array of shape ``image_grid_locations.shape[:-1]`` containing center of aperture
        times in seconds relative to collect start.

    """
    tgts = np.asarray(image_grid_locations)
    xrow = tgts[..., 0]
    ycol = tgts[..., 1]
    return npp.polyval2d(xrow, ycol, proj_metadata.cT_COA)


def compute_coa_pos_vel(
    proj_metadata: params.MetadataParams,
    t_coa: npt.ArrayLike,
) -> params.CoaPosVels:
    """Compute Center of Aperture positions and velocities at specified COA times.

    The parameters that specify the positions and velocities are dependent on
    ``proj_metadata.Collect_Type``:

    MONOSTATIC
        ARP_COA, VARP_COA

    BISTATIC
        GRP_COA, tx_COA, tr_COA, Xmt_COA, VXmt_COA, Rcv_COA, VRcv_COA

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    t_coa : array_like
        Center of aperture times in seconds relative to collect start.

    Returns
    -------
    CoaPosVels
        Ensemble of COA sensor positions and velocities with applicable parameters set.

    """
    t_coa = np.asarray(t_coa)
    if proj_metadata.is_monostatic():
        return params.CoaPosVels(
            ARP_COA=_xyzpolyval(t_coa, proj_metadata.ARP_Poly),
            VARP_COA=_xyzpolyval(t_coa, npp.polyder(proj_metadata.ARP_Poly)),
        )

    # Bistatic Image: COA APC Positions & Velocities
    # Compute GRP position at time t=tcoa
    grp_coa = _xyzpolyval(t_coa, proj_metadata.GRP_Poly)

    # Compute transmit time
    assert proj_metadata.Xmt_Poly is not None
    x0 = _xyzpolyval(t_coa, proj_metadata.Xmt_Poly)
    r_x0 = np.linalg.norm(x0 - grp_coa)
    tx_coa = t_coa - r_x0 / sarkit.constants.speed_of_light

    # Compute transmit APC position and velocity
    xmt_coa = _xyzpolyval(tx_coa, proj_metadata.Xmt_Poly)
    vxmt_coa = _xyzpolyval(tx_coa, npp.polyder(proj_metadata.Xmt_Poly))

    # Compute receive time
    r0 = _xyzpolyval(t_coa, proj_metadata.Rcv_Poly)
    r_r0 = np.linalg.norm(r0 - grp_coa)
    tr_coa = t_coa + r_r0 / sarkit.constants.speed_of_light

    # Compute receive APC position and velocity
    assert proj_metadata.Rcv_Poly is not None
    rcv_coa = _xyzpolyval(tr_coa, proj_metadata.Rcv_Poly)
    vrcv_coa = _xyzpolyval(tr_coa, npp.polyder(proj_metadata.Rcv_Poly))

    return params.CoaPosVels(
        GRP_COA=grp_coa,
        tx_COA=tx_coa,
        tr_COA=tr_coa,
        Xmt_COA=xmt_coa,
        VXmt_COA=vxmt_coa,
        Rcv_COA=rcv_coa,
        VRcv_COA=vrcv_coa,
    )


def compute_scp_coa_r_rdot(proj_metadata: params.MetadataParams) -> tuple[float, float]:
    """Compute COA range and range-rate for the Scene Center Point.

    The SCP R/Rdot projection contour is dependent upon the Collect Type.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.

    Returns
    -------
    r, rdot : float
        Range and range rate relative to the COA positions and velocities.
        For a monostatic image, ``r`` and ``rdot`` are relative to the ARP.
        For a bistatic image, ``r`` and ``rdot`` are averages relative to the COA APCs.

    """
    if proj_metadata.is_monostatic():
        r_scp_coa = np.linalg.norm(proj_metadata.ARP_SCP_COA - proj_metadata.SCP)
        u_pt_scp_coa = (proj_metadata.ARP_SCP_COA - proj_metadata.SCP) / r_scp_coa
        rdot_scp_coa = np.dot(proj_metadata.VARP_SCP_COA, u_pt_scp_coa)
        return float(r_scp_coa), float(rdot_scp_coa)
    bistatic_results = _scp_r_rdot_projection_contour_bistatic(proj_metadata)
    return bistatic_results["r_avg_scp_coa"], bistatic_results["rdot_avg_scp_coa"]


def _scp_r_rdot_projection_contour_bistatic(proj_metadata):
    """SCP R/Rdot Projection Contour calculations for Collect Type = Bistatic

    Private method for re-use.
    """
    # Bistatic
    r_xmt_scp_coa = np.linalg.norm(proj_metadata.Xmt_SCP_COA - proj_metadata.SCP)
    u_xmt_scp_coa = (proj_metadata.Xmt_SCP_COA - proj_metadata.SCP) / r_xmt_scp_coa
    rdot_xmt_scp_coa = np.dot(proj_metadata.VXmt_SCP_COA, u_xmt_scp_coa)
    u_xmtdot_scp_coa = (
        proj_metadata.VXmt_SCP_COA - rdot_xmt_scp_coa * u_xmt_scp_coa
    ) / r_xmt_scp_coa

    r_rcv_scp_coa = np.linalg.norm(proj_metadata.Rcv_SCP_COA - proj_metadata.SCP)
    u_rcv_scp_coa = (proj_metadata.Rcv_SCP_COA - proj_metadata.SCP) / r_rcv_scp_coa
    rdot_rcv_scp_coa = np.dot(proj_metadata.VRcv_SCP_COA, u_rcv_scp_coa)
    u_rcvdot_scp_coa = (
        proj_metadata.VRcv_SCP_COA - rdot_rcv_scp_coa * u_rcv_scp_coa
    ) / r_rcv_scp_coa

    return {
        "r_avg_scp_coa": float((r_xmt_scp_coa + r_rcv_scp_coa) / 2.0),
        "rdot_avg_scp_coa": float((rdot_xmt_scp_coa + rdot_rcv_scp_coa) / 2.0),
        "bp_scp_coa": (u_xmt_scp_coa + u_rcv_scp_coa) / 2.0,
        "bpdot_scp_coa": (u_xmtdot_scp_coa + u_rcvdot_scp_coa) / 2.0,
    }


def compute_scp_coa_slant_plane_normal(
    proj_metadata: params.MetadataParams,
) -> npt.NDArray:
    """Compute the slant plane unit normal for the Scene Center Point at its COA.

    The method for computing the SCP COA slant plane unit normal is dependent upon the
    collect type.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.

    Returns
    -------
    (3,) ndarray
        SCP COA slant plane unit normal with ECEF (WGS 84 cartesian) X, Y, Z components in meters.

    """
    look = {"L": +1, "R": -1}[proj_metadata.SideOfTrack]
    if proj_metadata.is_monostatic():
        spn_scp_coa = look * np.cross(
            (proj_metadata.ARP_SCP_COA - proj_metadata.SCP), proj_metadata.VARP_SCP_COA
        )
    else:
        bistatic_results = _scp_r_rdot_projection_contour_bistatic(proj_metadata)
        spn_scp_coa = look * np.cross(
            bistatic_results["bp_scp_coa"], bistatic_results["bpdot_scp_coa"]
        )
    return spn_scp_coa / np.linalg.norm(spn_scp_coa)


def compute_coa_r_rdot(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
    t_coa: npt.ArrayLike,
    coa_pos_vels: params.CoaPosVels,
) -> tuple[npt.NDArray, npt.NDArray]:
    """Compute COA range and range-rate contours given other projection set components.

    COA R/Rdot computation is dependent upon Collect Type, Grid Type & IFA used.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    image_grid_locations : (..., 2) array_like
        N-D array of image coordinates with xrow/ycol in meters in the last dimension.
    t_coa : array_like
        Center of aperture times in seconds relative to collect start.
    coa_pos_vels : CoaPosVels
        Ensemble of COA sensor positions and velocities

    Returns
    -------
    r, rdot : (..., 1) ndarray
        N-D array containing the ranges and range rates relative to the COA positions
        and velocities.
        For a monostatic image, ``r`` and ``rdot`` are relative to the ARP.
        For a bistatic image, ``r`` and ``rdot`` are averages relative to the COA APCs.

    """
    r_rdot_func = None
    if proj_metadata.Grid_Type == "RGAZIM":
        if proj_metadata.IFA == "PFA":
            r_rdot_func = r_rdot_from_rgazim_pfa
        if proj_metadata.IFA == "RGAZCOMP":
            r_rdot_func = r_rdot_from_rgazim_rgazcomp
    else:
        r_rdot_func = {
            "RGZERO": r_rdot_from_rgzero,
            "XRGYCR": r_rdot_from_xrgycr,
            "XCTYAT": r_rdot_from_xctyat,
            "PLANE": r_rdot_from_plane,
        }.get(proj_metadata.Grid_Type)
    if not r_rdot_func:
        raise ValueError("Insufficient metadata to perform projection")

    return r_rdot_func(proj_metadata, image_grid_locations, t_coa, coa_pos_vels)


def r_rdot_from_rgazim_pfa(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
    t_coa: npt.ArrayLike,
    coa_pos_vels: params.CoaPosVels,
) -> tuple[npt.NDArray, npt.NDArray]:
    """Image Grid To R/Rdot: Grid_Type = RGAZIM & IFA = PFA."""

    tgts = np.asarray(image_grid_locations)
    rg_tgts = tgts[..., 0]
    az_tgts = tgts[..., 1]
    t_coa = np.asarray(t_coa)

    if proj_metadata.is_monostatic():
        r_scp_vector = coa_pos_vels.ARP_COA - proj_metadata.SCP
        r_scp = np.linalg.norm(r_scp_vector, axis=-1, keepdims=True)
        rdot_scp = (coa_pos_vels.VARP_COA * r_scp_vector).sum(-1, keepdims=True) / r_scp
    else:
        pt_r_rdot_params = compute_pt_r_rdot_parameters(
            proj_metadata, coa_pos_vels, proj_metadata.SCP
        )
        r_scp = pt_r_rdot_params.R_Avg_PT
        rdot_scp = pt_r_rdot_params.Rdot_Avg_PT

    # Compute polar angle and its derivative with respect to time
    assert proj_metadata.cPA is not None
    theta = npp.polyval(t_coa, proj_metadata.cPA)
    dtheta_dt = npp.polyval(t_coa, npp.polyder(proj_metadata.cPA))

    # Compute polar aperture scale factor and its derivative with respect to polar angle
    assert proj_metadata.cKSF is not None
    ksf = npp.polyval(theta, proj_metadata.cKSF)
    dksf_dtheta = npp.polyval(theta, npp.polyder(proj_metadata.cKSF))

    # Compute spatial frequency phase slopes
    dphi_dka = rg_tgts * np.cos(theta) + az_tgts * np.sin(theta)
    dphi_dkc = -rg_tgts * np.sin(theta) + az_tgts * np.cos(theta)

    # Compute range relative to the SCP at COA
    delta_r = ksf * dphi_dka

    # Compute rdot relative to SCP at COA
    delta_rdot = (dksf_dtheta * dphi_dka + ksf * dphi_dkc) * dtheta_dt

    # Compute the range and range rate relative to the COA positions and velocities.
    r = r_scp + delta_r[..., np.newaxis]
    rdot = rdot_scp + delta_rdot[..., np.newaxis]
    return r, rdot


def r_rdot_from_rgazim_rgazcomp(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
    t_coa: npt.ArrayLike,
    coa_pos_vels: params.CoaPosVels,
) -> tuple[npt.NDArray, npt.NDArray]:
    """Image Grid To R/Rdot: Grid_Type = RGAZIM & IFA = RGAZCOMP."""

    assert proj_metadata.is_monostatic()
    assert coa_pos_vels.VARP_COA is not None

    tgts = np.asarray(image_grid_locations)
    rg_tgts = tgts[..., 0]
    az_tgts = tgts[..., 1]

    # Compute the range and range rate to the SCP at COA
    r_scp_vector = coa_pos_vels.ARP_COA - proj_metadata.SCP
    r_scp = np.linalg.norm(r_scp_vector, axis=-1, keepdims=True)
    rdot_scp = (coa_pos_vels.VARP_COA * r_scp_vector).sum(-1, keepdims=True) / r_scp

    # Compute the increment in cosine of the DCA at COA of the target and the increment in range rate
    delta_cos_dca = proj_metadata.AzSF * az_tgts
    delta_rdot = (
        -np.linalg.norm(coa_pos_vels.VARP_COA, axis=-1, keepdims=True) * delta_cos_dca
    )

    # Compute the range and range rate to the target at COA
    r_tgt_coa = r_scp + rg_tgts
    rdot_tgt_coa = rdot_scp + delta_rdot[..., np.newaxis]
    return r_tgt_coa, rdot_tgt_coa


def r_rdot_from_rgzero(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
    t_coa: npt.ArrayLike,
    coa_pos_vels: params.CoaPosVels,
) -> tuple[npt.NDArray, npt.NDArray]:
    """Image Grid To R/Rdot: Grid_Type = RGZERO."""

    assert proj_metadata.is_monostatic()

    tgts = np.asarray(image_grid_locations)
    rg_tgts = tgts[..., 0]
    az_tgts = tgts[..., 1]

    # Compute the range at closest approach and the time of closest approach for the image grid location
    assert proj_metadata.cT_CA is not None
    r_ca = proj_metadata.R_CA_SCP + rg_tgts
    t_ca = npp.polyval(az_tgts, proj_metadata.cT_CA)

    # Compute the ARP velocity at t_ca and compute the magnitude of the vector
    varp_ca = _xyzpolyval(t_ca, npp.polyder(proj_metadata.ARP_Poly))
    varp_ca_mag = np.linalg.norm(varp_ca, axis=-1, keepdims=True)

    # Compute the Doppler Rate Scale Factor for image grid (rg_tgts, az_tgts)
    assert proj_metadata.cDRSF is not None
    drsf = npp.polyval2d(rg_tgts, az_tgts, proj_metadata.cDRSF)

    # Compute the time difference between the COA time and the CA time
    delta_t_coa = t_coa - t_ca

    # Compute the range and range rate relative to the ARP at COA
    r_tgt_coa = np.sqrt(r_ca**2 + drsf * varp_ca_mag**2 * delta_t_coa**2)
    rdot_tgt_coa = drsf / r_tgt_coa * varp_ca_mag**2 * delta_t_coa
    return r_tgt_coa, rdot_tgt_coa


def r_rdot_from_xrgycr(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
    t_coa: npt.ArrayLike,
    coa_pos_vels: params.CoaPosVels,
) -> tuple[npt.NDArray, npt.NDArray]:
    """Image Grid To R/Rdot: Grid_Type = XRGYCR.

    XRGYCR is a special case of a uniformly sampled image plane.
    """
    return r_rdot_from_plane(proj_metadata, image_grid_locations, t_coa, coa_pos_vels)


def r_rdot_from_xctyat(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
    t_coa: npt.ArrayLike,
    coa_pos_vels: params.CoaPosVels,
) -> tuple[npt.NDArray, npt.NDArray]:
    """Image Grid To R/Rdot: Grid_Type = XCTYAT.

    XCTYAT is a special case of a uniformly sampled image plane.
    """
    return r_rdot_from_plane(proj_metadata, image_grid_locations, t_coa, coa_pos_vels)


def r_rdot_from_plane(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
    t_coa: npt.ArrayLike,
    coa_pos_vels: params.CoaPosVels,
) -> tuple[npt.NDArray, npt.NDArray]:
    """Image Grid To R/Rdot: Grid_Type = PLANE."""

    tgts = np.asarray(image_grid_locations)
    x_tgt = tgts[..., 0]
    y_tgt = tgts[..., 1]

    # Compute the image plane point for image grid location (xrowTGT, ycolTGT), IP_TGT
    ip_tgt = (
        proj_metadata.SCP + (x_tgt * proj_metadata.uRow) + (y_tgt * proj_metadata.uCol)
    )

    # Compute the range and range rate to the image plane point IP_TGT relative to the COA positions and velocities
    if proj_metadata.is_monostatic():
        r_tgt_coa = np.linalg.norm(
            coa_pos_vels.ARP_COA - ip_tgt, axis=-1, keepdims=True
        )
        u_pt = (coa_pos_vels.ARP_COA - ip_tgt) / r_tgt_coa
        rdot_tgt_coa = (coa_pos_vels.VARP_COA * u_pt).sum(-1, keepdims=True)

        return r_tgt_coa, rdot_tgt_coa
    else:
        pt_r_rdot_params = compute_pt_r_rdot_parameters(
            proj_metadata, coa_pos_vels, ip_tgt
        )

        return pt_r_rdot_params.R_Avg_PT, pt_r_rdot_params.Rdot_Avg_PT


def compute_projection_sets(
    proj_metadata: params.MetadataParams,
    image_grid_locations: npt.ArrayLike,
) -> params.ProjectionSets:
    """Compute Center of Aperture projection sets at specified image grid locations.

    For a selected image grid location, the COA projection set contains the parameters
    needed for computing precise image-to-scene projection. The parameters contained in
    the COA projection set are dependent upon the ``proj_metadata.Collect_Type``.

    MONOSTATIC
        t_COA, ARP_COA, VARP_COA, R_COA, Rdot_COA

    BISTATIC
        t_COA, tx_COA, tr_COA, Xmt_COA, VXmt_COA, Rcv_COA, VRcv_COA, R_Avg_COA, Rdot_Avg_COA

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    image_grid_locations : (..., 2) array_like
        N-D array of image coordinates with xrow/ycol in meters in the last dimension.

    Returns
    -------
    ProjectionSets
        Ensemble of Center of Aperture projection sets.

    """
    t_coa = compute_coa_time(proj_metadata, image_grid_locations)
    coa_pos_vels = compute_coa_pos_vel(proj_metadata, t_coa)
    r, rdot = compute_coa_r_rdot(
        proj_metadata, image_grid_locations, t_coa, coa_pos_vels
    )
    if proj_metadata.is_monostatic():
        return params.ProjectionSets(
            t_COA=t_coa,
            ARP_COA=coa_pos_vels.ARP_COA,
            VARP_COA=coa_pos_vels.VARP_COA,
            R_COA=r,
            Rdot_COA=rdot,
        )
    return params.ProjectionSets(
        t_COA=t_coa,
        tx_COA=coa_pos_vels.tx_COA,
        tr_COA=coa_pos_vels.tr_COA,
        Xmt_COA=coa_pos_vels.Xmt_COA,
        VXmt_COA=coa_pos_vels.VXmt_COA,
        Rcv_COA=coa_pos_vels.Rcv_COA,
        VRcv_COA=coa_pos_vels.VRcv_COA,
        R_Avg_COA=r,
        Rdot_Avg_COA=rdot,
    )


def r_rdot_to_ground_plane_mono(
    proj_metadata: params.MetadataParams,
    projection_sets: params.ProjectionSets,
    gref: npt.ArrayLike,
    ugpn: npt.ArrayLike,
) -> npt.NDArray:
    """Project along contours of constant range and range rate to an arbitrary plane.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    projection_sets : ProjectionSets
        Ensemble of Center of Aperture projection sets to project.
    gref : (3,) array_like
        Ground plane reference point with ECEF (WGS 84 cartesian) X, Y, Z components in meters.
    ugpn : (3,) array_like
        Unit normal vector to ground plane with ECEF (WGS 84 cartesian) X, Y, Z components in
        meters.

    Returns
    -------
    (..., 3) ndarray
        Array of ground plane points with ECEF (WGS 84 cartesian) X, Y, Z components in meters
        in the last dimension. NaNs are returned where no solution is found.

    """

    assert projection_sets.ARP_COA is not None
    assert projection_sets.VARP_COA is not None
    assert projection_sets.R_COA is not None
    assert projection_sets.Rdot_COA is not None

    # Assign unit vector in +Z direction
    gref = np.asarray(gref)
    uz = np.asarray(ugpn)

    # Compute ARP distance from the plane and ARP ground plane nadir (AGPN)
    arpz = ((projection_sets.ARP_COA - gref) * uz).sum(axis=-1, keepdims=True)
    arpz[np.abs(arpz) > projection_sets.R_COA] = np.nan  # No Solution
    agpn = projection_sets.ARP_COA - arpz * uz

    # Compute ground plane distance from ARP nadir to circle of constant range and sine/cosine graze
    g = np.sqrt(projection_sets.R_COA**2 - arpz**2)
    cos_graz = g / projection_sets.R_COA
    sin_graz = arpz / projection_sets.R_COA

    # Compute velocity components in x and y
    vz = (projection_sets.VARP_COA * uz).sum(axis=-1, keepdims=True)
    vx = np.sqrt((projection_sets.VARP_COA**2).sum(axis=-1, keepdims=True) - vz**2)
    vx[vx == 0] = np.nan  # No Solution

    # Orient +X direction in ground plane such that Vx > 0. Compute uX and uY
    ux = (projection_sets.VARP_COA - vz * uz) / vx
    uy = np.cross(uz, ux, axis=-1)

    # Compute the cosine of azimuth angle to ground plane points
    cos_az = (-projection_sets.Rdot_COA + vz * sin_graz) / (vx * cos_graz)
    cos_az[(cos_az < -1.0) | (cos_az > 1.0)] = np.nan  # No Solution

    # Compute the sine of the azimuth angle
    look = {"L": +1, "R": -1}[proj_metadata.SideOfTrack]
    sin_az = look * np.sqrt(1 - cos_az**2)

    # Compute the ground plane points
    return agpn + g * cos_az * ux + g * sin_az * uy


def r_rdot_to_ground_plane_bi(
    proj_metadata: params.MetadataParams,
    projection_sets: params.ProjectionSets,
    gref: npt.ArrayLike,
    ugpn: npt.ArrayLike,
    *,
    delta_gp_gpp: float = 0.010,
    maxiter: int = 10,
) -> tuple[npt.NDArray, npt.NDArray, bool]:
    """Project along bistatic contours of constant average range and range rate to an arbitrary plane.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    projection_sets : ProjectionSets
        Ensemble of Center of Aperture projection sets to project.
    gref : (3,) array_like
        Ground plane reference point with ECEF (WGS 84 cartesian) X, Y, Z components in meters.
    ugpn : (3,) array_like
        Unit normal vector to ground plane with ECEF (WGS 84 cartesian) X, Y, Z components in
        meters.
    delta_gp_gpp : float, optional
        Ground plane displacement threshold for final ground plane point in meters.
    maxiter : int, optional
        Maximum number of iterations to perform.

    Returns
    -------
    g : (..., 3) ndarray
        Array of ground plane points with ECEF (WGS 84 cartesian) X, Y, Z components in meters
        in the last dimension.
    delta_gp : ndarray
        Magnitude of the displacement from estimated point to the precise intersection
        of the target R/Rdot contour.
    success : bool
        Whether or not all displacement magnitudes, ``delta_gp`` are less than or equal
        to the threshold, ``delta_gp_gpp``.

    """
    assert projection_sets.Xmt_COA is not None
    assert projection_sets.VXmt_COA is not None
    assert projection_sets.Rcv_COA is not None
    assert projection_sets.VRcv_COA is not None
    assert projection_sets.R_Avg_COA is not None
    assert projection_sets.Rdot_Avg_COA is not None

    gref = np.asarray(gref)
    ugpn = np.asarray(ugpn)
    # Compute initial ground points
    u_up_scp = np.stack(
        (
            np.cos(np.deg2rad(proj_metadata.SCP_Lat))
            * np.cos(np.deg2rad(proj_metadata.SCP_Lon)),
            np.cos(np.deg2rad(proj_metadata.SCP_Lat))
            * np.sin(np.deg2rad(proj_metadata.SCP_Lon)),
            np.sin(np.deg2rad(proj_metadata.SCP_Lat)),
        ),
        axis=-1,
    )
    dist_gp = ((gref - proj_metadata.SCP) * ugpn).sum(axis=-1, keepdims=True) / (
        u_up_scp * ugpn
    ).sum(axis=-1, keepdims=True)
    g_0 = proj_metadata.SCP + dist_gp * u_up_scp

    xmt, vxmt, rcv, vrcv, g, ugpn = np.broadcast_arrays(
        projection_sets.Xmt_COA,
        projection_sets.VXmt_COA,
        projection_sets.Rcv_COA,
        projection_sets.VRcv_COA,
        g_0,
        ugpn,
    )
    g = np.array(g)  # make writable
    delta_gp = np.full(g.shape[:-1], np.nan)
    success = False
    above_threshold = np.full(g.shape[:-1], True)
    for _ in range(maxiter):
        pt_r_rdot_params = compute_pt_r_rdot_parameters(
            proj_metadata,
            params.CoaPosVels(
                Xmt_COA=xmt[above_threshold, :],
                VXmt_COA=vxmt[above_threshold, :],
                Rcv_COA=rcv[above_threshold, :],
                VRcv_COA=vrcv[above_threshold, :],
            ),
            g[above_threshold, :],
        )

        gp_xy_params = compute_gp_xy_parameters(
            g[above_threshold, :],
            ugpn[above_threshold, :],
            pt_r_rdot_params.bP_PT,
            pt_r_rdot_params.bPDot_PT,
        )

        delta_r_avg = (
            projection_sets.R_Avg_COA[above_threshold] - pt_r_rdot_params.R_Avg_PT
        )
        delta_rdot_avg = (
            projection_sets.Rdot_Avg_COA[above_threshold] - pt_r_rdot_params.Rdot_Avg_PT
        )

        delta_gxgy = (
            gp_xy_params.M_GPXY_RRdot
            @ np.concatenate((delta_r_avg, delta_rdot_avg), axis=-1)[..., np.newaxis]
        )
        delta_gp[above_threshold] = np.linalg.norm(delta_gxgy, axis=-2).squeeze(axis=-1)

        g[above_threshold, :] += (
            delta_gxgy[..., 0, :] * gp_xy_params.uGX
            + delta_gxgy[..., 1, :] * gp_xy_params.uGY
        )

        # Compare displacement to threshold.
        above_threshold = delta_gp > delta_gp_gpp
        success = bool((delta_gp <= delta_gp_gpp).all())
        if success:
            break
    return g, delta_gp, success


def compute_pt_r_rdot_parameters(
    proj_metadata: params.MetadataParams,
    coa_pos_vels: params.CoaPosVels,
    scene_points: npt.ArrayLike,
) -> params.ScenePointRRdotParams:
    """Compute range and range rate parameters at specified scene point positions.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    coa_pos_vels : CoaPosVels
        Ensemble of COA sensor positions and velocities.
    scene_points : (..., 3) array_like
        Array of scene points with ECEF (WGS 84 cartesian) X, Y, Z components in meters in the
        last dimension.

    Returns
    -------
    ScenePointRRdotParams
        Ensemble of range and range rate parameters for the specified scene points
    """
    pt = np.asarray(scene_points)

    # Compute parameters for transmit APC relative to scene points
    r_xmt_pt = np.linalg.norm(coa_pos_vels.Xmt_COA - pt, axis=-1, keepdims=True)
    u_xmt_pt = (coa_pos_vels.Xmt_COA - pt) / r_xmt_pt
    rdot_xmt_pt = (coa_pos_vels.VXmt_COA * u_xmt_pt).sum(axis=-1, keepdims=True)
    u_xmtdot_pt = (coa_pos_vels.VXmt_COA - rdot_xmt_pt * u_xmt_pt) / r_xmt_pt

    # Compute parameters for receive APC relative to scene points
    r_rcv_pt = np.linalg.norm(coa_pos_vels.Rcv_COA - pt, axis=-1, keepdims=True)
    u_rcv_pt = (coa_pos_vels.Rcv_COA - pt) / r_rcv_pt
    rdot_rcv_pt = (coa_pos_vels.VRcv_COA * u_rcv_pt).sum(axis=-1, keepdims=True)
    u_rcvdot_pt = (coa_pos_vels.VRcv_COA - rdot_rcv_pt * u_rcv_pt) / r_rcv_pt

    # Compute average range and average range rate
    r_avg_pt = (r_xmt_pt + r_rcv_pt) / 2.0
    rdot_avg_pt = (rdot_xmt_pt + rdot_rcv_pt) / 2.0

    # Compute bistatic pointing vector and its derivative w.r.t. time
    bp_pt = (u_xmt_pt + u_rcv_pt) / 2.0
    bpdot_pt = (u_xmtdot_pt + u_rcvdot_pt) / 2.0

    # Compute bistatic slant plane unit normal vector
    look = {"L": +1, "R": -1}[proj_metadata.SideOfTrack]
    spn_pt = look * np.cross(bp_pt, bpdot_pt)
    uspn_pt = spn_pt / np.linalg.norm(spn_pt)

    return params.ScenePointRRdotParams(
        R_Avg_PT=r_avg_pt,
        Rdot_Avg_PT=rdot_avg_pt,
        bP_PT=bp_pt,
        bPDot_PT=bpdot_pt,
        uSPN_PT=uspn_pt,
    )


def compute_gp_xy_parameters(
    scene_points: npt.ArrayLike,
    ugpn: npt.ArrayLike,
    bp_points: npt.ArrayLike,
    bpdot_points: npt.ArrayLike,
) -> params.ScenePointGpXyParams:
    """Compute the basis vectors and sensitivity matrices for a ground plane coordinate system.

    Parameters
    ----------
    scene_points : (..., 3) array_like
        Array of scene points with ECEF (WGS 84 cartesian) X, Y, Z components in meters in the
        last dimension.
    ugpn : (..., 3) array_like
        Unit normal vector to ground plane with ECEF (WGS 84 cartesian) X, Y, Z components in
        meters.
    bp_points, bpdot_points : (..., 3) array_like
        Bistatic pointing vector and its derivative with respect to time.

    Returns
    -------
    ScenePointGpXyParams
        Ensemble of scene point ground plane XY parameters for the specified scene points
    """
    pt = np.asarray(scene_points)
    ugpn = np.asarray(ugpn)
    bp_pt = np.asarray(bp_points)
    bpdot_pt = np.asarray(bpdot_points)

    gx = bp_pt - ugpn * (bp_pt * ugpn).sum(axis=-1, keepdims=True)
    ugx = gx / np.linalg.norm(gx, axis=-1, keepdims=True)

    _sgn_criteria = (ugpn * pt).sum(axis=-1, keepdims=True)
    sgn = np.full_like(_sgn_criteria, -1.0)
    sgn[_sgn_criteria > 0] = +1.0

    gy = sgn * np.cross(ugpn, ugx)
    ugy = gy / np.linalg.norm(gy, axis=-1, keepdims=True)

    m_rrdot_gpxy = np.negative(
        np.stack(
            (
                np.stack(
                    ((bp_pt * ugx).sum(axis=-1), np.zeros_like(ugx[..., 0])), axis=-1
                ),
                np.stack(
                    ((bpdot_pt * ugx).sum(axis=-1), (bpdot_pt * ugy).sum(axis=-1)),
                    axis=-1,
                ),
            ),
            axis=-1,
        )
    )

    m_gpxy_rrdot = np.linalg.inv(m_rrdot_gpxy)
    return params.ScenePointGpXyParams(
        uGX=ugx,
        uGY=ugy,
        M_RRdot_GPXY=m_rrdot_gpxy,
        M_GPXY_RRdot=m_gpxy_rrdot,
    )


def scene_to_image(
    proj_metadata: params.MetadataParams,
    scene_points: npt.ArrayLike,
    *,
    delta_gp_s2i: float = 0.001,
    maxiter: int = 10,
    bistat_delta_gp_gpp: float = 0.010,
    bistat_maxiter: int = 10,
) -> tuple[npt.NDArray, npt.NDArray, bool]:
    """Map geolocated points in the three-dimensional scene to image grid locations.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    scene_points : (..., 3) array_like
        Array of scene points with ECEF (WGS 84 cartesian) X, Y, Z components in meters in the
        last dimension.
    delta_gp_s2i : float, optional
        Ground plane displacement threshold for final ground plane point in meters.
    maxiter : int, optional
        Maximum number of iterations to perform.
    bistat_delta_gp_gpp : float, optional
        (Bistatic only) Ground plane displacement threshold for intermediate ground
        plane points in meters.
    bistat_maxiter : int, optional
        (Bistatic only) Maximum number of intermediate bistatic R/Rdot to Ground Plane
        iterations to perform per scene-to-image iteration.

    Returns
    -------
    image_grid_locations : (..., 2) ndarray
        Array of image coordinates with xrow/ycol in meters in the last dimension.
        Coordinates are NaN where there is no projection solution.
    delta_gp : ndarray
        Ground-plane to scene displacement magnitude. Values are NaN where there is no
        projection solution.
    success : bool
        Whether or not all displacement magnitudes, ``delta_gp`` are less than or equal
        to the threshold, ``delta_gp_s2i``.
        For bistatic projections, ``success`` also requires convergence of all
        intermediate ground plane points.

    """
    s = np.asarray(scene_points)
    # Compute the spherical earth ground plane unit normals (use Spherical Earth GPN)
    u_gpn = s / np.linalg.norm(s, axis=-1, keepdims=True)

    # Compute projection scale factor
    u_proj = compute_scp_coa_slant_plane_normal(proj_metadata)
    ipn = np.cross(proj_metadata.uRow, proj_metadata.uCol)
    u_ipn = ipn / np.linalg.norm(ipn)
    sf = np.dot(u_proj, u_ipn)

    # Set initial ground plane positions to scene point positions.
    g = s.copy()

    image_grid_locations = np.full(s.shape[:-1] + (2,), np.nan)
    delta_gp = np.full(s.shape[:-1], np.nan)
    success = False
    p = np.full_like(s, np.nan)
    above_threshold = np.full(s.shape[:-1], True)
    r_rdot_to_ground_success = np.full(s.shape[:-1], False)
    for _ in range(maxiter):
        # Project ground points to image plane points
        dist = sf ** (-1) * ((proj_metadata.SCP - g[above_threshold]) * u_ipn).sum(
            axis=-1
        )
        i = g[above_threshold] + dist[..., np.newaxis] * u_proj

        # For image plane points, compute the associated image grid coordinates.
        image_grid_locations[above_threshold] = image_plane_point_to_image_grid(
            proj_metadata, i
        )

        # Compute the COA projection sets
        projection_sets = compute_projection_sets(
            proj_metadata, image_grid_locations[above_threshold]
        )

        # Compute precise projection to ground plane.
        if proj_metadata.is_monostatic():
            p[above_threshold] = r_rdot_to_ground_plane_mono(
                proj_metadata,
                projection_sets,
                s[above_threshold],
                u_gpn[above_threshold],
            )
            r_rdot_to_ground_success[above_threshold] = np.isfinite(
                p[above_threshold]
            ).all(axis=-1)
        else:
            p[above_threshold], _, r_rdot_to_ground_success[above_threshold] = (
                r_rdot_to_ground_plane_bi(
                    proj_metadata,
                    projection_sets,
                    s[above_threshold],
                    u_gpn[above_threshold],
                    delta_gp_gpp=bistat_delta_gp_gpp,
                    maxiter=bistat_maxiter,
                )
            )

        # Compute displacement between ground plane points and scene points.
        delta_p = s - p
        delta_gp = np.linalg.norm(delta_p, axis=-1)

        # Compare displacement to threshold.
        above_threshold = delta_gp > delta_gp_s2i
        g[above_threshold] += delta_p[above_threshold]
        success = bool(
            (delta_gp <= delta_gp_s2i).all() and r_rdot_to_ground_success.all()
        )
        if success:
            break
    return image_grid_locations, delta_gp, success


def r_rdot_to_constant_hae_surface(
    proj_metadata: params.MetadataParams,
    projection_sets: params.ProjectionSets,
    hae0: npt.ArrayLike,
    *,
    delta_hae_max: float = 1.0,
    nlim: int = 3,
    bistat_delta_gp_gpp: float = 0.010,
    bistat_maxiter: int = 10,
) -> tuple[npt.NDArray, npt.NDArray, bool]:
    """Project along contours of constant range and range rate to a surface of constant HAE.

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    projection_sets : ProjectionSets
        Ensemble of Center of Aperture projection sets to project.
    hae0 : array_like
        Surface height above the WGS-84 reference ellipsoid for projection points in meters.
    delta_hae_max : float, optional
        Height threshold for convergence of iterative projection sequence in meters.
    nlim : int, optional
        Maximum number of iterations to perform.
    bistat_delta_gp_gpp : float, optional
        (Bistatic only) Ground plane displacement threshold for intermediate ground
        plane points in meters.
    bistat_maxiter : int, optional
        (Bistatic only) Maximum number of intermediate bistatic R/Rdot to Ground Plane
        iterations to perform per scene-to-image iteration.

    Returns
    -------
    spp_tgt : (..., 3) ndarray
        Array of points on the HAE0 surface with ECEF (WGS 84 cartesian) X, Y, Z components in meters
        in the last dimension.
    delta_hae : ndarray
        Height difference at point GPP relative to HAE0.
    success : bool
        Whether or not all height differences, ``delta_hae`` are less than or equal
        to the threshold, ``delta_hae_max``.
    """
    hae0 = np.asarray(hae0)

    def _calc_up(lat_deg, lon_deg):
        return np.stack(
            (
                np.cos(np.deg2rad(lat_deg)) * np.cos(np.deg2rad(lon_deg)),
                np.cos(np.deg2rad(lat_deg)) * np.sin(np.deg2rad(lon_deg)),
                np.sin(np.deg2rad(lat_deg)),
            ),
            axis=-1,
        )

    # Compute parameters for ground plane 1
    u_gpn1 = _calc_up(proj_metadata.SCP_Lat, proj_metadata.SCP_Lon)
    gref1 = proj_metadata.SCP + (hae0 - proj_metadata.SCP_HAE)[..., np.newaxis] * u_gpn1

    if proj_metadata.is_monostatic():
        assert projection_sets.ARP_COA is not None
        assert projection_sets.VARP_COA is not None
        gref, u_gpn, arp, varp = np.broadcast_arrays(
            gref1, u_gpn1, projection_sets.ARP_COA, projection_sets.VARP_COA
        )
    else:
        assert projection_sets.Xmt_COA is not None
        assert projection_sets.VXmt_COA is not None
        assert projection_sets.Rcv_COA is not None
        assert projection_sets.VRcv_COA is not None
        gref, u_gpn, xmt, vxmt, rcv, vrcv = np.broadcast_arrays(
            gref1,
            u_gpn1,
            projection_sets.Xmt_COA,
            projection_sets.VXmt_COA,
            projection_sets.Rcv_COA,
            projection_sets.VRcv_COA,
        )
    hae0 = np.broadcast_to(hae0, gref.shape[:-1])
    gref = np.array(gref)  # make writable
    u_gpn = np.array(u_gpn)  # make writable
    u_up = np.full(gref.shape, np.nan)
    gpp = np.full(gref.shape, np.nan)
    delta_hae = np.full(gref.shape[:-1], np.nan)
    success = False
    above_threshold = np.full(gref.shape[:-1], True)
    r_rdot_to_plane_success = np.full(gref.shape[:-1], False)
    for _ in range(nlim):
        # Compute precise projection to ground plane.
        if proj_metadata.is_monostatic():
            assert projection_sets.R_COA is not None
            assert projection_sets.Rdot_COA is not None
            gpp[above_threshold, :] = r_rdot_to_ground_plane_mono(
                proj_metadata,
                params.ProjectionSets(
                    t_COA=projection_sets.t_COA[above_threshold],
                    ARP_COA=arp[above_threshold, :],
                    VARP_COA=varp[above_threshold, :],
                    R_COA=projection_sets.R_COA[above_threshold],
                    Rdot_COA=projection_sets.Rdot_COA[above_threshold],
                ),
                gref[above_threshold, :],
                u_gpn[above_threshold, :],
            )
            r_rdot_to_plane_success[above_threshold] = np.isfinite(
                gpp[above_threshold, :]
            ).all(axis=-1)
        else:
            assert projection_sets.R_Avg_COA is not None
            assert projection_sets.Rdot_Avg_COA is not None
            gpp[above_threshold, :], _, r_rdot_to_plane_success[above_threshold] = (
                r_rdot_to_ground_plane_bi(
                    proj_metadata,
                    params.ProjectionSets(
                        t_COA=projection_sets.t_COA[above_threshold],
                        Xmt_COA=xmt[above_threshold, :],
                        VXmt_COA=vxmt[above_threshold, :],
                        Rcv_COA=rcv[above_threshold, :],
                        VRcv_COA=vrcv[above_threshold, :],
                        R_Avg_COA=projection_sets.R_Avg_COA[above_threshold],
                        Rdot_Avg_COA=projection_sets.Rdot_Avg_COA[above_threshold],
                    ),
                    gref[above_threshold, :],
                    u_gpn[above_threshold, :],
                    delta_gp_gpp=bistat_delta_gp_gpp,
                    maxiter=bistat_maxiter,
                )
            )

        # Convert from ECEF to WGS 84 geodetic
        gpp_llh = sarkit.standards.geocoords.ecf_to_geodetic(gpp[above_threshold, :])

        # Compute unit vector in increasing height direction and height difference at GPP.
        u_up[above_threshold, :] = _calc_up(gpp_llh[..., 0], gpp_llh[..., 1])
        delta_hae[above_threshold] = gpp_llh[..., 2] - hae0[above_threshold]

        # Check if GPP is sufficiently close to HAE0 surface.
        above_threshold = delta_hae > delta_hae_max
        success = bool(
            (delta_hae <= delta_hae_max).all() and r_rdot_to_plane_success.all()
        )
        if success:
            break
        gref[above_threshold, :] = (
            gpp[above_threshold, :]
            - delta_hae[above_threshold] * u_up[above_threshold, :]
        )
        u_gpn[above_threshold, :] = u_up[above_threshold, :]

    # Compute slant plane normal tangent to R/Rdot contour at GPP.
    look = {"L": +1, "R": -1}[proj_metadata.SideOfTrack]
    if proj_metadata.is_monostatic():
        spn = look * np.cross(varp, gpp - arp)
        u_spn = spn / np.linalg.norm(spn, axis=-1, keepdims=True)
    else:
        gpp_r_rdot_params = compute_pt_r_rdot_parameters(
            proj_metadata,
            params.CoaPosVels(
                Xmt_COA=projection_sets.Xmt_COA,
                VXmt_COA=projection_sets.VXmt_COA,
                Rcv_COA=projection_sets.Rcv_COA,
                VRcv_COA=projection_sets.VRcv_COA,
            ),
            gpp,
        )
        u_spn = gpp_r_rdot_params.uSPN_PT

    # Compute straight-line projection from GPP along uSPN to point SLP.
    sf = (u_up * u_spn).sum(axis=-1, keepdims=True)
    slp = gpp - (delta_hae[..., np.newaxis] * u_spn) / sf

    # Convert SLP from ECEF to geodetic
    slp_llh = sarkit.standards.geocoords.ecf_to_geodetic(slp)

    # Assign surface point spp by adjusting HAE to be on HAE0 surface.
    spp_llh = slp_llh.copy()
    spp_llh[..., 2] = hae0

    # Convert SPP from geodetic to ECEF
    spp_tgt = sarkit.standards.geocoords.geodetic_to_ecf(spp_llh)

    return spp_tgt, delta_hae, success
