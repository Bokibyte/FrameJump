import importlib
import importlib.util
import os
import sys
from collections.abc import Callable, Iterable
from types import ModuleType
from typing import Any

import bpy


class DynaLoad:
    def __init__(
        self,
        addon_name: str,
        modules: Iterable[str],
        addon_dir: str | None = None,
        on_reload: Callable[[dict[str, ModuleType]], None] | None = None,
    ) -> None:
        if not addon_name.isidentifier() or addon_name.lower() != addon_name:
            raise ValueError("addon_name must be a lowercase Python-style identifier")
        self.addon_name = addon_name
        self.modules = tuple(modules)
        self.addon_dir = addon_dir or os.path.dirname(os.path.abspath(__file__))
        self.on_reload = on_reload
        self.loaded_modules: dict[str, ModuleType] = {}
        self.operator_id = f"{addon_name}.reload_modules"

    def check(self) -> None:
        for module_name in self.modules:
            module_path = os.path.join(self.addon_dir, f"{module_name}.py")
            if not os.path.isfile(module_path):
                raise FileNotFoundError(f"Module not found: {module_path}")

    def load(self) -> dict[str, ModuleType]:
        self.check()
        importlib.invalidate_caches()
        loaded: dict[str, ModuleType] = {}

        for module_name in self.modules:
            module_path = os.path.join(self.addon_dir, f"{module_name}.py")
            unique_name = f"{self.addon_name}_{module_name}"
            spec = importlib.util.spec_from_file_location(unique_name, module_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load module: {module_path}")

            module = importlib.util.module_from_spec(spec)
            previous_module = sys.modules.get(unique_name)
            sys.modules[unique_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                if previous_module is None:
                    sys.modules.pop(unique_name, None)
                else:
                    sys.modules[unique_name] = previous_module
                raise
            loaded[module_name] = module

        self.loaded_modules = loaded
        return loaded

    def reload(self) -> dict[str, ModuleType]:
        loaded = self.load()
        if self.on_reload is not None:
            self.on_reload(loaded)
        return loaded

    def draw_ui(self, layout: Any) -> None:
        row = layout.row()
        row.alert = True
        row.operator(self.operator_id, icon="FILE_REFRESH")

    def create_reload_operator(self) -> type[bpy.types.Operator]:
        loader = self

        class dynaload_reload(bpy.types.Operator):
            bl_idname = loader.operator_id
            bl_label = "Reload Local Modules"
            bl_description = "Reload this add-on's local Python modules"

            def execute(self, context: Any) -> set[str]:
                try:
                    loader.reload()
                except Exception as error:
                    self.report({"ERROR"}, f"Module reload failed: {error}")
                    return {"CANCELLED"}

                self.report({"INFO"}, "Local modules reloaded")
                return {"FINISHED"}

        return dynaload_reload

