import dataclasses

import numpy as np
import numpy.typing as npt

import sarkit.wgs84
from sarkit.sicd.projection import _calc
from sarkit.sicd.projection import _params as params


@dataclasses.dataclass(kw_only=True)
class SensitivityMatrices:
    """Sensitivity Matrices See: Table 11-2 and Table 11-3"""

    # Table 11-2
    M_SPXY_PT: np.ndarray
    M_PT_GPXY: np.ndarray
    M_SPXY_GPXY: np.ndarray
    M_GPXY_SPXY: np.ndarray
    M_SPXY_IL: np.ndarray
    M_IL_SPXY: np.ndarray

    # Table 11-3
    M_IL_PT: np.ndarray
    M_IL_GPXY: np.ndarray
    M_GPXY_IL: np.ndarray
    M_PT_HAE: np.ndarray
    M_IL_HAE: np.ndarray

    def __post_init__(self):
        assert self.M_SPXY_PT.shape == (2, 3)
        assert self.M_PT_GPXY.shape == (3, 2)
        assert self.M_SPXY_GPXY.shape == (2, 2)
        assert self.M_GPXY_SPXY.shape == (2, 2)
        assert self.M_SPXY_IL.shape == (2, 2)
        assert self.M_IL_SPXY.shape == (2, 2)

        assert self.M_IL_PT.shape == (2, 3)
        assert self.M_IL_GPXY.shape == (2, 2)
        assert self.M_GPXY_IL.shape == (2, 2)
        assert self.M_PT_HAE.shape == (3, 1)
        assert self.M_IL_HAE.shape == (2, 1)


