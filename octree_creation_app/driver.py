#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of octree-creation-app package.
#
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

import sys

import numpy as np
from discretize import TreeMesh
from discretize.utils import mesh_builder_xyz
from geoapps_utils.driver.driver import BaseDriver
from geoapps_utils.locations import get_locations
from geoh5py.objects import Curve, ObjectBase, Octree, Points, Surface
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import utils
from scipy import interpolate
from scipy.spatial import Delaunay, cKDTree

from octree_creation_app.params import OctreeParams
from octree_creation_app.utils import densify_curve, treemesh_2_octree


class OctreeDriver(BaseDriver):
    """
    Driver for octree mesh creation.
    """

    _params_class = OctreeParams
    _validations: dict = {}

    def __init__(self, params: OctreeParams):
        super().__init__(params)
        self.params: OctreeParams = params

    def run(self) -> Octree:
        """
        Create an octree mesh from input values
        """
        with fetch_active_workspace(self.params.geoh5, mode="r+"):
            octree = self.octree_from_params(self.params)
            self.update_monitoring_directory(octree)

        return octree

    @staticmethod
    def minimum_level(mesh: TreeMesh, level: int):
        """Computes the minimum level of refinement for a given tree mesh."""
        return max([1, mesh.max_level - level + 1])

    @staticmethod
    def octree_from_params(params: OctreeParams):
        print("Setting the mesh extent")
        entity = params.objects
        mesh: TreeMesh = mesh_builder_xyz(
            entity.vertices,
            [
                params.u_cell_size,
                params.v_cell_size,
                params.w_cell_size,
            ],
            padding_distance=params.get_padding(),
            mesh_type="tree",
            depth_core=params.depth_core,
        )
        minimum_level = OctreeDriver.minimum_level(mesh, params.minimum_level)
        mesh.refine(
            minimum_level, finalize=False, diagonal_balance=params.diagonal_balance
        )

        for label, value in params.free_parameter_dict.items():
            refinement_object = getattr(params, value["object"])
            levels = utils.str2list(getattr(params, value["levels"]))
            if not isinstance(refinement_object, ObjectBase):
                continue

            print(f"Applying {label} on: {getattr(params, value['object']).name}")

            if getattr(params, value["horizon"]):
                mesh = OctreeDriver.refine_tree_from_surface(
                    mesh,
                    refinement_object,
                    levels,
                    params.diagonal_balance,
                    max_distance=getattr(params, value["distance"]),
                )

            elif isinstance(refinement_object, Curve):
                mesh = OctreeDriver.refine_tree_from_curve(
                    mesh, refinement_object, levels, params.diagonal_balance
                )

            elif isinstance(refinement_object, Surface):
                mesh = OctreeDriver.refine_tree_from_triangulation(
                    mesh, refinement_object, levels, params.diagonal_balance
                )

            elif isinstance(refinement_object, Points):
                mesh = OctreeDriver.refine_tree_from_points(
                    mesh,
                    refinement_object,
                    levels,
                    diagonal_balance=params.diagonal_balance,
                )

            else:
                raise NotImplementedError(
                    f"Refinement for object {type(refinement_object)} is not implemented."
                )

        print("Finalizing . . .")
        mesh.finalize()
        octree = treemesh_2_octree(params.geoh5, mesh, name=params.ga_group_name)

        return octree

    @staticmethod
    def refine_tree_from_curve(
        mesh: TreeMesh,
        curve: Curve,
        levels: list[int] | np.ndarray,
        diagonal_balance: bool = True,
        finalize: bool = False,
    ) -> TreeMesh:
        """
        Refine a tree mesh along the segments of a curve densified by the
        mesh cell size.

        :param mesh: Tree mesh to refine.
        :param curve: Curve object to use for refinement.
        :param levels: Number of cells requested at each refinement level.
            Defined in reversed order from the highest octree to lowest.
        :param diagonal_balance: Whether to balance cells along the diagonal
            of the tree during construction.
        :param finalize: Finalize the tree mesh after refinement.

        """
        if not isinstance(curve, Curve):
            raise TypeError("Refinement object must be a Curve.")

        if isinstance(levels, list):
            levels = np.array(levels)

        locations = densify_curve(curve, mesh.h[0][0])
        mesh = OctreeDriver.refine_tree_from_points(
            mesh, locations, levels, diagonal_balance=diagonal_balance, finalize=False
        )

        if finalize:
            mesh.finalize()

        return mesh

    @staticmethod
    def refine_tree_from_points(
        mesh: TreeMesh,
        points: ObjectBase | np.ndarray,
        levels: list[int] | np.ndarray,
        diagonal_balance: bool = True,
        finalize: bool = False,
    ) -> TreeMesh:
        """
        Refine a tree mesh along the vertices of an object.

        :param mesh: Tree mesh to refine.
        :param points: Object to use for refinement.
        :param levels: Number of cells requested at each refinement level.
            Defined in reversed order from the highest octree to lowest.
        :param diagonal_balance: Whether to balance cells along the diagonal of
            the tree during construction.
        :param finalize: Finalize the tree mesh after refinement.

        :return: Refined tree mesh.
        """
        if isinstance(points, ObjectBase):
            locations = get_locations(points.workspace, points)
        else:
            locations = points

        if locations is None:
            raise ValueError("Could not find locations for refinement.")

        if isinstance(levels, list):
            levels = np.array(levels)

        distance = 0
        for ii, n_cells in enumerate(levels):
            distance += n_cells * OctreeDriver.cell_size_from_level(mesh, ii)
            mesh.refine_ball(
                locations,
                distance,
                mesh.max_level - ii,
                diagonal_balance=diagonal_balance,
                finalize=False,
            )

        if finalize:
            mesh.finalize()

        return mesh

    @staticmethod
    def refine_tree_from_surface(  # pylint: disable=too-many-arguments, too-many-locals
        mesh: TreeMesh,
        surface: ObjectBase,
        levels: list[int] | np.ndarray,
        diagonal_balance: bool = True,
        max_distance: float = np.inf,
        finalize: bool = False,
    ) -> TreeMesh:
        """
        Refine a tree mesh along the simplicies of a surface.

        :param mesh: Tree mesh to refine.
        :param surface: Surface object to use for refinement.
        :param levels: Number of cells requested at each refinement level.
            Defined in reversed order from the highest octree to lowest.
        :param max_distance: Maximum distance from the surface to refine.
        :param diagonal_balance: Whether to balance cells along the diagonal
            of the tree during construction.
        :param finalize: Finalize the tree mesh after refinement.

        :return: Refined tree mesh.
        """
        if isinstance(levels, list):
            levels = np.array(levels)

        xyz = get_locations(surface.workspace, surface)
        triang = Delaunay(xyz[:, :2])
        tree = cKDTree(xyz[:, :2])

        interp = interpolate.LinearNDInterpolator(triang, xyz[:, -1])
        levels = np.array(levels)

        depth = 0
        # Cycle through the Tree levels backward
        for ind, n_cells in enumerate(levels):
            if n_cells == 0:
                continue

            dx = OctreeDriver.cell_size_from_level(mesh, ind, 0)
            dy = OctreeDriver.cell_size_from_level(mesh, ind, 1)
            dz = OctreeDriver.cell_size_from_level(mesh, ind, 2)

            # Create a grid at the octree level in xy
            cell_center_x, cell_center_y = np.meshgrid(
                np.arange(surface.extent[0, 0], surface.extent[1, 0], dx),
                np.arange(surface.extent[0, 1], surface.extent[1, 1], dy),
            )
            xy = np.c_[cell_center_x.reshape(-1), cell_center_y.reshape(-1)]

            # Only keep points within triangulation
            inside = triang.find_simplex(xy) != -1
            r, _ = tree.query(xy)
            keeper = np.logical_and(r < max_distance, inside)
            nnz = keeper.sum()
            elevation = interp(xy[keeper])

            # Apply vertical padding for current octree level
            for _ in range(int(n_cells)):
                depth += dz
                mesh.insert_cells(
                    np.c_[xy[keeper], elevation - depth],
                    np.ones(nnz) * mesh.max_level - ind,
                    diagonal_balance=diagonal_balance,
                    finalize=False,
                )

        if finalize:
            mesh.finalize()

        return mesh

    @staticmethod
    def refine_tree_from_triangulation(
        mesh: TreeMesh,
        surface,
        levels: list[int] | np.ndarray,
        diagonal_balance: bool = True,
        finalize=False,
    ) -> TreeMesh:
        """
        Refine a tree mesh along the simplicies of a surface.

        :param mesh: Tree mesh to refine.
        :param surface: Surface object to use for refinement.
        :param levels: Number of cells requested at each refinement level.
            Defined in reversed order from highest octree to lowest.
        :param diagonal_balance: Whether to balance cells along the diagonal of
            the tree during construction.
        :param finalize: Finalize the tree mesh after refinement.

        :return: Refined tree mesh.
        """
        if not isinstance(surface, Surface):
            raise TypeError("Refinement object must be a Surface.")

        if surface.vertices is None or surface.cells is None:
            raise ValueError("Surface object must have vertices and cells.")

        if isinstance(levels, list):
            levels = np.array(levels)

        vertices = surface.vertices.copy()
        normals = np.cross(
            vertices[surface.cells[:, 1], :] - vertices[surface.cells[:, 0], :],
            vertices[surface.cells[:, 2], :] - vertices[surface.cells[:, 0], :],
        )
        average_normals = np.zeros((surface.n_vertices, 3))

        for vert_ids in surface.cells.T:
            average_normals[vert_ids, :] += normals

        average_normals /= np.linalg.norm(average_normals, axis=1)[:, None]

        base_cells = np.r_[mesh.h[0][0], mesh.h[1][0], mesh.h[2][0]]
        for level, n_cells in enumerate(levels):
            if n_cells == 0:
                continue

            for _ in range(int(n_cells)):
                mesh.refine_surface(
                    (vertices, surface.cells),
                    level=-level - 1,
                    diagonal_balance=diagonal_balance,
                    finalize=False,
                )
                vertices -= average_normals * base_cells * 2.0**level

        if finalize:
            mesh.finalize()

        return mesh

    @staticmethod
    def cell_size_from_level(octree, level: int, axis: int = 0):
        """
        Computes the cell size at a given level of refinement for a given tree mesh.

        :param octree: Tree mesh to refine.
        :param level: Level of refinement.
        :param axis: Axis of refinement.

        :return: Cell size at the given level of refinement.
        """
        return octree.h[axis][0] * 2**level


if __name__ == "__main__":
    file = sys.argv[1]
    OctreeDriver.start(file)
