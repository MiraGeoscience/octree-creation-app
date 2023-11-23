#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of octree_creation_app package.
#
#  All rights reserved.
#
import numpy as np
from discretize import TreeMesh
from geoh5py.objects import Octree


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
