# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2025 Mira Geoscience Ltd.                                          '
#                                                                                        '
#  This file is part of octree-creation-app package.                                     '
#                                                                                        '
#  octree-creation-app is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                           '
#                                                                                        '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
import numpy as np
import pytest
from discretize.utils import mesh_builder_xyz


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
