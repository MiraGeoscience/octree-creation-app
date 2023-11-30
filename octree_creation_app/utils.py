#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of octree_creation_app package.
#
#  All rights reserved.
#
from __future__ import annotations

from logging import warn

import numpy as np
from discretize import TreeMesh
from geoh5py.objects import Octree
from geoh5py.shared.utils import fetch_active_workspace
from scipy.spatial._ckdtree import cKDTree


def create_octree_from_octrees(meshes: list[Octree | TreeMesh]) -> TreeMesh:
    """
    Create an all encompassing octree mesh from a list of meshes.

    :param meshes: List of Octree or TreeMesh meshes.

    :return octree: A global Octree.
    """
    cell_size = []
    dimensions = None
    origin = None

    for mesh in meshes:
        attributes = get_octree_attributes(mesh)

        if dimensions is None:
            dimensions = attributes["dimensions"]
            origin = attributes["origin"]
        else:
            if not np.allclose(dimensions, attributes["dimensions"]):
                raise ValueError("Meshes must have same dimensions")

            if not np.allclose(origin, attributes["origin"]):
                raise ValueError("Meshes must have same origin")

        cell_size.append(attributes["cell_size"])

    cell_size = np.min(np.vstack(cell_size), axis=0)
    cells = []
    for ind in range(3):
        if dimensions is not None:
            extent = dimensions[ind]
            maxLevel = int(np.ceil(np.log2(extent / cell_size[ind])))
            cells += [np.ones(2**maxLevel) * cell_size[ind]]

    # Define the mesh and origin
    treemesh = TreeMesh(cells, origin=origin)

    for mesh in meshes:
        if mesh.octree_cells is None:
            continue
        if isinstance(mesh, Octree):
            centers = mesh.centroids
            levels = treemesh.max_level - np.log2(mesh.octree_cells["NCells"])
        else:
            centers = mesh.cell_centers
            levels = (
                treemesh.max_level
                - mesh.max_level
                + mesh.cell_levels_by_index(np.arange(mesh.nC))
            )

        treemesh.insert_cells(centers, levels, finalize=False)

    treemesh.finalize()

    return treemesh


def collocate_octrees(global_mesh: Octree, local_meshes: list[Octree]):
    """
    Collocate a list of octree meshes into a global octree mesh.

    :param global_mesh: Global octree mesh.
    :param local_meshes: List of local octree meshes.
    """
    attributes = get_octree_attributes(global_mesh)
    cell_size = attributes["cell_size"]
    if global_mesh.octree_cells is None:
        raise ValueError("Mesh octree cells must be defined.")
    u_grid = global_mesh.octree_cells["I"] * global_mesh.u_cell_size
    v_grid = global_mesh.octree_cells["J"] * global_mesh.v_cell_size
    w_grid = global_mesh.octree_cells["K"] * global_mesh.w_cell_size

    xyz = np.c_[u_grid, v_grid, w_grid] + attributes["origin"]
    tree = cKDTree(xyz)

    for local_mesh in local_meshes:
        attributes = get_octree_attributes(local_mesh)

        if cell_size and not cell_size == attributes["cell_size"]:
            raise ValueError(
                f"Cell size mismatch in dimension {cell_size} != {attributes['cell_size']}"
            )

        _, closest = tree.query(attributes["origin"])
        shift = xyz[closest, :] - attributes["origin"]

        if np.any(shift != 0.0):
            with fetch_active_workspace(local_mesh.workspace) as workspace:
                warn(
                    f"Shifting {local_mesh.name} mesh origin by {shift} m to match inversion mesh."
                )
                local_mesh.origin = attributes["origin"] + shift
                workspace.update_attribute(local_mesh, "attributes")


