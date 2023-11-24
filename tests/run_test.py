#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of octree_creation_app package.
#
#  All rights reserved.

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from discretize.utils import mesh_builder_xyz
from geoh5py.objects import Curve, Octree, Points, Surface
from geoh5py.shared.utils import compare_entities
from geoh5py.ui_json.utils import str2list
from geoh5py.workspace import Workspace
from scipy.spatial._qhull import Delaunay

from octree_creation_app.driver import OctreeDriver
from octree_creation_app.params import OctreeParams
from octree_creation_app.utils import octree_2_treemesh, treemesh_2_octree

# pylint: disable=redefined-outer-name


@pytest.fixture
def setup_test_octree():
    """
    Create a circle of points and treemesh from extent.
    """
    refinement = "4, 4"
    minimum_level = 4
    cell_sizes = [5.0, 5.0, 5.0]
    n_data = 16
    degree = np.linspace(0, 2 * np.pi, n_data)
    locations = np.c_[
        np.cos(degree) * 200.0, np.sin(degree) * 200.0, np.sin(degree * 2.0) * 40.0
    ]
    # Add point at origin
    locations = np.r_[locations, np.zeros((1, 3))]
    depth_core = 400.0
    horizontal_padding = 500.0
    vertical_padding = 200.0
    paddings = [
        [horizontal_padding, horizontal_padding],
        [horizontal_padding, horizontal_padding],
        [vertical_padding, vertical_padding],
    ]
    # Create a tree mesh from discretize
    treemesh = mesh_builder_xyz(
        locations,
        cell_sizes,
        padding_distance=paddings,
        mesh_type="tree",
        depth_core=depth_core,
    )

    return (
        cell_sizes,
        depth_core,
        horizontal_padding,
        locations,
        minimum_level,
        refinement,
        treemesh,
        vertical_padding,
    )


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
            "Refinement A type": "radial",
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree.json", path=tmp_path, validate=False)
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
        points = Points.create(workspace, vertices=locations)
        treemesh.refine(
            treemesh.max_level - minimum_level + 1,
            diagonal_balance=False,
            finalize=False,
        )
        treemesh = OctreeDriver.refine_tree_from_surface(
            treemesh,
            points,
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
            "objects": points,
            "u_cell_size": cell_sizes[0],
            "v_cell_size": cell_sizes[1],
            "w_cell_size": cell_sizes[2],
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": depth_core,
            "diagonal_balance": False,
            "Refinement A object": points,
            "Refinement A levels": refinement,
            "Refinement A type": "surface",
            "Refinement A distance": 1000.0,
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree.json", path=tmp_path, validate=False)
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
            "Refinement A type": "radial",
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree.json", path=tmp_path, validate=False)
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
            str2list(refinement),
            diagonal_balance=False,
            finalize=True,
        )
        octree = treemesh_2_octree(workspace, treemesh, name="Octree_Mesh")

        assert octree.n_cells == 293892

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
            "Refinement A type": "surface",
            "Refinement B object": None,
            "minimum_level": minimum_level,
        }
        params = OctreeParams(**params_dict)
        params.write_input_file(name="testOctree.json", path=tmp_path, validate=False)
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
            "Refinement A type": "radial",
            "Refinement A distance": 200,
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
        if not isinstance(mesh_obj, Octree):
            pytest.fail("Mesh is None")
        treemesh = octree_2_treemesh(mesh_obj)  # type: ignore

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
