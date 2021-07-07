bl_info = {
    "name": "Blockbench model importer (.bbmodel)",
    "author": "Gaetan",
    "blender": (2, 93, 0),
    "location": "File > Import-Export",
    "description": "Import blockbench model",
    "warning": "",
    "wiki_url": "",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

if "bpy" in locals():
    import importlib
    if "import_bbmodel" in locals():
        importlib.reload(import_bbmodel)


import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper,
        axis_conversion,
        )


@orientation_helper(axis_forward='Y', axis_up='Z')
class ImportBBModel(bpy.types.Operator, ImportHelper):
    """Import from blockbench file format (.bbmodel)"""
    bl_idname = "import_scene.blockbench"
    bl_label = 'Import blockbench'
    bl_options = {'UNDO'}

    filename_ext = ".bbmodel"
    filter_glob : StringProperty(default="*.bbmodel", options={'HIDDEN'})


    def execute(self, context):
        from . import import_bbmodel

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            ))

        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        return import_bbmodel.load(self, context, **keywords)


def menu_func_import(self, context):
    self.layout.operator(ImportBBModel.bl_idname, text="Blockbench (.bbmodel)")


def register():
    bpy.utils.register_class(ImportBBModel)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportBBModel)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()