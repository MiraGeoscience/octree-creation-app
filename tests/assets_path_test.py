# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2025 Mira Geoscience Ltd.                                '
#                                                                              '
#  This file is part of octree-creation-app package.                           '
#                                                                              '
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).                 '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from octree_creation_app import assets_path


def test_assets_directory_exist():
    assert assets_path().is_dir()


def test_uijson_files_exists():
    assert (assets_path() / "uijson").is_dir()
    assert list((assets_path() / "uijson").iterdir())[0].is_file()
