#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of octree-creation-app package.
#
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

from pathlib import Path
from types import GenericAlias
from typing import Any, ClassVar

import numpy as np
from geoapps_utils.driver.data import BaseData
from geoh5py.objects import Points
from geoh5py.ui_json import InputFile
from pydantic import BaseModel, ConfigDict
from typing_extensions import Self

from octree_creation_app import assets_path


defaults_ifile = InputFile.read_ui_json(
    assets_path() / "uijson/octree_mesh.ui.json", validate=False
)
default_ui_json = defaults_ifile.ui_json
defaults = defaults_ifile.data


class OctreeParams(BaseData):
    """
    Octree creation parameters.

    :param objects: Object used to define the core of the mesh.
    :param depth_core: Limit the depth of the core of the mesh.
    :param diagonal_balance: Whether to limit the cell size change
        to one level in the transition between diagonally adjacent
        cells.
    :param minimum_level: Provides a minimum level of refinement for
        the whole mesh to prevent excessive coarsenin in padding
        regions.
    :param u_cell_size: Cell size in the x-direction.
    :param v_cell_size: Cell size in the y-direction.
    :param w_cell_size: Cell size in the z-direction.
    :param horizontal_padding: Padding in the x and y directions.
    :param vertical_padding: Padding in the z direction.
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        extra="allow",
    )

    name: ClassVar[str] = "octree_mesh"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/octree_mesh.ui.json"
    title: ClassVar[str] = "Octree Mesh Creator"
    run_command: ClassVar[str] = "octree_creation_app.driver"

    conda_environment: str = "octree_creation_app"
    objects: Points
    depth_core: float
    diagonal_balance: bool
    minimum_level: int
    u_cell_size: float
    v_cell_size: float
    w_cell_size: float
    horizontal_padding: float
    vertical_padding: float
    refinements: list[dict[str, Any]] | None = None

    def get_padding(self) -> list:
        """
        Utility to get the padding values as a list of padding along each axis.
        """
        return [
            [
                self.horizontal_padding,
                self.horizontal_padding,
            ],
            [
                self.horizontal_padding,
                self.horizontal_padding,
            ],
            [self.vertical_padding, self.vertical_padding],
        ]

    @classmethod
    def build(cls, input_data: InputFile | dict) -> Self:
        """
        Build a dataclass from a dictionary or InputFile.

        :param input_data: Dictionary of parameters and values.

        :return: Dataclass of application parameters.
        """

        data = input_data

        if isinstance(input_data, InputFile) and input_data.data is not None:
            data = input_data.data.copy()

        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary or InputFile.")

        kwargs = OctreeParams.collect_input_from_dict(cls, data)  # type: ignore
        out = cls(**kwargs)
        if isinstance(input_data, InputFile):
            out._input_file = input_data

        return out

    @staticmethod
    def collect_input_from_dict(base_model: type[BaseModel], data: dict[str, Any]):
        """
        Recursively replace BaseModel objects with dictionary of 'data' values.

        :param base_model: BaseModel object holding data and possibly other nested
            BaseModel objects.
        :param data: Dictionary of parameters and values without nesting structure.
        """
        update = {}
        for field, info in base_model.model_fields.items():
            if (
                isinstance(info.annotation, type)
                and not isinstance(info.annotation, GenericAlias)
                and issubclass(info.annotation, BaseModel)
            ):
                update[field] = OctreeParams.collect_input_from_dict(
                    info.annotation,
                    data,  # type: ignore
                )
            else:
                if field in data:
                    update[field] = data.get(field, info.default)

        # update["refinements"] = OctreeParams._collect_refinements_from_dict(data)

        update.update(
            {"refinements": OctreeParams._collect_refinements_from_dict(data)}
        )
        return update

    @staticmethod
    def _collect_refinements_from_dict(data: dict) -> list[dict]:
        """Collect active refinement dictionaries from input dictionary."""

        refinements = []
        for identifier in OctreeParams._active_refinements(data):
            refinement_params = {}
            for param in ["object", "levels", "horizon", "distance"]:
                name = f"refinement_{param}" if param == "object" else param
                refinement_name = f"Refinement {identifier} {param}"
                refinement_params[name] = data.get(refinement_name, None)

            refinements.append(refinement_params)

        return refinements

    @staticmethod
    def _active_refinements(data: dict) -> list[str]:
        """Return identifiers for active refinements (object not none)."""
        refinements = [k for k in data if "Refinement" in k]
        active = [k for k in refinements if "object" in k and data[k] is not None]
        return np.unique([k.split(" ")[1] for k in active])


# class OctreeParams(BaseParams):  # pylint: disable=too-many-instance-attributes
#     """
#     Parameter class for octree mesh creation application.
#     """
#
#     def __init__(self, input_file=None, **kwargs):
#         self._default_ui_json = deepcopy(default_ui_json)
#         self._defaults = deepcopy(defaults)
#         self._free_parameter_keys = ["object", "levels", "horizon", "distance"]
#         self._free_parameter_identifier = REFINEMENT_KEY
#         self._objects = None
#         self._u_cell_size = None
#         self._v_cell_size = None
#         self._w_cell_size = None
#         self._diagonal_balance = None
#         self._minimum_level = None
#         self._horizontal_padding = None
#         self._vertical_padding = None
#         self._depth_core = None
#         self._ga_group_name = None
#         self._title = None
#
#         if input_file is None:
#             free_param_dict = {}
#             for key in kwargs:
#                 if (
#                     self._free_parameter_identifier in key.lower()
#                     and "object" in key.lower()
#                 ):
#                     group = key.replace("object", "").rstrip()
#                     free_param_dict[group] = deepcopy(template_dict)
#
#             ui_json = deepcopy(self._default_ui_json)
#             for group, forms in free_param_dict.items():
#                 for key, form in forms.items():
#                     form["group"] = group
#
#                     if "dependency" in form:
#                         form["dependency"] = group + f" {form['dependency']}"
#
#                     ui_json[f"{group} {key}"] = form
#
#                     self._defaults[f"{group} {key}"] = form["value"]
#
#             input_file = InputFile(
#                 ui_json=ui_json,
#                 validate=False,
#             )
#
#         super().__init__(input_file=input_file, **kwargs)
#
#     def update(self, params_dict: dict[str, Any]):
#         """
#         Update parameters with dictionary contents.
#
#         :param params_dict: Dictionary of parameters.
#         """
#
#         super().update(params_dict)
#         with fetch_active_workspace(self.geoh5):
#             for key, value in params_dict.items():
#                 if REFINEMENT_KEY in key.lower():
#                     setattr(self, key, value)
#
#     def get_padding(self) -> list:
#         """
#         Utility to get the padding values as a list of padding along each axis.
#         """
#         return [
#             [
#                 self.horizontal_padding,
#                 self.horizontal_padding,
#             ],
#             [
#                 self.horizontal_padding,
#                 self.horizontal_padding,
#             ],
#             [self.vertical_padding, self.vertical_padding],
#         ]
#
#     @property
#     def title(self):
#         return self._title
#
#     @title.setter
#     def title(self, val):
#         self.setter_validator("title", val)
#
#     @property
#     def objects(self):
#         return self._objects
#
#     @objects.setter
#     def objects(self, val):
#         self.setter_validator("objects", val, fun=self._uuid_promoter)
#
#     @property
#     def u_cell_size(self):
#         return self._u_cell_size
#
#     @u_cell_size.setter
#     def u_cell_size(self, val):
#         self.setter_validator("u_cell_size", val)
#
#     @property
#     def v_cell_size(self):
#         return self._v_cell_size
#
#     @v_cell_size.setter
#     def v_cell_size(self, val):
#         self.setter_validator("v_cell_size", val)
#
#     @property
#     def w_cell_size(self):
#         return self._w_cell_size
#
#     @w_cell_size.setter
#     def w_cell_size(self, val):
#         self.setter_validator("w_cell_size", val)
#
#     @property
#     def horizontal_padding(self):
#         return self._horizontal_padding
#
#     @horizontal_padding.setter
#     def horizontal_padding(self, val):
#         self.setter_validator("horizontal_padding", val)
#
#     @property
#     def vertical_padding(self):
#         return self._vertical_padding
#
#     @vertical_padding.setter
#     def vertical_padding(self, val):
#         self.setter_validator("vertical_padding", val)
#
#     @property
#     def depth_core(self):
#         return self._depth_core
#
#     @depth_core.setter
#     def depth_core(self, val):
#         self.setter_validator("depth_core", val)
#
#     @property
#     def diagonal_balance(self):
#         return self._diagonal_balance
#
#     @diagonal_balance.setter
#     def diagonal_balance(self, val):
#         self.setter_validator("diagonal_balance", val)
#
#     @property
#     def minimum_level(self):
#         return self._minimum_level
#
#     @minimum_level.setter
#     def minimum_level(self, val):
#         self.setter_validator("minimum_level", val)
#
#     @property
#     def ga_group_name(self):
#         return self._ga_group_name
#
#     @ga_group_name.setter
#     def ga_group_name(self, val):
#         self.setter_validator("ga_group_name", val)
#
#     @property
#     def input_file(self) -> InputFile | None:
#         """
#         An InputFile class holding the associated ui_json and validations.
#         """
#         return self._input_file
#
#     @input_file.setter
#     def input_file(self, ifile: InputFile | None):
#         if not isinstance(ifile, (type(None), InputFile)):
#             raise TypeError(
#                 f"Value for 'input_file' must be {InputFile} or None. "
#                 f"Provided {ifile} of type{type(ifile)}"
#             )
#
#         if ifile is not None:
#             ifile = self.deprecation_update(ifile)
#             self.validator = ifile.validators
#             self.validations = ifile.validations
#
#         self._input_file = ifile
#
#     @classmethod
#     def deprecation_update(cls, ifile: InputFile) -> InputFile:
#         """
#         Update the input file to the latest version of the ui_json.
#         """
#
#         json_dict = {}
#
#         if ifile.ui_json is None or not any("type" in key for key in ifile.ui_json):
#             return ifile
#
#         key_swap = "Refinement horizon"
#         for key, form in ifile.ui_json.items():
#             if "type" in key:
#                 key_swap = form["group"] + " horizon"
#                 is_horizon = form.get("value")
#                 logic = is_horizon == "surface"
#                 msg = (
#                     f"Old refinement format 'type'='{is_horizon}' is deprecated. "
#                     f" Input type {'surface' if logic else 'radial'} will be interpreted as "
#                     f"'is_horizon'={logic}."
#                 )
#                 warn(msg, FutureWarning)
#                 json_dict[key_swap] = template_dict["horizon"].copy()
#                 json_dict[key_swap]["value"] = logic
#                 json_dict[key_swap]["group"] = form["group"]
#
#             elif "distance" in key:
#                 json_dict[key] = template_dict["distance"].copy()
#                 json_dict[key]["dependency"] = key_swap
#                 json_dict[key]["enabled"] = json_dict[key_swap]["value"]
#             else:
#                 json_dict[key] = form
#
#         input_file = InputFile(ui_json=json_dict, validate=False)
#
#         if ifile.path is not None and ifile.name is not None:
#             input_file.write_ui_json(name="[Updated]" + ifile.name, path=ifile.path)
#
#         return input_file