def compute_sensitivity_matrices(
    proj_metadata: params.MetadataParams,
    pt0: npt.ArrayLike | None = None,
    u_gpn0: npt.ArrayLike | None = None,
    delta_xrow: float | None = None,
    delta_ycol: float | None = None,
) -> SensitivityMatrices:
    """Compute the defined sensitivity matrices

    Parameters
    ----------
    proj_metadata : MetadataParams
        Metadata parameters relevant to projection.
    pt0 : array_like, optional
        ECF scene point. Defaults to SCP.
    u_gpn0 : array_like, optional
        unit normal to scene surface at pt0. Defaults to ETP normal at pt0.
    delta_xrow : float, optional
        row coordinate increment (m).  Defaults to min(Row_SS, 1.0).
    delta_ycol : float, optional
        col coordinate increment (m).  Defaults to min(Col_SS, 1.0).

    Returns
    -------
    SensitivityMatrices
    """

    assert proj_metadata.is_monostatic()

    if pt0 is None:
        pt0 = proj_metadata.SCP
    pt0 = np.asarray(pt0)

    if delta_xrow is None:
        delta_xrow = min(1.0, proj_metadata.Row_SS)
    if delta_ycol is None:
        delta_ycol = min(1.0, proj_metadata.Col_SS)

    il0, _, _ = _calc.scene_to_image(proj_metadata, pt0)
    proj_set_0 = _calc.compute_projection_sets(proj_metadata, il0)
    assert isinstance(proj_set_0, params.ProjectionSetsMono)

    pt0_lat, pt0_lon = sarkit.wgs84.cartesian_to_geodetic(pt0)[:2]
    u_up0 = np.stack(
        (
            np.cos(np.deg2rad(pt0_lat)) * np.cos(np.deg2rad(pt0_lon)),
            np.cos(np.deg2rad(pt0_lat)) * np.sin(np.deg2rad(pt0_lon)),
            np.sin(np.deg2rad(pt0_lat)),
        )
    )
    if u_gpn0 is None:
        u_gpn0 = u_up0
    u_gpn0 = np.asarray(u_gpn0)

    assert np.dot(u_gpn0, u_up0) > 0
    assert pt0.shape == (3,)
    assert u_gpn0.shape == (3,)
    assert np.isscalar(delta_xrow)
    assert np.isscalar(delta_ycol)

    # Ground Plane & Slant Plane Coordinates
    # (1)
    u_gpz = u_gpn0
    arp0_gpz = np.dot(proj_set_0.ARP_COA - pt0, u_gpz)

    sin_graz = arp0_gpz / proj_set_0.R_COA

    agpn0 = proj_set_0.ARP_COA - np.dot(arp0_gpz, u_gpz)
    arp0_gpx = np.linalg.norm(agpn0 - pt0, axis=-1)
    cos_graz = arp0_gpx / proj_set_0.R_COA
    tan_graz = sin_graz / cos_graz
    u_gpx = (agpn0 - pt0) / arp0_gpx
    u_gpy = np.cross(u_gpz, u_gpx)

    # (2)
    vm0 = np.linalg.norm(proj_set_0.VARP_COA, axis=-1)
    u_vm = proj_set_0.VARP_COA / vm0
    u_spx = (proj_set_0.ARP_COA - pt0) / proj_set_0.R_COA
    spz = proj_metadata.LOOK * np.cross(u_spx, u_vm)
    u_spz = spz / np.linalg.norm(spz, axis=-1)
    u_spy = np.cross(u_spz, u_spx)
    u_vc = np.cross(u_spz, u_vm)

    # (3)
    sin_twst = np.dot(-u_gpy, u_spz)
    cos_twst = np.dot(u_gpy, u_spy)
    tan_twst = sin_twst / cos_twst
    cos_dca0 = -proj_set_0.Rdot_COA / vm0
    sin_dca0 = np.sqrt(1 - cos_dca0**2)

    m_spxy_pt = np.stack((u_spx, u_spy))
    m_pt_gpxy = np.stack((u_gpx, u_gpy)).T
    m_spxy_gpxy = np.asarray([[cos_graz, 0], [-sin_graz * sin_twst, cos_twst]])
    m_gpxy_spxy = np.asarray([[1 / cos_graz, 0], [tan_graz * tan_twst, 1 / cos_twst]])

    # Delta SPXY Due To a Change in the Row Coordinate
    # (1)
    il1x = il0 + [delta_xrow, 0]

    # (2)
    proj_set_1x = _calc.compute_projection_sets(proj_metadata, il1x)
    assert isinstance(proj_set_1x, params.ProjectionSetsMono)
    delta_arp1x_coa = proj_set_1x.ARP_COA - proj_set_0.ARP_COA
    delta_r1x_coa = proj_set_1x.R_COA - proj_set_0.R_COA
    delta_varp1x_coa = proj_set_1x.VARP_COA - proj_set_0.VARP_COA
    delta_rdot1x_coa = proj_set_1x.Rdot_COA - proj_set_0.Rdot_COA

    # (3)
    delta_arp1x_spx = np.dot(delta_arp1x_coa, u_spx)
    delta_vm1x = np.dot(delta_varp1x_coa, u_vm)
    delta_arp1x_spy = np.dot(delta_arp1x_coa, u_spy)
    delta_vc1x = np.dot(delta_varp1x_coa, u_vc)

    # (4)
    delta_cos_dca1x = -(delta_rdot1x_coa + delta_vm1x * cos_dca0) / vm0
    delta_dca1x = -delta_cos_dca1x / sin_dca0

    # (5)
    delta_vdir1x = delta_vc1x / vm0

    # (6)
    delta_ang1x = delta_vdir1x + proj_metadata.LOOK * delta_dca1x

    # (7)
    delta_spx1x = delta_arp1x_spx - delta_r1x_coa
    delta_spy1x = delta_arp1x_spy - proj_set_0.R_COA * delta_ang1x

    # Delta SPXY Due To a Change in the Column Coordinate
    # (1)
    il1y = il0 + [0, delta_ycol]
    # (2)
    proj_set_1y = _calc.compute_projection_sets(proj_metadata, il1y)
    assert isinstance(proj_set_1y, params.ProjectionSetsMono)

    delta_arp1y_coa = proj_set_1y.ARP_COA - proj_set_0.ARP_COA
    delta_r1y_coa = proj_set_1y.R_COA - proj_set_0.R_COA
    delta_varp1y_coa = proj_set_1y.VARP_COA - proj_set_0.VARP_COA
    delta_rdot1y_coa = proj_set_1y.Rdot_COA - proj_set_0.Rdot_COA

    # (3)
    delta_arp1y_spx = np.dot(delta_arp1y_coa, u_spx)
    delta_vm1y = np.dot(delta_varp1y_coa, u_vm)
    delta_arp1y_spy = np.dot(delta_arp1y_coa, u_spy)
    delta_vc1y = np.dot(delta_varp1y_coa, u_vc)

    # (4)
    delta_cos_dca1y = -(delta_rdot1y_coa + delta_vm1y * cos_dca0) / vm0
    delta_dca1y = -delta_cos_dca1y / sin_dca0

    # (5)
    delta_vdir1y = delta_vc1y / vm0

    # (6)
    delta_ang1y = delta_vdir1y + proj_metadata.LOOK * delta_dca1y

    # (7)
    delta_spx1y = delta_arp1y_spx - delta_r1y_coa
    delta_spy1y = delta_arp1y_spy - proj_set_0.R_COA * delta_ang1y

    m_spxy_il = np.asarray(
        [
            [delta_spx1x / delta_xrow, delta_spx1y / delta_ycol],
            [delta_spy1x / delta_xrow, delta_spy1y / delta_ycol],
        ]
    )
    m_il_spxy = np.linalg.inv(m_spxy_il)

    # Image To Scene Sensitivity Matrices
    # (1)
    m_il_pt = m_il_spxy @ m_spxy_pt
    # (2)
    m_il_gpxy = m_il_spxy @ m_spxy_gpxy
    m_gpxy_il = m_gpxy_spxy @ m_spxy_il

    # Scene Point HAE <=> Scene Point or Image Location
    # (1)
    sf_spz = np.dot(u_up0, u_spz)
    m_pt_hae = (u_spz / sf_spz).reshape(3, 1)
    # (2)
    m_il_hae = m_il_pt @ u_up0.reshape(3, 1)

    return SensitivityMatrices(
        M_SPXY_PT=m_spxy_pt,
        M_PT_GPXY=m_pt_gpxy,
        M_SPXY_GPXY=m_spxy_gpxy,
        M_GPXY_SPXY=m_gpxy_spxy,
        M_SPXY_IL=m_spxy_il,
        M_IL_SPXY=m_il_spxy,
        M_IL_PT=m_il_pt,
        M_IL_GPXY=m_il_gpxy,
        M_GPXY_IL=m_gpxy_il,
        M_PT_HAE=m_pt_hae,
        M_IL_HAE=m_il_hae,
    )
