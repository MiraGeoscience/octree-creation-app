# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2025 Mira Geoscience Ltd.                                          '
#                                                                                        '
#  This file is part of octree-creation-app package.                                     '
#                                                                                        '
#  octree-creation-app is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                           '
#                                                                                        '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from discretize import TreeMesh
from geoh5py.objects import (
    CurrentElectrode,
    Curve,
    Octree,
    Points,
    PotentialElectrode,
    Surface,
)
from geoh5py.shared.utils import compare_entities
from geoh5py.ui_json.utils import str2list
from geoh5py.workspace import Workspace
from scipy.spatial import Delaunay

from octree_creation_app.driver import OctreeDriver
from octree_creation_app.params import OctreeParams
from octree_creation_app.utils import octree_2_treemesh, treemesh_2_octree


# pylint: disable=redefined-outer-name, duplicate-code


def test_create_octree_radial(tmp_path: Path, setup_test_octree):  # pylint: disable=too-many-locals
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
            "minimum_level": minimum_level,
            "refinements": [
                {
                    "refinement_object": points,
                    "levels": refinement,
                    "horizon": False,
                }
            ],
        }
        params = OctreeParams(**params_dict)
        params.write_ui_json(tmp_path / "testOctree.ui.json")
        # params.write_input_file(name="testOctree", path=tmp_path, validate=False)
        driver = OctreeDriver(params)
        driver.run()

        rec_octree = workspace.get_entity("Octree_Mesh")[0]
        compare_entities(octree, rec_octree, ignore=["_uid"])


def test_create_octree_surface(tmp_path: Path, setup_test_octree):  # pylint: disable=too-many-locals
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
            "minimum_level": minimum_level,
            "refinements": [
                {
                    "refinement_object": surface,
                    "levels": refinement,
                    "horizon": True,
                    "distance": 1000.0,
                }
            ],
        }
        params = OctreeParams(**params_dict)
        params.write_ui_json(tmp_path / "testOctree.ui.json")
        driver = OctreeDriver(params)
        driver.run()

        rec_octree = workspace.get_entity("Octree_Mesh")[0]
        compare_entities(octree, rec_octree, ignore=["_uid"])


def test_create_octree_surface_straight_line(tmp_path: Path, setup_test_octree):
    _, _, _, _, _, refinement, treemesh, _ = setup_test_octree

    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        locs = np.c_[np.linspace(-50, 50, 21), np.zeros(21), np.zeros(21)]

        pts = Points.create(workspace, vertices=locs)
        treemesh = OctreeDriver.refine_by_object_type(
            treemesh,
            pts,
            str2list(refinement),
            horizon=True,
            distance=None,
            diagonal_balance=False,
        )
        treemesh.finalize()
        treemesh_2_octree(workspace, treemesh, name="Octree_Mesh")
        strip = workspace.get_entity("Surface strip")[0]
        assert np.allclose(strip.extent, [[-60, -10, 0], [60, 10, 0]])


def test_create_octree_curve(tmp_path: Path, setup_test_octree):  # pylint: disable=too-many-locals
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
        curve = Curve.create(workspace, vertices=locations)
        curve.remove_cells([-1])

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
            "minimum_level": minimum_level,
            "refinements": [
                {
                    "refinement_object": curve,
                    "levels": refinement,
                }
            ],
        }
        params = OctreeParams(**params_dict)
        params.write_ui_json(tmp_path / "testOctree.ui.json")
        driver = OctreeDriver(params)
        driver.run()

        results = driver.params.geoh5.get_entity("Octree_Mesh")
        assert results[0].n_cells == 177230


