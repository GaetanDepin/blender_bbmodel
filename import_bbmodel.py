import json
import bpy
import math
import base64
import tempfile

X_INDEX = 2
Z_INDEX = 1
Y_INDEX = 0
FACE_ORDER = ["north", "east", "south", "west", "down", "up"]

def create_mesh(element):
    bpy.ops.mesh.primitive_cube_add()
    
    name = element["uuid"]
    pos = element["from"]
    to = element["to"]

    cube = bpy.context.selected_objects[0]
    cube.name = name

    x = abs(pos[X_INDEX] - to[X_INDEX])
    y = abs(pos[Y_INDEX] - to[Y_INDEX])
    z = abs(pos[Z_INDEX] - to[Z_INDEX])
    cube.dimensions = (x, y, z)
    cube.location = (pos[X_INDEX] + x/ 2, pos[Y_INDEX] + y / 2, pos[Z_INDEX] + z / 2)
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

def load_outline(outline, meshes):
    o = bpy.data.objects.new("empty", None)
    bpy.context.scene.collection.objects.link(o)
    o.empty_display_size = 2
    o.empty_display_type = 'PLAIN_AXES'
    o.name = outline["name"]
    for child in outline["children"]:
        if type(child) is dict:
            c = load_outline(child, meshes)
            c.parent = o
        else:
            meshes[child].parent = o
    return o

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
        load_outline(outline, meshes)
    return {"FINISHED"}

if __name__ == "__main__":
    # filepath = "/home/gaetan/Documents/mindustry/test.bbmodel"
    filepath = "/home/gaetan/Documents/mindustry/blockbench_model/character/character.bbmodel"
    # filepath = "/home/gaetan/Documents/mindustry/blockbench_model/item/circuit_board.bbmodel"
    # filepath = "/home/gaetan/Documents/mindustry/blockbench_model/item/copper_ore.bbmodel"
    # filepath = "/home/gaetan/Documents/mindustry/blockbench_model/item/copper_wire.bbmodel"
    load(None, None, filepath, None)