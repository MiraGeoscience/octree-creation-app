#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of octree_creation_app package.
#
#  All rights reserved.
#
from __future__ import annotations

from logging import warning

import discretize
import numpy as np
from discretize import TreeMesh
from geoh5py import Workspace
from geoh5py.objects import Curve, Octree
from geoh5py.shared.utils import fetch_active_workspace
from scipy.interpolate import interp1d
from scipy.spatial import cKDTree


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
        if dimensions is not None and cell_size is not None:
            extent = dimensions[ind]
            max_level = int(np.ceil(np.log2(extent / cell_size[ind])))
            cells += [np.ones(2**max_level) * cell_size[ind]]

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

    if global_mesh.octree_cells is not None:
        u_grid = global_mesh.octree_cells["I"] * global_mesh.u_cell_size
        v_grid = global_mesh.octree_cells["J"] * global_mesh.v_cell_size
        w_grid = global_mesh.octree_cells["K"] * global_mesh.w_cell_size

    xyz = np.c_[u_grid, v_grid, w_grid] + attributes["origin"]
    tree = cKDTree(xyz)

    for local_mesh in local_meshes:
        attributes = get_octree_attributes(local_mesh)

        if cell_size and cell_size != attributes["cell_size"]:
            raise ValueError(
                f"Cell size mismatch in dimension {cell_size} != {attributes['cell_size']}"
            )

        _, closest = tree.query(attributes["origin"])
        shift = xyz[closest, :] - attributes["origin"]

        if np.any(shift != 0.0):
            with fetch_active_workspace(local_mesh.workspace) as workspace:
                warning(
                    f"Shifting {local_mesh.name} mesh origin by {shift} m to match inversion mesh."
                )
                local_mesh.origin = attributes["origin"] + shift
                workspace.update_attribute(local_mesh, "attributes")


def densify_curve(curve: Curve, increment: float) -> np.ndarray:
    """
    Refine a curve by adding points along the curve at a given increment.

    :param curve: Curve object to be refined.
    :param increment: Distance between points along the curve.

    :return: Array of shape (n, 3) of x, y, z locations.
    """
    locations = []
    for part in curve.unique_parts:
        if curve.cells is not None and curve.vertices is not None:
            logic = curve.parts == part
            cells = curve.cells[np.all(logic[curve.cells], axis=1)]
            vert_ind = np.r_[cells[:, 0], cells[-1, 1]]
            locs = curve.vertices[vert_ind, :]
            locations.append(resample_locations(locs, increment))

    return np.vstack(locations)


def get_neighbouring_cells(mesh: TreeMesh, indices: list | np.ndarray) -> tuple:
    """
    Get the indices of neighbouring cells along a given axis for a given list of
    cell indices.

    :param mesh: discretize.TreeMesh object.
    :param indices: List of cell indices.

    :return: Two lists of neighbouring cell indices for every axis.
        axis[0] = (west, east)
        axis[1] = (south, north)
        axis[2] = (down, up)
    """
    if not isinstance(indices, (list, np.ndarray)):
        raise TypeError("Input 'indices' must be a list or numpy.ndarray of indices.")

    if not isinstance(mesh, TreeMesh):
        raise TypeError("Input 'mesh' must be a discretize.TreeMesh object.")

    neighbors: dict[int, list] = {ax: [[], []] for ax in range(mesh.dim)}

    for ind in indices:
        for ax in range(mesh.dim):
            neighbors[ax][0].append(np.r_[mesh[ind].neighbors[ax * 2]])
            neighbors[ax][1].append(np.r_[mesh[ind].neighbors[ax * 2 + 1]])

    return tuple(
        (np.r_[tuple(neighbors[ax][0])], np.r_[tuple(neighbors[ax][1])])
        for ax in range(mesh.dim)
    )


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


def octree_2_treemesh(  # pylint: disable=too-many-locals
    mesh: Octree,
) -> discretize.TreeMesh:
    """
    Convert a geoh5 octree mesh to discretize.TreeMesh

    Modified code from module discretize.TreeMesh.readUBC function.

    :param mesh: Octree mesh to convert.

    :return: Resulting TreeMesh.
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
    if mesh.octree_cells is None:
        return None
    cells = np.vstack(mesh.octree_cells.tolist())
    levels = cells[:, -1]
    array_ind = cells[:, :-1]
    array_ind = 2 * array_ind + levels[:, None]  # get cell center index
    if n_cell_dim[2] is None:
        return None
    array_ind[:, 2] = 2 * n_cell_dim[2] - array_ind[:, 2]  # switch direction of iz
    levels = max_level - np.log2(levels)  # calculate level

    treemesh.__setstate__((array_ind, levels))

    return treemesh


def resample_locations(locations: np.ndarray, increment: float) -> np.ndarray:
    """
    Resample locations along a sequence of positions at a given increment.

    :param locations: Array of shape (n, 3) of x, y, z locations.
    :param increment: Minimum distance between points along the curve.

    :return: Array of shape (n, 3) of x, y, z locations.
    """
    distance = np.cumsum(
        np.r_[0, np.linalg.norm(locations[1:, :] - locations[:-1, :], axis=1)]
    )
    new_distances = np.sort(
        np.unique(np.r_[distance, np.arange(0, distance[-1], increment)])
    )

    resampled = []
    for axis in locations.T:
        interpolator = interp1d(distance, axis, kind="linear")
        resampled.append(interpolator(new_distances))

    return np.c_[resampled].T


def treemesh_2_octree(
    workspace: Workspace, treemesh: discretize.TreeMesh, **kwargs
) -> Octree:
    """
    Converts a :obj:`discretize.TreeMesh` to :obj:`geoh5py.objects.Octree` entity.

    :param workspace: Workspace to create the octree in.
    :param treemesh: TreeMesh to convert.

    :return: Octree entity.
    """
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
