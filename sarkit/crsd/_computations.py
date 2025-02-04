"""
Select calculations from the CRSD D&I
"""

import numpy as np
import numpy.typing as npt

import sarkit.wgs84


def compute_ref_point_parameters(rpt: npt.ArrayLike):
    """Computes the reference point parameters as in CRSD D&I 8.2"""
    rpt_llh = sarkit.wgs84.cartesian_to_geodetic(rpt)
    rpt_lat = rpt_llh[..., 0]
    rpt_lon = rpt_llh[..., 1]
    ueast = np.stack(
        [
            -np.sin(np.deg2rad(rpt_lon)),
            np.cos(np.deg2rad(rpt_lon)),
            np.zeros_like(rpt_lat),
        ],
        axis=-1,
    )
    unor = np.stack(
        [
            -np.sin(np.deg2rad(rpt_lat)) * np.cos(np.deg2rad(rpt_lon)),
            -np.sin(np.deg2rad(rpt_lat)) * np.sin(np.deg2rad(rpt_lon)),
            np.cos(np.deg2rad(rpt_lat)),
        ]
    )
    uup = np.stack(
        [
            np.cos(np.deg2rad(rpt_lat)) * np.cos(np.deg2rad(rpt_lon)),
            np.cos(np.deg2rad(rpt_lat)) * np.sin(np.deg2rad(rpt_lon)),
            np.sin(np.deg2rad(rpt_lat)),
        ],
        axis=-1,
    )
    return rpt_llh, (ueast, unor, uup)


def compute_apc_to_pt_geometry_parameters(
    apc: npt.ArrayLike,
    vapc: npt.ArrayLike,
    pt: npt.ArrayLike,
    ueast: npt.ArrayLike,
    unor: npt.ArrayLike,
    uup: npt.ArrayLike,
):
    """Computes APC geometry parameters as in CRSD D&I 8.3"""
    apc = np.asarray(apc)
    vapc = np.asarray(vapc)
    pt = np.asarray(pt)
    ueast = np.asarray(ueast)
    unor = np.asarray(unor)
    uup = np.asarray(uup)

    # (1)
    r_apc_pt = np.linalg.norm(apc - pt, axis=-1)
    uapc = (apc - pt) / r_apc_pt[..., np.newaxis]
    rdot_apc_pt = np.inner(vapc, uapc)
    uapcdot = (vapc - rdot_apc_pt[..., np.newaxis] * uapc) / r_apc_pt[..., np.newaxis]

    # (2)
    pt_dec = np.linalg.norm(pt, axis=-1)
    uec_pt = pt / pt_dec[..., np.newaxis]

    # (3)
    apc_dec = np.linalg.norm(apc, axis=-1)
    uec_apc = apc / apc_dec[..., np.newaxis]
    ag = pt_dec[..., np.newaxis] * uec_apc

    # (4)
    ea_apc = np.arccos(np.inner(uec_apc, uec_pt))
    rg_pt = pt_dec * ea_apc

    # (5)
    vat = vapc - np.inner(vapc, uec_apc)[..., np.newaxis] * uec_apc
    vat_m = np.linalg.norm(vat, axis=-1)

    # (6)  side of track
    uat = vat / vat_m[..., np.newaxis]
    uleft = np.cross(uec_apc, uat)
    is_left = np.asarray(np.inner(uleft, uapc) < 0)
    is_left[vat_m == 0] = True
    is_left[rg_pt == 0] = True
    side_of_track = np.where(is_left, "L", "R")

    # (7)
    vapc_m = np.linalg.norm(vapc, axis=-1)
    dca = np.asarray(np.rad2deg(np.arccos(-rdot_apc_pt / vapc_m)))
    dca[vapc_m == 0] = 90.0

    # (8)
    pt_at = np.inner(uat, pt - ag)
    pt_ct = np.abs(np.inner(uleft, pt - ag))
    sqnt = np.rad2deg(np.arctan2(pt_at, pt_ct))

    # (9)
    uapc_e = np.inner(ueast, uapc)
    uapc_n = np.inner(unor, uapc)
    uapc_up = np.inner(uup, uapc)

    # (10)
    azim = np.asarray(np.rad2deg(np.arctan2(uapc_e, uapc_n)) % 360)
    azim[rg_pt == 0] = 0.0

    # (11)
    incd = np.rad2deg(np.arccos(uapc_up))
    graz = 90 - incd

    return {
        "R_APC_PT": r_apc_pt,
        "Rdot_APC_PT": rdot_apc_pt,
        "Rg_PT": rg_pt,
        "SideOfTrack": side_of_track,
        "uAPC": uapc,
        "uAPCDot": uapcdot,
        "DCA": dca,
        "SQNT": sqnt,
        "AZIM": azim,
        "GRAZ": graz,
        "INCD": incd,
    }


