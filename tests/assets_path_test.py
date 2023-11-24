#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of octree_creation_app package.
#
#  All rights reserved.
#

from geoapps_utils.importing import assets_path

import octree_creation_app


def test_assets_directory_exist():
    assert assets_path(octree_creation_app.__assets_dir__).is_dir()


def test_uijson_files_exists():
    assert (assets_path(octree_creation_app.__assets_dir__) / "uijson").is_dir()
    assert list((assets_path(octree_creation_app.__assets_dir__) / "uijson").iterdir())[
        0
    ].is_file()
