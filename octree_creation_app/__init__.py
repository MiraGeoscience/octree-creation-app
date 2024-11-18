#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of octree-creation-app package.
#
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

from pathlib import Path

from geoapps_utils.utils.importing import assets_path as assets_path_impl


__version__ = "0.2.0-beta.1"


def assets_path() -> Path:
    """Return the path to the assets folder."""

    return assets_path_impl(__file__)
