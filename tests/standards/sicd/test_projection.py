import dataclasses
import pathlib

import lxml.etree
import numpy as np
import pytest

import sarpy.standards.geocoords
import sarpy.standards.sicd.projection as ss_proj

DATAPATH = pathlib.Path(__file__).parents[3] / "data"


@pytest.fixture
def example_proj_metadata():
    etree = lxml.etree.parse(DATAPATH / "example-sicd-1.3.0.xml")
    return ss_proj.MetadataParams.from_xml(etree)


@pytest.fixture
def example_proj_metadata_bi():
    etree = lxml.etree.parse(DATAPATH / "example-sicd-1.4.0.xml")
    proj_metadata = ss_proj.MetadataParams.from_xml(etree)
    assert not proj_metadata.is_monostatic()
    return proj_metadata


def test_metadata_params():
    all_attrs = set()
    set_attrs = set()
    for xml_file in (DATAPATH / "syntax_only/sicd").glob("*.xml"):
        etree = lxml.etree.parse(xml_file)
        proj_metadata = ss_proj.MetadataParams.from_xml(etree)
        pm_dict = dataclasses.asdict(proj_metadata)
        all_attrs.update(pm_dict.keys())
        set_attrs.update(k for k, v in pm_dict.items() if v is not None)
    unset_attrs = all_attrs - set_attrs
    assert not unset_attrs


def test_metadata_params_is_monostatic(example_proj_metadata):
    example_proj_metadata.Collect_Type = "MONOSTATIC"
    assert example_proj_metadata.is_monostatic()

    example_proj_metadata.Collect_Type = "BISTATIC"
    assert not example_proj_metadata.is_monostatic()

    example_proj_metadata.Collect_Type = "NOT_A_REAL_COLLECT_TYPE"
    with pytest.raises(ValueError, match="must be MONOSTATIC or BISTATIC"):
        example_proj_metadata.is_monostatic()


def test_image_plane_parameters_roundtrip(example_proj_metadata):
    image_grid_locations = np.random.default_rng(12345).uniform(
        low=-24, high=24, size=(3, 4, 5, 2)
    )
    image_plane_points = ss_proj.image_grid_to_image_plane_point(
        example_proj_metadata, image_grid_locations
    )
    re_image_grid_locations = ss_proj.image_plane_point_to_image_grid(
        example_proj_metadata, image_plane_points
    )
    assert image_grid_locations == pytest.approx(re_image_grid_locations)


def test_compute_coa_time(example_proj_metadata):
    assert ss_proj.compute_coa_time(example_proj_metadata, [0, 0]) == pytest.approx(
        example_proj_metadata.t_SCP_COA
    )


def test_compute_coa_pos_vel_mono(example_proj_metadata):
    assert example_proj_metadata.is_monostatic()
    computed_pos_vel = ss_proj.compute_coa_pos_vel(
        example_proj_metadata, example_proj_metadata.t_SCP_COA
    )
    assert computed_pos_vel.ARP_COA == pytest.approx(example_proj_metadata.ARP_SCP_COA)
    assert computed_pos_vel.VARP_COA == pytest.approx(
        example_proj_metadata.VARP_SCP_COA
    )


def test_compute_coa_pos_vel_bi(example_proj_metadata_bi):
    computed_pos_vel = ss_proj.compute_coa_pos_vel(
        example_proj_metadata_bi, example_proj_metadata_bi.t_SCP_COA
    )
    assert computed_pos_vel.GRP_COA == pytest.approx(example_proj_metadata_bi.SCP)
    assert computed_pos_vel.tx_COA == pytest.approx(example_proj_metadata_bi.tx_SCP_COA)
    assert computed_pos_vel.tr_COA == pytest.approx(example_proj_metadata_bi.tr_SCP_COA)
    assert computed_pos_vel.Xmt_COA == pytest.approx(
        example_proj_metadata_bi.Xmt_SCP_COA
    )
    assert computed_pos_vel.VXmt_COA == pytest.approx(
        example_proj_metadata_bi.VXmt_SCP_COA
    )
    assert computed_pos_vel.Rcv_COA == pytest.approx(
        example_proj_metadata_bi.Rcv_SCP_COA
    )
    assert computed_pos_vel.VRcv_COA == pytest.approx(
        example_proj_metadata_bi.VRcv_SCP_COA
    )


