"""
=========================================================
SICD Projection (:mod:`sarkit.standards.sicd.projection`)
=========================================================

Sub-package for objects and methods that implement the exploitation processing
described in SICD Volume 3 Image Projections Description Document.

Data Classes
============

To simplify interfaces, some collections of metadata parameters are encapsulated in
dataclasses with attributes named as similar as feasible to the IPDD. Each class
contains a superset of the available parameters. A given instance may only specify a
relevant subset, e.g. for when Collect_Type = MONOSTATIC vs BISTATIC.

.. autosummary::
   :toctree: generated/

   MetadataParams
   CoaPosVels
   ProjectionSets
   ScenePointRRdotParams
   ScenePointGpXyParams

Image Plane Parameters
======================

.. autosummary::
   :toctree: generated/

   image_grid_to_image_plane_point
   image_plane_point_to_image_grid

Image Grid to COA Positions & Velocities
========================================

.. autosummary::
   :toctree: generated/

   compute_coa_time
   compute_coa_pos_vel

SCP Pixel Projection
====================

.. autosummary::
   :toctree: generated/

   compute_scp_coa_r_rdot
   compute_scp_coa_slant_plane_normal

Image Grid to R/Rdot Contour
============================

.. autosummary::
   :toctree: generated/

   compute_coa_r_rdot
   compute_projection_sets

Precise R/Rdot to Ground Plane Projection
=========================================

.. autosummary::
   :toctree: generated/

   r_rdot_to_ground_plane_mono
   r_rdot_to_ground_plane_bi
   compute_pt_r_rdot_parameters
   compute_gp_xy_parameters

Scene To Image Grid Projection
==============================

.. autosummary::
   :toctree: generated/

   scene_to_image

Precise R/Rdot to Constant HAE Surface Projection
=================================================

.. autosummary::
   :toctree: generated/

   r_rdot_to_constant_hae_surface
"""

from .calc import (
    compute_coa_pos_vel,
    compute_coa_r_rdot,
    compute_coa_time,
    compute_gp_xy_parameters,
    compute_projection_sets,
    compute_pt_r_rdot_parameters,
    compute_scp_coa_r_rdot,
    compute_scp_coa_slant_plane_normal,
    image_grid_to_image_plane_point,
    image_plane_point_to_image_grid,
    r_rdot_to_constant_hae_surface,
    r_rdot_to_ground_plane_bi,
    r_rdot_to_ground_plane_mono,
    scene_to_image,
)
from .params import (
    CoaPosVels,
    MetadataParams,
    ProjectionSets,
    ScenePointGpXyParams,
    ScenePointRRdotParams,
)

__all__ = [
    "compute_coa_pos_vel",
    "compute_coa_r_rdot",
    "compute_coa_time",
    "compute_gp_xy_parameters",
    "compute_projection_sets",
    "compute_pt_r_rdot_parameters",
    "compute_scp_coa_r_rdot",
    "compute_scp_coa_slant_plane_normal",
    "image_grid_to_image_plane_point",
    "image_plane_point_to_image_grid",
    "r_rdot_to_constant_hae_surface",
    "r_rdot_to_ground_plane_bi",
    "r_rdot_to_ground_plane_mono",
    "scene_to_image",
]

__all__ += [
    "CoaPosVels",
    "MetadataParams",
    "ProjectionSets",
    "ScenePointGpXyParams",
    "ScenePointRRdotParams",
]
