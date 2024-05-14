#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of octree-creation-app package.
#
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from geoh5py.objects import Curve, Octree, Points, Surface
from geoh5py.shared.utils import compare_entities
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import str2list
from geoh5py.workspace import Workspace
from scipy.spatial import Delaunay

from octree_creation_app.driver import OctreeDriver
from octree_creation_app.params import OctreeParams
from octree_creation_app.utils import octree_2_treemesh, treemesh_2_octree

# pylint: disable=redefined-outer-name, duplicate-code


def test_create_octree_radial(
    tmp_path: Path, setup_test_octree
):  # pylint: disable=too-many-locals
    (
        cell_sizes,
        depth_core,
        horizontal_padding,
        locations,
        minimum_level,
        refinement,
        treemesh,
        vertical_padding,
    ) = setup_test_octree

    with Workspace.create(tmp_path / "testOctree.geoh5") as workspace:
        points = Points.create(workspace, vertices=locations)
        treemesh.refine(treemesh.max_level - minimum_level + 1, finalize=False)
        treemesh = OctreeDriver.refine_tree_from_points(
            treemesh,
            points,
            str2list(refinement),
            diagonal_balance=False,
            finalize=True,
        )
        octree = treemesh_2_octree(workspace, treemesh, name="Octree_Mesh")

        # Hard-wire the expected result
        assert octree.n_cells == 164742

        assert OctreeDriver.cell_size_from_level(treemesh, 1) == 10.0

        params_dict = {
            "geoh5": workspace,
            "objects": points,
            "u_cell_size": cell_sizes[0],
            "v_cell_size": cell_sizes[1],
            "w_cell_size": cell_sizes[2],
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": depth_core,
            "diagonal_balance": False,
            "Refinement A object": points.uid,
            "Refinement A levels": refinement,
            "Refinement A horizon": False,
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree", path=tmp_path, validate=False)
        driver = OctreeDriver(params)
        driver.run()

        rec_octree = workspace.get_entity("Octree_Mesh")[0]
        compare_entities(octree, rec_octree, ignore=["_uid"])


def test_create_octree_surface(
    tmp_path: Path, setup_test_octree
):  # pylint: disable=too-many-locals
    (
        cell_sizes,
        depth_core,
        horizontal_padding,
        locations,
        minimum_level,
        refinement,
        treemesh,
        vertical_padding,
    ) = setup_test_octree

    with Workspace.create(tmp_path / "testOctree.geoh5") as workspace:
        simplices = np.unique(
            np.random.randint(0, locations.shape[0] - 1, (locations.shape[0], 3)),
            axis=1,
        )

        surface = Surface.create(
            workspace,
            vertices=locations,
            cells=simplices,
        )

        treemesh.refine(
            treemesh.max_level - minimum_level + 1,
            diagonal_balance=False,
            finalize=False,
        )
        treemesh = OctreeDriver.refine_tree_from_surface(
            treemesh,
            surface,
            str2list(refinement),
            diagonal_balance=False,
            finalize=True,
        )

        octree = treemesh_2_octree(workspace, treemesh, name="Octree_Mesh")

        assert octree.n_cells in [
            168627,
            168396,
        ]  # Different results on Linux and Windows

        params_dict = {
            "geoh5": workspace,
            "objects": surface,
            "u_cell_size": cell_sizes[0],
            "v_cell_size": cell_sizes[1],
            "w_cell_size": cell_sizes[2],
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": depth_core,
            "diagonal_balance": False,
            "Refinement A object": surface,
            "Refinement A levels": refinement,
            "Refinement A horizon": True,
            "Refinement A distance": 1000.0,
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree", path=tmp_path, validate=False)
        driver = OctreeDriver(params)
        driver.run()

        rec_octree = workspace.get_entity("Octree_Mesh")[0]
        compare_entities(octree, rec_octree, ignore=["_uid"])


def test_create_octree_curve(
    tmp_path: Path, setup_test_octree
):  # pylint: disable=too-many-locals
    (
        cell_sizes,
        depth_core,
        horizontal_padding,
        locations,
        minimum_level,
        refinement,
        treemesh,
        vertical_padding,
    ) = setup_test_octree

    with Workspace.create(tmp_path / "testOctree.geoh5") as workspace:
        curve = Curve.create(workspace, vertices=locations)
        curve.remove_cells([-1])
        treemesh.refine(
            treemesh.max_level - minimum_level + 1,
            diagonal_balance=False,
            finalize=False,
        )
        treemesh = OctreeDriver.refine_tree_from_curve(
            treemesh,
            curve,
            str2list(refinement),
            diagonal_balance=False,
            finalize=True,
        )
        octree = treemesh_2_octree(workspace, treemesh, name="Octree_Mesh")
        assert octree.n_cells == 176915

        params_dict = {
            "geoh5": workspace,
            "objects": curve,
            "u_cell_size": cell_sizes[0],
            "v_cell_size": cell_sizes[1],
            "w_cell_size": cell_sizes[2],
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": depth_core,
            "diagonal_balance": False,
            "Refinement A object": curve,
            "Refinement A levels": refinement,
            "Refinement A horizon": False,
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree", path=tmp_path, validate=False)
        driver = OctreeDriver(params)
        driver.run()

        results = driver.params.geoh5.get_entity("Octree_Mesh")
        compare_entities(results[0], results[1], ignore=["_uid"])


def test_create_octree_triangulation(
    tmp_path: Path, setup_test_octree
):  # pylint: disable=too-many-locals
    (
        cell_sizes,
        depth_core,
        horizontal_padding,
        locations,
        minimum_level,
        refinement,
        treemesh,
        vertical_padding,
    ) = setup_test_octree

    # Generate a sphere of points
    phi, theta = np.meshgrid(
        np.linspace(-np.pi / 2.0, np.pi / 2.0, 32), np.linspace(-np.pi, np.pi, 32)
    )
    surf = Delaunay(np.c_[phi.flatten(), theta.flatten()])
    x = np.cos(phi) * np.cos(theta) * 200.0
    y = np.cos(phi) * np.sin(theta) * 200.0
    z = np.sin(phi) * 200.0
    # refinement = "1, 2"
    with Workspace.create(tmp_path / "testOctree.geoh5") as workspace:
        curve = Curve.create(workspace, vertices=locations)
        sphere = Surface.create(
            workspace,
            vertices=np.c_[x.flatten(), y.flatten(), z.flatten()],
            cells=surf.simplices,
        )
        treemesh.refine(
            treemesh.max_level - minimum_level + 1,
            diagonal_balance=False,
            finalize=False,
        )
        treemesh = OctreeDriver.refine_tree_from_triangulation(
            treemesh,
            sphere,
            [3, 3],
            diagonal_balance=False,
            finalize=True,
        )
        octree = treemesh_2_octree(workspace, treemesh, name="Octree_Mesh")

        assert octree.n_cells == 267957

        params_dict = {
            "geoh5": workspace,
            "objects": curve,
            "u_cell_size": cell_sizes[0],
            "v_cell_size": cell_sizes[1],
            "w_cell_size": cell_sizes[2],
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": depth_core,
            "diagonal_balance": False,
            "Refinement A object": sphere,
            "Refinement A levels": refinement,
            "Refinement A horizon": False,
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree", path=tmp_path, validate=False)
        driver = OctreeDriver(params)
        driver.run()

        rec_octree = workspace.get_entity("Octree_Mesh")[0]
        compare_entities(octree, rec_octree, ignore=["_uid"])


@pytest.mark.parametrize(
    "diagonal_balance, exp_values, exp_counts",
    [(True, [0, 1], [22, 10]), (False, [0, 1, 2], [22, 8, 2])],
)
def test_octree_diagonal_balance(  # pylint: disable=too-many-locals
    tmp_path: Path, diagonal_balance, exp_values, exp_counts
):
    workspace = Workspace.create(tmp_path / "testDiagonalBalance.geoh5")
    with workspace.open(mode="r+"):
        point = [0, 0, 0]
        points = Points.create(workspace, vertices=np.array([[150, 0, 150], point]))

        # Repeat the creation using the app
        params_dict = {
            "geoh5": workspace,
            "objects": str(points.uid),
            "u_cell_size": 10.0,
            "v_cell_size": 10.0,
            "w_cell_size": 10.0,
            "horizontal_padding": 500.0,
            "vertical_padding": 200.0,
            "depth_core": 400.0,
            "Refinement A object": points.uid,
            "Refinement A levels": "1",
            "Refinement A horizon": False,
        }

        params = OctreeParams(
            **params_dict, diagonal_balance=diagonal_balance, ga_group_name="mesh"
        )
        filename = "diag_balance.ui.json"

        params.write_input_file(name=filename, path=tmp_path, validate=False)

    OctreeDriver.start(tmp_path / filename)

    with workspace.open(mode="r"):
        results = []
        mesh_obj = workspace.get_entity("mesh")[0]

        assert isinstance(mesh_obj, Octree)

        treemesh = octree_2_treemesh(mesh_obj)
        assert treemesh is not None

        ind = treemesh._get_containing_cell_indexes(  # pylint: disable=protected-access
            point
        )
        starting_cell = treemesh[ind]

        level = starting_cell._level  # pylint: disable=protected-access
        for first_neighbor in starting_cell.neighbors:
            neighbors = []
            for neighbor in treemesh[first_neighbor].neighbors:
                if isinstance(neighbor, list):
                    neighbors += neighbor
                else:
                    neighbors.append(neighbor)

            for second_neighbor in neighbors:
                compare_cell = treemesh[second_neighbor]
                if set(starting_cell.nodes) & set(compare_cell.nodes):
                    results.append(
                        np.abs(
                            level
                            - compare_cell._level  # pylint: disable=protected-access
                        )
                    )

        values, counts = np.unique(results, return_counts=True)

        assert (values == np.array(exp_values)).all()
        assert (counts == np.array(exp_counts)).all()


def test_backward_compatible_type(tmp_path):
    workspace = Workspace.create(tmp_path / "testDiagonalBalance.geoh5")
    with workspace.open(mode="r+"):
        points = Points.create(workspace, vertices=np.random.randn(5, 3))

        # Repeat the creation using the app
        params_dict = {
            "geoh5": workspace,
            "objects": str(points.uid),
            "u_cell_size": 10.0,
            "v_cell_size": 10.0,
            "w_cell_size": 10.0,
            "horizontal_padding": 500.0,
            "vertical_padding": 200.0,
            "depth_core": 400.0,
            "Refinement A object": points.uid,
            "Refinement A levels": "1",
            "Refinement A horizon": False,
        }

        params = OctreeParams(**params_dict)
        filename = "old_version.ui.json"
        params.write_input_file(name=filename, path=tmp_path, validate=False)

    ifile = params.input_file
    assert isinstance(ifile, InputFile)
    assert ifile.ui_json is not None

    # Mock the old format
    horizon = ifile.ui_json["Refinement A horizon"].copy()
    horizon["choiceList"] = ["surface", "radial"]
    horizon["value"] = "surface"

    distance = ifile.ui_json["Refinement A distance"].copy()
    distance["enabled"] = True
    distance["value"] = 1.0
    del distance["dependency"]
    del distance["dependencyType"]
    del ifile.ui_json["Refinement A horizon"]
    del ifile.ui_json["Refinement A distance"]

    ifile.ui_json["Refinement A type"] = horizon
    ifile.ui_json["Refinement A distance"] = distance

    with open(tmp_path / filename, "w", encoding="utf-8") as file:
        json.dump(ifile.stringify(ifile.demote(ifile.ui_json)), file, indent=4)

    with pytest.warns(FutureWarning, match="Old refinement format"):
        OctreeDriver.start(tmp_path / filename)


def test_refine_complement(
    tmp_path: Path, setup_test_octree
):  # pylint: disable=too-many-locals
    (
        cell_sizes,
        depth_core,
        horizontal_padding,
        locations,
        minimum_level,
        refinement,
        _,
        vertical_padding,
    ) = setup_test_octree

    with Workspace.create(tmp_path / "testOctree.geoh5") as workspace:

        points = Points.create(workspace, vertices=np.c_[locations[-1, :]].T)
        curve = Curve.create(workspace, vertices=locations)
        curve.remove_cells([-1])
        curve.complement = points

        params_dict = {
            "geoh5": workspace,
            "objects": curve,
            "u_cell_size": cell_sizes[0],
            "v_cell_size": cell_sizes[1],
            "w_cell_size": cell_sizes[2],
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": depth_core,
            "diagonal_balance": False,
            "Refinement A object": curve.uid,
            "Refinement A levels": refinement,
            "Refinement A horizon": False,
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree", path=tmp_path, validate=False)
        driver = OctreeDriver(params)
        driver.run()

        rec_octree = workspace.get_entity("Octree_Mesh")[0]
        treemesh = octree_2_treemesh(rec_octree)

        # center of curve should be refined because of point complement
        ind = treemesh._get_containing_cell_indexes(np.array([[0.0, 0.0, 0.0]]))
        assert all(k == 5 for k in treemesh[ind].h)
        # between curve and point complement should be > base cell size
        ind = treemesh._get_containing_cell_indexes(np.array([[100.0, 0.0, 0.0]]))
        assert all(k == 20 for k in treemesh[ind].h)
        # along curve path should be base cell size
        point = np.mean(locations[1:3, :], axis=0)
        ind = treemesh._get_containing_cell_indexes(point)
        assert all(k == 5 for k in treemesh[ind].h)