def test_scp_projection_set_mono(example_proj_metadata):
    assert example_proj_metadata.is_monostatic()
    r_scp_coa, rdot_scp_coa = ss_proj.compute_scp_coa_r_rdot(example_proj_metadata)
    scp_proj_set = ss_proj.compute_projection_sets(example_proj_metadata, [0, 0])
    assert scp_proj_set.t_COA == pytest.approx(example_proj_metadata.t_SCP_COA)
    assert scp_proj_set.ARP_COA == pytest.approx(example_proj_metadata.ARP_SCP_COA)
    assert scp_proj_set.VARP_COA == pytest.approx(example_proj_metadata.VARP_SCP_COA)
    assert scp_proj_set.R_COA == pytest.approx(r_scp_coa)
    assert scp_proj_set.Rdot_COA == pytest.approx(rdot_scp_coa)


def test_scp_projection_set_bi(example_proj_metadata_bi):
    assert not example_proj_metadata_bi.is_monostatic()
    r_scp_coa, rdot_scp_coa = ss_proj.compute_scp_coa_r_rdot(example_proj_metadata_bi)
    scp_proj_set = ss_proj.compute_projection_sets(example_proj_metadata_bi, [0, 0])
    assert scp_proj_set.t_COA == pytest.approx(example_proj_metadata_bi.t_SCP_COA)
    assert scp_proj_set.tx_COA == pytest.approx(example_proj_metadata_bi.tx_SCP_COA)
    assert scp_proj_set.tr_COA == pytest.approx(example_proj_metadata_bi.tr_SCP_COA)
    assert scp_proj_set.Xmt_COA == pytest.approx(example_proj_metadata_bi.Xmt_SCP_COA)
    assert scp_proj_set.VXmt_COA == pytest.approx(example_proj_metadata_bi.VXmt_SCP_COA)
    assert scp_proj_set.Rcv_COA == pytest.approx(example_proj_metadata_bi.Rcv_SCP_COA)
    assert scp_proj_set.VRcv_COA == pytest.approx(example_proj_metadata_bi.VRcv_SCP_COA)
    assert scp_proj_set.R_Avg_COA == pytest.approx(r_scp_coa)
    assert scp_proj_set.Rdot_Avg_COA == pytest.approx(rdot_scp_coa)


@pytest.mark.parametrize(
    "pm_fixture_name", ("example_proj_metadata", "example_proj_metadata_bi")
)
def test_scp_coa_slant_plane_normal(pm_fixture_name, request):
    proj_metadata = request.getfixturevalue(pm_fixture_name)
    u_spn_scp_coa = ss_proj.compute_scp_coa_slant_plane_normal(proj_metadata)

    # unit vector
    assert np.linalg.norm(u_spn_scp_coa) == pytest.approx(1.0)

    # points away from earth
    assert np.linalg.norm(proj_metadata.SCP) < np.linalg.norm(
        proj_metadata.SCP + u_spn_scp_coa
    )


