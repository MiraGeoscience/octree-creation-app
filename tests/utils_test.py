#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of octree_creation_app package.
#
#  All rights reserved.
from pathlib import Path

import numpy as np
from discretize import TreeMesh
from geoh5py import Workspace
from geoh5py.shared.utils import fetch_active_workspace

from octree_creation_app.utils import treemesh_2_octree


def test_treemesh_2_octree(tmp_path: Path):
    with fetch_active_workspace(
        Workspace(tmp_path / "testTreemesh2Octree.geoh5")
    ) as workspace:
        mesh = TreeMesh([[10] * 16, [10] * 4, [10] * 8], [0, 0, 0])
        mesh.insert_cells([10, 10, 10], mesh.max_level, finalize=True)
        omesh = treemesh_2_octree(workspace, mesh, name="test_mesh")
        assert omesh.n_cells == mesh.n_cells
        assert np.all(
            (omesh.centroids - mesh.cell_centers[getattr(mesh, "_ubc_order")]) < 1e-14
        )
        expected_refined_cells = [
            (0, 0, 6),
            (0, 0, 7),
            (1, 0, 6),
            (1, 0, 7),
            (0, 1, 6),
            (0, 1, 7),
            (1, 1, 6),
            (1, 1, 7),
        ]
        ijk_refined = omesh.octree_cells[["I", "J", "K"]][
            omesh.octree_cells["NCells"] == 1
        ].tolist()
        assert np.all([k in ijk_refined for k in expected_refined_cells])
        assert np.all([k in expected_refined_cells for k in ijk_refined])
