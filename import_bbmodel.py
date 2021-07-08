import json
import bpy
import math
import base64
import tempfile

X_INDEX = 2
Z_INDEX = 1
Y_INDEX = 0
FACE_ORDER = ["north", "east", "south", "west", "down", "up"]
FPS = 24

def get_rotation(rot):
    return (math.radians(float(rot["z"])), math.radians(float(rot["x"])), math.radians(float(rot["y"])))

def create_mesh(element):
    bpy.ops.mesh.primitive_cube_add()
    
    name = element["uuid"]
    from_coord = element["from"]
    to_coord = element["to"]
    pos = element["origin"]

    cube = bpy.context.selected_objects[0]
    cube.name = name

    x = abs(from_coord[X_INDEX] - to_coord[X_INDEX])
    y = abs(from_coord[Y_INDEX] - to_coord[Y_INDEX])
    z = abs(from_coord[Z_INDEX] - to_coord[Z_INDEX])
    center = (from_coord[X_INDEX] + x / 2, from_coord[Y_INDEX] + y / 2, from_coord[Z_INDEX] + z / 2)
    # cube.location = (pos[X_INDEX], pos[Y_INDEX], pos[Z_INDEX])
    cube.location = (pos[X_INDEX] + center[0], pos[Y_INDEX] + center[1], pos[Z_INDEX] + center[2])
    cube.dimensions = (x, y, z)
    if "rotation" in element:
        rot = element["rotation"]
        cube.rotation_euler = (math.radians(rot[X_INDEX]), math.radians(rot[Y_INDEX]), math.radians(rot[Z_INDEX]))
    bpy.ops.object.transform_apply(location = False, scale = True, rotation = False)
    return cube

def load_uv(element, content, mesh):
    new_uv = mesh.uv_layers[0]
    img_width = content["resolution"]["width"]
    img_height = content["resolution"]["height"]

    for loop in range(int(len(bpy.context.active_object.data.loops) / 4)):
        index = 4 * loop
        uvs_face = element["faces"][FACE_ORDER[loop]]["uv"]
        top_left = (uvs_face[2] / img_width, 1 - uvs_face[1] / img_height)
        bottom_right = (uvs_face[0] / img_width, 1 - uvs_face[3] / img_height)
        new_uv.data[index].uv = (top_left[0], bottom_right[1])
        new_uv.data[index + 1].uv = top_left
        new_uv.data[index + 2].uv = (bottom_right[0], top_left[1])
        new_uv.data[index + 3].uv = bottom_right

def load_outline(outline, meshes, parent_pos):
    o = bpy.data.objects.new("empty", None)
    bpy.context.scene.collection.objects.link(o)
    o.empty_display_size = 2
    o.empty_display_type = 'PLAIN_AXES'
    o.name = outline["name"]
    pos = outline["origin"]
    o.location = (pos[X_INDEX] - parent_pos[X_INDEX], pos[Y_INDEX] - parent_pos[Y_INDEX], pos[Z_INDEX] - parent_pos[Z_INDEX])

    for child in outline["children"]:
        if type(child) is dict:
            c = load_outline(child, meshes, pos)
            c.parent = o
        else:
            meshes[child].parent = o
            meshes[child].location[0] -= pos[X_INDEX]
            meshes[child].location[1] -= pos[Y_INDEX]
            meshes[child].location[2] -= pos[Z_INDEX]
    meshes[outline["uuid"]] = o
    return o

def load_animation(animation, meshes):
    scene = bpy.context.scene
    for animator in animation["animators"]:
        mesh = meshes[animator]
        animator_data = animation["animators"][animator]
        for keyframe in animator_data["keyframes"]:
            scene.frame_set(int(keyframe["time"] * FPS))
            if keyframe["channel"] == "rotation":
                rot = keyframe["data_points"][0]
                mesh.rotation_euler = get_rotation(rot)
                mesh.keyframe_insert(data_path="rotation_euler", index=-1)
            for fcurve in mesh.animation_data.action.fcurves:
                fcurve.extrapolation = 'LINEAR'


def load(operator, context, filepath="", global_matrix=None):
    print("load", filepath)
    file = open(filepath, "rb")
    content = json.load(file)
    
    mat = None
    meshes = {}

    for texture in content["textures"]:
        decode = base64.b64decode(texture["source"].split(",")[1])
        # file = tempfile.NamedTemporaryFile()
        file = open("/tmp/img","wb")
        file.write(decode)
        file.flush()
        mat = bpy.data.materials.new(name="test")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(file.name)
        tex.interpolation = "Closest"
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex.outputs['Color'])
    for element in content["elements"]:
        if "visibility" in element and not element["visibility"]:
            continue
        mesh = create_mesh(element)
        load_uv(element, content, mesh.data)
        if mesh.data.materials:
            mesh.data.materials[0] = mat
        else:
            mesh.data.materials.append(mat)
        meshes[element["uuid"]] = mesh
    for outline in content["outliner"]:
        if type(outline) is dict:
            load_outline(outline, meshes, (0, 0, 0))
    # if "animations" in content and len(content["animations"]) > 0:
    #     load_animation(content["animations"][0], meshes)
    return {"FINISHED"}

if __name__ == "__main__":
    # filepath = "/home/gaetan/Documents/blender_bbmodel/blockbench_model/test.bbmodel"
    filepath = "/home/gaetan/Documents/blender_bbmodel/blockbench_model/factory/welder.bbmodel"
    # filepath = "/home/gaetan/Documents/blender_bbmodel/blockbench_model/character/character.bbmodel"
    # filepath = "/home/gaetan/Documents/blender_bbmodel/blockbench_model/item/circuit_board.bbmodel"
    # filepath = "/home/gaetan/Documents/blender_bbmodel/blockbench_model/item/copper_ore.bbmodel"
    # filepath = "/home/gaetan/Documents/blender_bbmodel/blockbench_model/item/copper_wire.bbmodel"
    load(None, None, filepath, None)