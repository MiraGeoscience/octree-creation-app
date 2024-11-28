#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of octree-creation-app package.
#
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Points
from geoh5py.ui_json import InputFile

from octree_creation_app import assets_path
from octree_creation_app.driver import OctreeDriver
from octree_creation_app.params import OctreeParams


# pylint: disable=protected-access
def test_collect_refinements_from_dict():
    data = {
        "Not a refinement": "ignore me",
        "Refinement A object": "I am not None. Collect me.",
        "Refinement A levels": [4, 2],
        "Refinement A horizon": False,
        "Refinement A distance": 1000,
        "Refinement B object": None,
        "Refinement B levels": [4, 2],
        "Refinement B horizon": False,
        "Refinement B distance": 1000,
    }
    refinements = OctreeParams._collect_refinements_from_dict(data)
    assert len(refinements) == 1
    assert all(
        k in refinements[0]
        for k in ["refinement_object", "levels", "horizon", "distance"]
    )

    # Test handling of missing params, should return full refinement
    # dictionary with None values

    data = {
        "Refinement A object": "I am not None. Collect me.",
    }
    refinements = OctreeParams._collect_refinements_from_dict(data)
    assert len(refinements) == 1
    assert all(
        k in refinements[0]
        for k in ["refinement_object", "levels", "horizon", "distance"]
    )
    assert all(refinements[0][k] is None for k in ["levels", "horizon", "distance"])


def test_active_refinements():
    data = {
        "Not a refinement": "ignore me",
        "Refinement A object": "I am not None. Collect me.",
        "Refinement A levels": [4, 2],
        "Refinement A horizon": False,
        "Refinement A distance": 1000,
        "Refinement B object": None,
        "Refinement B levels": [4, 2],
        "Refinement B horizon": False,
        "Refinement B distance": 1000,
    }
    active = OctreeParams._active_refinements(data)
    assert active == ["A"]


def test_params_from_dict(tmp_path):
    ws = Workspace(tmp_path / "test.geoh5")
    points = Points.create(ws, name="test", vertices=np.random.rand(100, 3))

    kwargs = {
        "geoh5": ws,
        "objects": points,
        "refinements": [{"refinement_object": points}],
    }
    params = OctreeParams(**kwargs)
    assert params.geoh5 == ws
    assert params.objects == points
    assert params.refinements is not None
    refinement = params.refinements[0]  # pylint: disable=unsubscriptable-object
    assert refinement.refinement_object == points
    assert refinement.levels == [4, 2]
    assert refinement.horizon is False
    assert refinement.distance == np.inf


def test_refinement_serializer(tmp_path):
    ws = Workspace(tmp_path / "test.geoh5")
    points = Points.create(ws, name="test", vertices=np.random.rand(100, 3))

    kwargs = {
        "geoh5": ws,
        "objects": points,
        "refinements": [
            {
                "refinement_object": points,
                "levels": [4, 4, 4],
                "horizon": False,
                "distance": 200,
            },
            {
                "refinement_object": points,
                "horizon": True,
            },
        ],
    }
    params = OctreeParams(**kwargs)
    dump = params.model_dump()
    assert dump["geoh5"] == ws
    assert dump["objects"] == points
    assert dump["Refinement A object"] == points
    assert dump["Refinement A levels"] == [4, 4, 4]
    assert not dump["Refinement A horizon"]
    assert dump["Refinement A distance"] == 200
    assert dump["Refinement B object"] == points
    assert dump["Refinement B levels"] == [4, 2]
    assert dump["Refinement B horizon"]
    assert dump["Refinement B distance"] == np.inf


def test_treemesh_from_params(tmp_path):
    ws = Workspace(tmp_path / "test.geoh5")
    points = Points.create(ws, name="test", vertices=np.random.rand(100, 3))
    uijson_path = assets_path() / "uijson/octree_mesh.ui.json"
    ifile = InputFile.read_ui_json(uijson_path, validate=False)
    ifile.update_ui_values(
        {
            "geoh5": ws,
            "objects": points,
            "Refinement A object": points,
            "Refinement A levels": [4, 2],
            "Refinement A horizon": False,
            "Refinement A distance": 1000,
        }
    )
    params = OctreeParams.build(ifile)
    mesh = OctreeDriver.octree_from_params(params)
    assert mesh.u_cell_size == 25.0
    assert mesh.v_cell_size == 25.0
    assert mesh.w_cell_size == 25.0