def test_create_octree_empty_curve(tmp_path: Path, setup_test_octree):  # pylint: disable=too-many-locals
    (
        cell_sizes,
        depth_core,
        horizontal_padding,
        locations,
        _,
        refinement,
        _,
        vertical_padding,
    ) = setup_test_octree

    with Workspace.create(tmp_path / "testOctree.geoh5") as workspace:
        # Create sources along line
        extent = Points.create(workspace, vertices=locations)
        curve = Curve.create(workspace)
        curve.remove_cells([0])

        params_dict = {
            "geoh5": workspace,
            "objects": extent,
            "u_cell_size": cell_sizes[0],
            "v_cell_size": cell_sizes[1],
            "w_cell_size": cell_sizes[2],
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": depth_core,
            "diagonal_balance": False,
            "minimum_level": 10,
            "refinements": [
                {
                    "refinement_object": curve,
                    "levels": refinement,
                }
            ],
        }
        params = OctreeParams(**params_dict)
        params.write_ui_json(tmp_path / "testOctree.ui.json")
        driver = OctreeDriver(params)
        driver.run()

        results = driver.params.geoh5.get_entity("Octree_Mesh")[0]
        assert isinstance(results, Octree)
        assert results.n_cells == 4


def test_create_octree_dipoles(tmp_path: Path, setup_test_octree):  # pylint: disable=too-many-locals
    (
        cell_sizes,
        depth_core,
        horizontal_padding,
        _,
        minimum_level,
        refinement,
        _,
        vertical_padding,
    ) = setup_test_octree

    n_data = 12
    with Workspace.create(tmp_path / "testOctree.geoh5") as workspace:
        # Create sources along line
        x_loc, y_loc = np.meshgrid(np.arange(n_data), np.arange(-1, 3))
        vertices = np.c_[x_loc.ravel(), y_loc.ravel(), np.zeros_like(x_loc).ravel()]
        parts = np.kron(np.arange(4), np.ones(n_data)).astype("int")
        currents = CurrentElectrode.create(workspace, vertices=vertices, parts=parts)
        currents.add_default_ab_cell_id()

        n_dipoles = 9
        dipoles = []
        current_id = []
        for val in currents.ab_cell_id.values:
            cell_id = int(currents.ab_map[val]) - 1

            for dipole in range(n_dipoles):
                dipole_ids = currents.cells[cell_id, :] + 2 + dipole

                if (
                    any(dipole_ids > (len(vertices) - 1))
                    or len(np.unique(parts[dipole_ids])) > 1
                ):
                    continue

                dipoles += [dipole_ids]
                current_id += [val]

        potentials = PotentialElectrode.create(
            workspace,
            vertices=vertices,
            cells=np.vstack(dipoles).astype("uint32"),
            ab_cell_id=np.hstack(current_id).astype("int32"),
        )

        params_dict = {
            "geoh5": workspace,
            "objects": potentials,
            "u_cell_size": cell_sizes[0],
            "v_cell_size": cell_sizes[1],
            "w_cell_size": cell_sizes[2],
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": depth_core,
            "diagonal_balance": False,
            "minimum_level": minimum_level,
            "refinements": [
                {
                    "refinement_object": potentials,
                    "levels": refinement,
                }
            ],
        }
        params = OctreeParams(**params_dict)
        params.write_ui_json(tmp_path / "testOctree.ui.json")
        driver = OctreeDriver(params)
        driver.run()

        assert driver.params.geoh5.get_entity("Octree_Mesh")[0]