def test_compute_pt_r_rdot_parameters_mono(example_proj_metadata):
    """From Vol. 3:
    For a Monostatic Image: Input the COA ARP position and velocity for both COA APC
    positions and velocities. The resulting range and range rate will be the range and range rate of
    the ARP relative to the point PT.
    """

    pt_r_rdot_params = ss_proj.compute_pt_r_rdot_parameters(
        example_proj_metadata,
        ss_proj.CoaPosVels(
            Xmt_COA=example_proj_metadata.ARP_SCP_COA,
            VXmt_COA=example_proj_metadata.VARP_SCP_COA,
            Rcv_COA=example_proj_metadata.ARP_SCP_COA,
            VRcv_COA=example_proj_metadata.VARP_SCP_COA,
        ),
        example_proj_metadata.SCP,
    )
    r_scp, rdot_scp = ss_proj.compute_scp_coa_r_rdot(example_proj_metadata)
    assert pt_r_rdot_params.R_Avg_PT == pytest.approx(r_scp)
    assert pt_r_rdot_params.Rdot_Avg_PT == pytest.approx(rdot_scp)


def test_r_rdot_to_ground_plane(example_proj_metadata):
    im_coords = np.random.default_rng(12345).uniform(
        low=-24.0, high=24.0, size=(3, 4, 5, 2)
    )
    proj_sets_mono = ss_proj.compute_projection_sets(example_proj_metadata, im_coords)
    scp_spn = ss_proj.compute_scp_coa_slant_plane_normal(example_proj_metadata)
    gpp_tgt_mono = ss_proj.r_rdot_to_ground_plane_mono(
        example_proj_metadata,
        proj_sets_mono,
        example_proj_metadata.SCP,
        scp_spn,
    )

    # Per Volume 3: The bistatic function defined may also be used for a monostatic image.
    gpp_tgt_bi, delta_gp, success = ss_proj.r_rdot_to_ground_plane_bi(
        example_proj_metadata,
        ss_proj.ProjectionSets(
            t_COA=proj_sets_mono.t_COA,
            Xmt_COA=proj_sets_mono.ARP_COA,
            VXmt_COA=proj_sets_mono.VARP_COA,
            Rcv_COA=proj_sets_mono.ARP_COA,
            VRcv_COA=proj_sets_mono.VARP_COA,
            R_Avg_COA=proj_sets_mono.R_COA,
            Rdot_Avg_COA=proj_sets_mono.Rdot_COA,
        ),
        example_proj_metadata.SCP,
        scp_spn,
    )
    assert gpp_tgt_mono == pytest.approx(gpp_tgt_bi)
    assert np.isfinite(delta_gp).all()
    assert success


@pytest.mark.parametrize("scalar_hae", (True, False))
@pytest.mark.parametrize(
    "mdata_name", ("example_proj_metadata", "example_proj_metadata_bi")
)
def test_r_rdot_to_hae_surface(mdata_name, scalar_hae, request):
    proj_metadata = request.getfixturevalue(mdata_name)
    rng = np.random.default_rng(12345)
    im_coords = rng.uniform(low=-24.0, high=24.0, size=(3, 4, 5, 2))
    hae0 = proj_metadata.SCP_HAE
    if not scalar_hae:
        hae0 += rng.uniform(low=-24.0, high=24.0, size=im_coords.shape[:-1])
    proj_sets = ss_proj.compute_projection_sets(proj_metadata, im_coords)
    spp_tgt, _, success = ss_proj.r_rdot_to_constant_hae_surface(
        proj_metadata,
        proj_sets,
        hae0,
    )
    assert success
    spp_llh = sarpy.standards.geocoords.ecf_to_geodetic(spp_tgt)
    assert spp_llh[..., 2] == pytest.approx(hae0, abs=1e-6)

    bad_index = (1, 2, 3)
    if proj_metadata.is_monostatic():
        proj_sets.R_COA[bad_index] *= 1e6
    else:
        proj_sets.R_Avg_COA[bad_index] *= 1e6

    spp_tgt_w_bad, _, success = ss_proj.r_rdot_to_constant_hae_surface(
        proj_metadata,
        proj_sets,
        hae0,
    )
    assert not success
    mismatched_index = np.argwhere((spp_tgt != spp_tgt_w_bad).any(axis=-1)).squeeze()
    assert np.array_equal(bad_index, mismatched_index)