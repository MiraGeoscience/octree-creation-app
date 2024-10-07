#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of octree-creation-app package.
#
#  octree-creation-app is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

from copy import deepcopy
from typing import Any
from warnings import warn

from geoapps_utils.driver.params import BaseParams
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import fetch_active_workspace

from octree_creation_app import assets_path

from .constants import REFINEMENT_KEY, template_dict


defaults_ifile = InputFile.read_ui_json(
    assets_path() / "uijson/octree_mesh.ui.json", validate=False
)
default_ui_json = defaults_ifile.ui_json
defaults = defaults_ifile.data


class OctreeParams(BaseParams):  # pylint: disable=too-many-instance-attributes
    """
    Parameter class for octree mesh creation application.
    """

    def __init__(self, input_file=None, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._defaults = deepcopy(defaults)
        self._free_parameter_keys = ["object", "levels", "horizon", "distance"]
        self._free_parameter_identifier = REFINEMENT_KEY
        self._objects = None
        self._u_cell_size = None
        self._v_cell_size = None
        self._w_cell_size = None
        self._diagonal_balance = None
        self._minimum_level = None
        self._horizontal_padding = None
        self._vertical_padding = None
        self._depth_core = None
        self._ga_group_name = None
        self._title = None

        if input_file is None:
            free_param_dict = {}
            for key in kwargs:
                if (
                    self._free_parameter_identifier in key.lower()
                    and "object" in key.lower()
                ):
                    group = key.replace("object", "").rstrip()
                    free_param_dict[group] = deepcopy(template_dict)

            ui_json = deepcopy(self._default_ui_json)
            for group, forms in free_param_dict.items():
                for key, form in forms.items():
                    form["group"] = group

                    if "dependency" in form:
                        form["dependency"] = group + f" {form['dependency']}"

                    ui_json[f"{group} {key}"] = form

                    self._defaults[f"{group} {key}"] = form["value"]

            input_file = InputFile(
                ui_json=ui_json,
                validate=False,
            )

        super().__init__(input_file=input_file, **kwargs)

    def update(self, params_dict: dict[str, Any]):
        """
        Update parameters with dictionary contents.

        :param params_dict: Dictionary of parameters.
        """

        super().update(params_dict)
        with fetch_active_workspace(self.geoh5):
            for key, value in params_dict.items():
                if REFINEMENT_KEY in key.lower():
                    setattr(self, key, value)

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

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, val):
        self.setter_validator("title", val)

    @property
    def objects(self):
        return self._objects

    @objects.setter
    def objects(self, val):
        self.setter_validator("objects", val, fun=self._uuid_promoter)

    @property
    def u_cell_size(self):
        return self._u_cell_size

    @u_cell_size.setter
    def u_cell_size(self, val):
        self.setter_validator("u_cell_size", val)

    @property
    def v_cell_size(self):
        return self._v_cell_size

    @v_cell_size.setter
    def v_cell_size(self, val):
        self.setter_validator("v_cell_size", val)

    @property
    def w_cell_size(self):
        return self._w_cell_size

    @w_cell_size.setter
    def w_cell_size(self, val):
        self.setter_validator("w_cell_size", val)

    @property
    def horizontal_padding(self):
        return self._horizontal_padding

    @horizontal_padding.setter
    def horizontal_padding(self, val):
        self.setter_validator("horizontal_padding", val)

    @property
    def vertical_padding(self):
        return self._vertical_padding

    @vertical_padding.setter
    def vertical_padding(self, val):
        self.setter_validator("vertical_padding", val)

    @property
    def depth_core(self):
        return self._depth_core

    @depth_core.setter
    def depth_core(self, val):
        self.setter_validator("depth_core", val)

    @property
    def diagonal_balance(self):
        return self._diagonal_balance

    @diagonal_balance.setter
    def diagonal_balance(self, val):
        self.setter_validator("diagonal_balance", val)

    @property
    def minimum_level(self):
        return self._minimum_level

    @minimum_level.setter
    def minimum_level(self, val):
        self.setter_validator("minimum_level", val)

    @property
    def ga_group_name(self):
        return self._ga_group_name

    @ga_group_name.setter
    def ga_group_name(self, val):
        self.setter_validator("ga_group_name", val)

    @property
    def input_file(self) -> InputFile | None:
        """
        An InputFile class holding the associated ui_json and validations.
        """
        return self._input_file

    @input_file.setter
    def input_file(self, ifile: InputFile | None):
        if not isinstance(ifile, (type(None), InputFile)):
            raise TypeError(
                f"Value for 'input_file' must be {InputFile} or None. "
                f"Provided {ifile} of type{type(ifile)}"
            )

        if ifile is not None:
            ifile = self.deprecation_update(ifile)
            self.validator = ifile.validators
            self.validations = ifile.validations

        self._input_file = ifile

    @classmethod
    def deprecation_update(cls, ifile: InputFile) -> InputFile:
        """
        Update the input file to the latest version of the ui_json.
        """

        json_dict = {}

        if ifile.ui_json is None or not any("type" in key for key in ifile.ui_json):
            return ifile

        key_swap = "Refinement horizon"
        for key, form in ifile.ui_json.items():
            if "type" in key:
                key_swap = form["group"] + " horizon"
                is_horizon = form.get("value")
                logic = is_horizon == "surface"
                msg = (
                    f"Old refinement format 'type'='{is_horizon}' is deprecated. "
                    f" Input type {'surface' if logic else 'radial'} will be interpreted as "
                    f"'is_horizon'={logic}."
                )
                warn(msg, FutureWarning)
                json_dict[key_swap] = template_dict["horizon"].copy()
                json_dict[key_swap]["value"] = logic
                json_dict[key_swap]["group"] = form["group"]

            elif "distance" in key:
                json_dict[key] = template_dict["distance"].copy()
                json_dict[key]["dependency"] = key_swap
                json_dict[key]["enabled"] = json_dict[key_swap]["value"]
            else:
                json_dict[key] = form

        input_file = InputFile(ui_json=json_dict, validate=False)

        if ifile.path is not None and ifile.name is not None:
            input_file.write_ui_json(name="[Updated]" + ifile.name, path=ifile.path)

        return input_file
