#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of octree-creation-app package.
#
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations


REFINEMENT_KEY = "refinement"

template_dict: dict[str, dict] = {
    "object": {
        "groupOptional": True,
        "enabled": False,
        "group": "Refinement A",
        "label": "Object",
        "meshType": [
            "{202c5db1-a56d-4004-9cad-baafd8899406}",
            "{6a057fdc-b355-11e3-95be-fd84a7ffcb88}",
            "{f26feba3-aded-494b-b9e9-b2bbcbe298e1}",
            "{b99bd6e5-4fe1-45a5-bd2f-75fc31f91b38}",
            "{0b639533-f35b-44d8-92a8-f70ecff3fd26}",
            "{9b08bb5a-300c-48fe-9007-d206f971ea92}",
            "{19730589-fd28-4649-9de0-ad47249d9aba}",
            "{b3a47539-0301-4b27-922e-1dde9d882c60}",
            "{a81c6b0a-f290-4bc8-b72d-60e59964bfe8}",
            "{41018a45-01a0-4c61-a7cb-9f32d8159df4}",
            "{deebe11a-b57b-4a03-99d6-8f27b25eb2a8}",
            "{275ecee9-9c24-4378-bf94-65f3c5fbe163}",
        ],
        "value": None,
        "tooltip": "Object used to refine the mesh. Refinement strategy varies "
        "depending on the object type. See documentation for details.",
    },
    "levels": {
        "enabled": True,
        "group": "Refinement A",
        "label": "Levels",
        "value": "4, 4, 4",
        "tooltip": "Number of consecutive cells requested at each octree level. "
        "See documentation for details.",
    },
    "horizon": {
        "enabled": True,
        "group": "Refinement A",
        "label": "Use as horizon",
        "tooltip": "Object vertices are triangulated. Refinement levels are "
        "applied as depth layers.",
        "value": False,
    },
    "distance": {
        "enabled": False,
        "group": "Refinement A",
        "dependency": "horizon",
        "dependencyType": "enabled",
        "label": "Distance",
        "tooltip": "Radial horizontal distance to extend the refinement "
        "around each vertex.",
        "value": 1000.0,
    },
}