def get_octree_attributes(mesh: Octree | TreeMesh) -> dict[str, list]:
    """
    Get mesh attributes.

    :param mesh: Input Octree or TreeMesh object.
    :return mesh_attributes: Dictionary of mesh attributes.
    """
    if not isinstance(mesh, (Octree, TreeMesh)):
        raise TypeError(f"All meshes must be Octree or TreeMesh, not {type(mesh)}")

    cell_size = []
    cell_count = []
    dimensions = []
    if isinstance(mesh, TreeMesh):
        for int_dim in range(3):
            cell_size.append(mesh.h[int_dim][0])
            cell_count.append(mesh.h[int_dim].size)
            dimensions.append(mesh.h[int_dim].sum())
        origin = mesh.origin
    else:
        with fetch_active_workspace(mesh.workspace):
            for str_dim in "uvw":
                cell_size.append(np.abs(getattr(mesh, f"{str_dim}_cell_size")))
                cell_count.append(getattr(mesh, f"{str_dim}_count"))
                dimensions.append(
                    getattr(mesh, f"{str_dim}_cell_size")
                    * getattr(mesh, f"{str_dim}_count")
                )
            origin = np.r_[mesh.origin["x"], mesh.origin["y"], mesh.origin["z"]]

    extent = np.r_[origin, origin + np.r_[dimensions]]

    return {
        "cell_count": cell_count,
        "cell_size": cell_size,
        "dimensions": dimensions,
        "extent": extent,
        "origin": origin,
    }


def octree_2_treemesh(mesh):  # pylint: disable=too-many-locals
    """
    Convert a geoh5 octree mesh to discretize.TreeMesh
    Modified code from module discretize.TreeMesh.readUBC function.
    """
    tsw_corner = np.asarray(mesh.origin.tolist())
    small_cell = [mesh.u_cell_size, mesh.v_cell_size, mesh.w_cell_size]
    n_cell_dim = [mesh.u_count, mesh.v_count, mesh.w_count]
    cell_sizes = [np.ones(nr) * sz for nr, sz in zip(n_cell_dim, small_cell)]
    u_shift, v_shift, w_shift = (np.sum(h[h < 0]) for h in cell_sizes)
    h1, h2, h3 = (np.abs(h) for h in cell_sizes)
    x0 = tsw_corner + np.array([u_shift, v_shift, w_shift])
    ls = np.log2(n_cell_dim).astype(int)

    if ls[0] == ls[1] and ls[1] == ls[2]:
        max_level = ls[0]
    else:
        max_level = min(ls) + 1

    treemesh = TreeMesh([h1, h2, h3], x0=x0)

    # Convert array_ind to points in coordinates of underlying cpp tree
    # array_ind is ix, iy, iz(top-down) need it in ix, iy, iz (bottom-up)
    cells = np.vstack(mesh.octree_cells.tolist())
    levels = cells[:, -1]
    array_ind = cells[:, :-1]
    array_ind = 2 * array_ind + levels[:, None]  # get cell center index
    array_ind[:, 2] = 2 * n_cell_dim[2] - array_ind[:, 2]  # switch direction of iz
    levels = max_level - np.log2(levels)  # calculate level

    treemesh.__setstate__((array_ind, levels))

    return treemesh


def treemesh_2_octree(workspace, treemesh, **kwargs):
    index_array, levels = getattr(treemesh, "_ubc_indArr")
    ubc_order = getattr(treemesh, "_ubc_order")

    index_array = index_array[ubc_order] - 1
    levels = levels[ubc_order]

    origin = treemesh.x0.copy()
    origin[2] += treemesh.h[2].size * treemesh.h[2][0]
    mesh_object = Octree.create(
        workspace,
        origin=origin,
        u_count=treemesh.h[0].size,
        v_count=treemesh.h[1].size,
        w_count=treemesh.h[2].size,
        u_cell_size=treemesh.h[0][0],
        v_cell_size=treemesh.h[1][0],
        w_cell_size=-treemesh.h[2][0],
        octree_cells=np.c_[index_array, levels],
        **kwargs,
    )

    return mesh_object
