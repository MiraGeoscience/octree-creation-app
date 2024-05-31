#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of octree-creation-app package.
#
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

template_dict: dict[str, dict] = {
    "object": {
        "groupOptional": True,
        "enabled": False,
        "group": "Refinement A",
        "label": "Object",
        "meshType": [
            "{202C5DB1-A56D-4004-9CAD-BAAFD8899406}",
            "{6A057FDC-B355-11E3-95BE-FD84A7FFCB88}",
            "{F26FEBA3-ADED-494B-B9E9-B2BBCBE298E1}",
            "{b99bd6e5-4fe1-45a5-bd2f-75fc31f91b38}",
            "{0b639533-f35b-44d8-92a8-f70ecff3fd26}",
            "{9b08bb5a-300c-48fe-9007-d206f971ea92}",
            "{19730589-fd28-4649-9de0-ad47249d9aba}",
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