def compute_apc_to_pt_geometry_parameters_xmlnames(
    apc: npt.ArrayLike,
    vapc: npt.ArrayLike,
    pt: npt.ArrayLike,
    ueast: npt.ArrayLike,
    unor: npt.ArrayLike,
    uup: npt.ArrayLike,
):
    """Computes APC geometry parameters as in CRSD D&I 8.3 but with the XML names"""
    geom = compute_apc_to_pt_geometry_parameters(apc, vapc, pt, ueast, unor, uup)
    return {
        "APCPos": apc,
        "APCVel": vapc,
        "SideOfTrack": geom["SideOfTrack"],
        "SlantRange": geom["R_APC_PT"],
        "GroundRange": geom["Rg_PT"],
        "DopplerConeAngle": geom["DCA"],
        "SquintAngle": geom["SQNT"],
        "AzimuthAngle": geom["AZIM"],
        "GrazeAngle": geom["GRAZ"],
        "IncidenceAngle": geom["INCD"],
    }


def arp_to_rpt_geometry_xmlnames(xmt, vxmt, rcv, vrcv, pt, ueast, unor, uup):
    """Computes ARP geometry as in CRSD D&I 8.4.2 with the XML names"""
    xmt_geom = compute_apc_to_pt_geometry_parameters(xmt, vxmt, pt, ueast, unor, uup)
    rcv_geom = compute_apc_to_pt_geometry_parameters(rcv, vrcv, pt, ueast, unor, uup)
    bp = (xmt_geom["uAPC"] + rcv_geom["uAPC"]) / 2
    bpdot = (xmt_geom["uAPCDot"] + rcv_geom["uAPCDot"]) / 2
    bp_mag = np.linalg.norm(bp, axis=-1)
    bistat_ang = 2 * np.arccos(bp_mag)
    bistat_ang_rate = np.asarray((-4 / np.sin(bistat_ang)) * np.inner(bp, bpdot))
    bistat_ang_rate[bp_mag >= 1] = 0
    bistat_ang_rate[bp_mag == 0] = 0
    uarp = bp / bp_mag[..., np.newaxis]
    uarpdot = (bpdot - np.inner(bpdot, uarp)[..., np.newaxis] * uarp) / bp_mag[
        ..., np.newaxis
    ]
    r_arp_rpt = np.asarray((xmt_geom["R_APC_PT"] + rcv_geom["R_APC_PT"]) / 2)
    rdot_arp_rpt = np.asarray((xmt_geom["Rdot_APC_PT"] + rcv_geom["Rdot_APC_PT"]) / 2)
    arp = pt + r_arp_rpt[..., np.newaxis] * uarp
    varp = rdot_arp_rpt[..., np.newaxis] * uarp + r_arp_rpt * uarpdot
    r_arp_rpt[bp_mag == 0] = 0
    rdot_arp_rpt[bp_mag == 0] = 0
    arp[bp_mag == 0, :] = pt
    varp[bp_mag == 0, :] = 0

    # The next section of calulations (5) - (10) and (13) - (15) are the same as the ones in compute_apc_to_pt_geometry_parameters
    # we call that function instead
    arp_geom = compute_apc_to_pt_geometry_parameters_xmlnames(
        arp, varp, pt, ueast, unor, uup
    )

    # (11)
    ugpz = uup
    bp_gpz = np.inner(bp, ugpz)
    bp_etp = bp - bp_gpz[..., np.newaxis] * ugpz
    bp_gpx = np.linalg.norm(bp_etp, axis=-1)

    # (12)
    ugpx = bp_etp / bp_gpx[..., np.newaxis]
    ugpy = np.cross(ugpz, ugpx)

    # (16)
    bpdot_gpy = np.inner(bpdot, ugpy)

    # (17)
    sgn = np.where(bpdot_gpy > 0, 1, -1)
    spn = sgn[..., np.newaxis] * np.cross(bp, bpdot)
    uspn = spn / np.linalg.norm(spn, axis=-1)[..., np.newaxis]

    # (18)
    arp_twst = np.rad2deg(-np.arcsin(np.inner(uspn, ugpy)))

    # (19)
    arp_slope = np.rad2deg(np.arccos(np.inner(uspn, ugpz)))

    # (20)
    lo_e = -np.inner(ueast, uspn)
    lo_n = -np.inner(unor, uspn)
    arp_lo_ang = np.rad2deg(np.arctan2(lo_e, lo_n)) % 360.0

    return arp_geom | {
        "ARPPos": arp,
        "ARPVel": varp,
        "BistaticAngle": bistat_ang * 180 / np.pi,
        "BistaticAngleRate": bistat_ang_rate * 180 / np.pi,
        "TwistAngle": arp_twst,
        "SlopeAngle": arp_slope,
        "LayoverAngle": arp_lo_ang,
    }


