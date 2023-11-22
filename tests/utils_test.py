#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of octree_creation_app package.
#
#  All rights reserved.
from pathlib import Path
from uuid import UUID

import numpy as np
from discretize import TreeMesh
from geoh5py import Workspace

from octree_creation_app.utils import treemesh_2_octree


class Geoh5Tester:
    """Create temp workspace, copy entities, and setup params class."""

    def __init__(self, geoh5, path, name, params_class=None):
        self.geoh5 = geoh5
        self.tmp_path = Path(path) / name
        self.ws = Workspace.create(self.tmp_path)

        if params_class is not None:
            self.params = params_class(validate=False, geoh5=self.ws)
            self.has_params = True
        else:
            self.has_params = False

    def copy_entity(self, uid):
        entity = self.ws.get_entity(uid)
        if not entity or entity[0] is None:
            return self.geoh5.get_entity(uid)[0].copy(parent=self.ws)
        return entity[0]

    def set_param(self, param, value):
        if self.has_params:
            try:
                uid = UUID(value)
                entity = self.copy_entity(uid)
                setattr(self.params, param, entity)
            except (AttributeError, ValueError):
                setattr(self.params, param, value)
        else:
            msg = "No params class has been initialized."
            raise ValueError(msg)

    def make(self):
        if self.has_params:
            return self.ws, self.params
        return self.ws


def test_treemesh_2_octree(tmp_path: Path):
    geotest = Geoh5Tester(geoh5, tmp_path, "test.geoh5")
    with geotest.make() as workspace:
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
