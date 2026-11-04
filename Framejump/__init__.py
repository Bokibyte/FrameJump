bl_info = {
    "name": "FrameJump",
    "description": "Animation Utilities for Repeatitive Animation",
    "author": "Bokibyte",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar (N-Panel) > FrameJump",
    "category": "Object" }

import sys
import os
import importlib
import importlib.util
import bpy
from bpy.props import PointerProperty

MODULES = [
    "properties",
    "operators",
    "ui"
]

ADDONS_DIR = os.path.dirname(os.path.abspath(__file__))

def reload_modules(): # local modules
    reload_modules = {}
    for mods in MODULES:
        mods_path = os.path.join(ADDONS_DIR, f"{mods}.py")
        unique_key = f"framejump_{mods}"
        spec = importlib.util.spec_from_file_location(unique_key, mods_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_key] = module
        spec.loader.exec_module(module)
        reload_modules[mods] = module
    return reload_modules

addon_modules = reload_modules()
for name in MODULES:
    globals()[name] = addon_modules[name]
    
def get_classes():
    classes = []
    for name in MODULES:
        module = globals()[name]
        module_classes = getattr(module, f"framejump_classes_{name}", ())
        classes.extend(module_classes)
    return tuple(classes)

def draw_reload_header(self, context):
    layout = self.layout
    row = layout.row()
    row.alert = True
    row.operator("framejump.reload")
    
