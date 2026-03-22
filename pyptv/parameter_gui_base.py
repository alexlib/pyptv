"""
Base GUI classes for schema-driven parameter management.

This module provides auto-generation of TraitsUI forms from parameter schemas,
eliminating duplication between parameter definitions and GUI code.
"""

from typing import Any, Callable, Optional
from pathlib import Path

from traits.api import HasTraits, Str, Float, Int, Bool, List
from traitsui.api import View, Item, Group, HGroup, VGroup, Handler, spring

from pyptv.parameter_schema import ALL_SCHEMAS, ParamField, get_schema_defaults
from pyptv.experiment import Experiment


TRAIT_TYPE_MAP = {
    "int": Int,
    "float": Float,
    "bool": Bool,
    "str": Str,
}


class SchemaToTraits:
    @staticmethod
    def get_trait_class(param_type: str):
        return TRAIT_TYPE_MAP.get(param_type.split("[")[0], Str)

    @staticmethod
    def get_default(param_type: str):
        if param_type.startswith("List"):
            base = param_type[5:-1]
            if base == "int":
                return []
            elif base == "float":
                return []
            elif base == "str":
                return []
        return None


def make_trait(name: str, field: ParamField) -> tuple:
    trait_class = SchemaToTraits.get_trait_class(field.param_type)
    trait_kwargs = {}
    if field.label:
        trait_kwargs["label"] = field.label
    return (name, trait_class, field.get_default(), trait_kwargs)


class BaseParamGUI(HasTraits):
    experiment = Any()

    _schema_name: str = ""
    _fields: dict = {}

    def __init__(self, experiment: Experiment, schema_name: str):
        super().__init__()
        self.experiment = experiment
        self._schema_name = schema_name
        self._load_from_params()

    def _load_from_params(self):
        params = self.experiment.pm.parameters
        schema = ALL_SCHEMAS.get(self._schema_name, {})
        for field_name, field_def in schema.get("fields", {}).items():
            if field_name in params:
                value = params[field_name]
                if hasattr(self, field_name):
                    setattr(self, field_name, value)
            elif not field_def.gui_only:
                setattr(self, field_name, field_def.get_default())

    def _collect_params(self) -> dict:
        schema = ALL_SCHEMAS.get(self._schema_name, {})
        result = {}
        for field_name, field_def in schema.get("fields", {}).items():
            if not field_def.gui_only and hasattr(self, field_name):
                result[field_name] = getattr(self, field_name)
        return result

    def _save_to_experiment(self):
        params = self._collect_params()
        self.experiment.pm.parameters[self._schema_name] = params
        self.experiment.save_parameters()


class BaseParamHandler(Handler):
    _gui_class: type = BaseParamGUI
    _schema_name: str = ""

    def closed(self, info, is_ok):
        if is_ok:
            gui = info.object
            gui._save_to_experiment()
            print(f"{self._schema_name} parameters saved successfully!")


class SchemaGUIBuilder:
    @staticmethod
    def build_traits(schema_name: str, extra_traits: dict = None) -> dict:
        schema = ALL_SCHEMAS.get(schema_name, {})
        traits = {}
        extra_traits = extra_traits or {}

        for field_name, field_def in schema.get("fields", {}).items():
            if field_name in extra_traits:
                continue
            trait_class = SchemaToTraits.get_trait_class(field_def.param_type)
            default = field_def.get_default()
            if isinstance(default, list):
                trait_class = List
            traits[field_name] = trait_class(default if default is not None else ...)

        traits.update(extra_traits)
        return traits

    @staticmethod
    def build_view(schema_name: str, title: str, groups: list = None) -> View:
        schema = ALL_SCHEMAS.get(schema_name, {})
        fields = schema.get("fields", {})

        if groups is None:
            items = []
            for field_name, field_def in fields.items():
                if field_def.label:
                    items.append(Item(name=field_name, label=field_def.label))
                else:
                    items.append(Item(name=field_name))
            root_group = VGroup(*items, show_border=True, label=schema_name.title())
        else:
            root_group = VGroup(*groups, label=schema_name.title())

        return View(
            root_group,
            resizable=True,
            buttons=["Undo", "OK", "Cancel"],
            title=title,
        )

    @staticmethod
    def build_handler(schema_name: str, gui_class: type) -> type:
        class Handler(Handler):
            def closed(self, info, is_ok):
                if is_ok:
                    gui = info.object
                    gui._save_to_experiment()
                    print(f"{schema_name} parameters saved successfully!")

        return Handler


def create_param_class(
    schema_name: str,
    title: str,
    extra_traits: dict = None,
    groups: list = None,
    gui_bases: tuple = (BaseParamGUI,),
) -> type:
    traits = SchemaGUIBuilder.build_traits(schema_name, extra_traits)
    view = SchemaGUIBuilder.build_view(schema_name, title, groups)
    handler = SchemaGUIBuilder.build_handler(schema_name, None)

    return type(
        f"{schema_name.title().replace('_', '')}GUI",
        gui_bases,
        {
            "_schema_name": schema_name,
            "edit_view": view,
            "__init__": lambda self, exp: gui_bases[0].__init__(self, exp),
        },
    )


def register_schema_guis():
    pass