def compute_h_v_los_unit_vectors(apc: npt.ArrayLike, gpt: npt.ArrayLike):
    """Compute H, V, LOS unit vectors as in CRSD D&I 9.4.3"""
    apc = np.asarray(apc)
    gpt = np.asarray(gpt)

    # (1)
    _, (_, _, uup) = compute_ref_point_parameters(gpt)

    # (2)
    r_apc_gpt = np.linalg.norm(gpt - apc, axis=-1)
    ulos = (gpt - apc) / r_apc_gpt[..., np.newaxis]

    # (3)
    hor = np.cross(uup, ulos)
    uhor = hor / np.linalg.norm(hor, axis=-1)[..., np.newaxis]

    # (4)
    uvert = np.cross(ulos, uhor)

    return uhor, uvert, ulos


def compute_h_v_pol_parameters(apc, uacx, uacy, gpt, xr, ampx, ampy, phasex, phasey):
    """Compute H, V polarization parameters as in CRSD D&I 9.4.4"""
    # (1)
    uhor, uvert, ulos = compute_h_v_los_unit_vectors(apc, gpt)

    # (2)
    acxn = uacx - np.inner(uacx, ulos)[..., np.newaxis] * ulos
    acyn = uacy - np.inner(uacy, ulos)[..., np.newaxis] * ulos

    # (3)
    axh = ampx * np.inner(acxn, uhor)
    ayh = ampy * np.inner(acyn, uhor)
    axv = ampx * np.inner(acxn, uvert)
    ayv = ampy * np.inner(acyn, uvert)

    # (4)
    ch = axh * np.exp(xr * 2j * np.pi * phasex) + ayh * np.exp(xr * 2j * np.pi * phasey)
    ah = np.abs(ch)
    phaseh = np.angle(ch) / (2 * np.pi)

    # (5)
    cv = axv * np.exp(xr * 2j * np.pi * phasex) + ayv * np.exp(xr * 2j * np.pi * phasey)
    av = np.abs(cv)
    phasev = np.angle(cv) / (2 * np.pi)

    amph = ah / (ah**2 + av**2) ** 0.5
    ampv = av / (ah**2 + av**2) ** 0.5
    return amph, ampv, phaseh, phasev