def test_create_octree_triangulation(tmp_path: Path, setup_test_octree):  # pylint: disable=too-many-locals
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
            "minimum_level": minimum_level,
            "refinements": [
                {
                    "refinement_object": sphere,
                    "levels": refinement,
                }
            ],
        }
        params = OctreeParams(**params_dict)
        params.write_ui_json(tmp_path / "testOctree.ui.json")
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
        point = [125, 0, 125]
        points = Points.create(
            workspace, vertices=np.array([[150, 0, 150], [200, 0, 200], point])
        )

        # Repeat the creation using the app
        params_dict = {
            "geoh5": workspace,
            "objects": points,
            "u_cell_size": 10.0,
            "v_cell_size": 10.0,
            "w_cell_size": 10.0,
            "horizontal_padding": 500.0,
            "vertical_padding": 200.0,
            "depth_core": 400.0,
            "minimum_level": 4,
            "refinements": [
                {
                    "refinement_object": points,
                    "levels": 1,
                    "horizon": False,
                    "distance": 1000.0,
                }
            ],
        }

        params = OctreeParams(**params_dict, diagonal_balance=diagonal_balance)
        # driver = OctreeDriver(params)
        # driver.run()
        filename = "diag_balance.ui.json"

        params.write_ui_json(tmp_path / filename)

    OctreeDriver.start(tmp_path / filename)

    with workspace.open(mode="r"):
        results = []
        mesh_obj = workspace.get_entity("Octree_Mesh")[0]

        assert isinstance(mesh_obj, Octree)

        treemesh = octree_2_treemesh(mesh_obj)
        assert treemesh is not None

        ind = treemesh.get_containing_cells(  # pylint: disable=protected-access
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
                            level - compare_cell._level  # pylint: disable=protected-access
                        )
                    )

        values, counts = np.unique(results, return_counts=True)

        assert (values == np.array(exp_values)).all()
        assert (counts == np.array(exp_counts)).all()


def test_refine_complement(tmp_path: Path, setup_test_octree):  # pylint: disable=too-many-locals
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
        points.complement = curve

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
            "minimum_level": minimum_level,
            "refinements": [
                {
                    "refinement_object": curve,
                    "levels": refinement,
                    "horizon": False,
                }
            ],
        }
        params = OctreeParams(**params_dict)
        params.write_ui_json(tmp_path / "testOctree.ui.json")
        driver = OctreeDriver(params)
        driver.run()

        rec_octree = workspace.get_entity("Octree_Mesh")[0]
        treemesh = octree_2_treemesh(rec_octree)
        assert isinstance(treemesh, TreeMesh)

        # center of curve should be refined because of point complement
        ind = treemesh.get_containing_cells(  # pylint: disable=protected-access
            np.array([[0.0, 0.0, 0.0]])
        )
        assert all(k == 5 for k in treemesh[ind].h)
        # between curve and point complement should be > base cell size
        ind = treemesh.get_containing_cells(  # pylint: disable=protected-access
            np.array([[100.0, 0.0, 0.0]])
        )
        assert all(k == 20 for k in treemesh[ind].h)
        # along curve path should be base cell size
        point = np.mean(locations[1:3, :], axis=0)
        ind = treemesh.get_containing_cells(  # pylint: disable=protected-access
            point
        )
        assert all(k == 5 for k in treemesh[ind].h)


def test_regular_grid(tmp_path: Path, setup_test_octree):  # pylint: disable=too-many-locals
    (
        cell_sizes,
        depth_core,
        horizontal_padding,
        _,
        minimum_level,
        refinement,
        treemesh,
        vertical_padding,
    ) = setup_test_octree

    x, y = np.meshgrid(
        np.arange(0, 100, 5) + np.random.randn(1),
        np.arange(0, 100, 5) + np.random.randn(1),
    )
    locations = np.c_[x.flatten(), y.flatten(), np.ones(400) * np.random.randn(1)]

    with Workspace.create(tmp_path / "testOctree.geoh5") as workspace:
        points = Points.create(workspace, vertices=locations)

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
            "minimum_level": minimum_level,
            "refinements": [
                {
                    "refinement_object": points,
                    "levels": refinement,
                    "horizon": False,
                }
            ],
        }
        params = OctreeParams(**params_dict)
        params.write_ui_json(tmp_path / "testOctree.ui.json")
        driver = OctreeDriver(params)
        driver.run()

        rec_octree = workspace.get_entity("Octree_Mesh")[0]

        treemesh = octree_2_treemesh(rec_octree)

    # center of curve should be refined because of point complement
    ind = treemesh.get_containing_cells(  # pylint: disable=protected-access
        locations
    )

    np.testing.assert_allclose(treemesh.cell_centers[ind], locations)
