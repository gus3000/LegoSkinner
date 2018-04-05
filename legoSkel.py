bl_info = {
    "name": "Lego skeleton manager",
    "category": "Object",
}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty

origin = (0, 0, 0)
amtName = "Armature"


class Utils(bpy.types.Operator):
    """Utils3000"""
    bl_idname = "object.utils3000"
    bl_label = "Util3000"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.selected_objects[0]
        objData = obj.data
        for vert in objData.vertices:
            inf = []
            for influence in objData.getVertexInfluences(vert.index):
                inf.append(influence)
                print(vert.index, ':', influence)


class LegoSkeletonCreator(bpy.types.Operator):
    """Lego Skeleton Creator"""
    bl_idname = "object.lego_skeleton_creator"
    bl_label = "Lego Skeleton Creator"
    bl_options = {'REGISTER', 'UNDO'}

    def handle_torso(self, amt):
        bone = amt.edit_bones.new('Torso')

        bone.head = origin
        bone.tail = (0, 0, 1.2)

        self.handle_head(amt, bone)
        self.handle_shoulder(amt, bone, True)
        self.handle_shoulder(amt, bone, False)
        self.handle_leg(amt, bone, True)
        self.handle_leg(amt, bone, False)

    def handle_head(self, amt, torso):
        bone = amt.edit_bones.new('Head')
        bone.use_connect = True
        bone.parent = torso
        bone.head = torso.tail
        bone.tail = (0, 0, 2.2)

    def handle_shoulder(self, amt, torso, isLeft):
        bone = amt.edit_bones.new('Shoulder' + ((isLeft and 'L') or 'R'))
        bone.use_connect = True
        bone.parent = torso

        bone.head = torso.tail
        x = 0.472
        z = 1.068
        bone.tail = ((isLeft and x) or -x, 0, z)

        self.handle_arm(amt, bone, isLeft)

    def handle_arm(self, amt, shoulder, isLeft):
        bone = amt.edit_bones.new('Arm' + ((isLeft and 'L') or 'R'))
        bone.use_connect = True
        bone.parent = shoulder

        bone.head = shoulder.tail
        x = 0.8
        z = 1.125
        bone.tail = ((isLeft and x) or -x, 0, z)
        self.handle_hand(amt, bone, isLeft)

    def handle_hand(self, amt, arm, isLeft):
        bone = amt.edit_bones.new('Hand' + ((isLeft and 'L') or 'R'))
        bone.parent = arm

        hx = 0.85
        hy = 0
        hz = 0.8
        bone.head = ((isLeft and hx) or -hx, hy, hz)

        tx = 0.924
        ty = -0.4
        tz = 0.4
        bone.tail = ((isLeft and tx) or -tx, ty, tz)

    def handle_leg(self, amt, torso, isLeft):
        bone = amt.edit_bones.new('Leg' + ((isLeft and 'L') or 'R'))
        bone.parent = torso

        hx = 0.4
        hz = -0.2
        bone.head = ((isLeft and hx) or -hx, 0, hz)

        tx = 0.4
        tz = -1.3
        bone.tail = ((isLeft and tx) or -tx, 0, tz)

    def rig(self, pieces, amt):
        bpy.ops.object.mode_set(mode='EDIT')
        amtObject = bpy.data.objects[amtName]
        amtLocation = amtObject.location
        for o in pieces:
            min = 1000
            nearest_bone = None
            for bone in amt.edit_bones:
                # bpy.ops.mesh.primitive_uv_sphere_add(location=bone.center + amtLocation)
                # bpy.context.object.scale = (0.1, 0.1, 0.1)
                # bpy.context.object.name = "sphere" + bone.name
                for pos in [bone.tail, bone.center, bone.head]:
                    len = (o.location - (pos + amtLocation)).length
                    # print(o.name,": (",o.location,'-',bone.center,') =>',len)
                    if len < min:
                        min = len
                        nearest_bone = bone
            # print(o.name,'is near',nearest_bone.name)
            bpy.ops.object.parent_set(type='ARMATURE_NAME')

            existingMod = None
            if o.modifiers:
                for mod in o.modifiers:
                    if mod.name == "SkeletonLego":
                        existingMod = mod

            mod = existingMod or o.modifiers.new(name='SkeletonLego', type='ARMATURE')
            mod.object = amtObject

    def execute(self, context):
        print('#################### Début Programme #####################')

        oldAmt = bpy.data.objects.get(amtName)
        if oldAmt:
            oldAmt.select = False

        pieces = context.selected_objects
        for p in pieces:
            p.select = False

        bpy.ops.object.delete()

        bpy.ops.object.add(
            type='ARMATURE',
            enter_editmode=False,
            location=(0, 0, 1.41082))

        bpy.ops.object.mode_set(mode='EDIT')
        ob = bpy.context.object
        amt = ob.data
        self.handle_torso(amt)
        self.rig(pieces, amt)

        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}


class LegoSkeletonSpectator(bpy.types.Operator):
    """Lego Skeleton Spectator"""
    bl_idname = "object.lego_skeleton_spectator"
    bl_label = "Lego Skeleton Analyser"
    bl_options = {'REGISTER'}

    def execute(self, context):
        ob = bpy.context.object
        amt = ob.data
        for bone in amt.bones:
            print(bone.name, ":", bone.tail)
        return {'FINISHED'}

class LegoImporter(bpy.types.Operator, ImportHelper):
    bl_idname = "object.lego_importer"
    bl_label = "Lego Importer"
    bl_options = {'REGISTER'}

    adjust_transform = BoolProperty(
        name="Adjust Transform",
        description="Scale /= 25; rotate.x(-90);",
        default=True,
    )

    def import_lego(self, context):
        print('Beginning Lego import from', self.filepath, 'with settings', self.adjust_transform)
        fig = bpy.ops.import_scene.obj(filepath=self.filepath, axis_forward='Y')
        if(self.adjust_transform):
            bpy.ops.transform.resize(value=(1/25,1/25,1/25))

        bpy.ops.object.shade_smooth()

        mini_array = bpy.context.selected_objects
        for obj in mini_array:
            bpy.context.scene.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')


        return {'FINISHED'}

    def execute(self, context):
        return self.import_lego(context)

def register():
    bpy.utils.register_class(LegoSkeletonCreator)
    bpy.utils.register_class(LegoSkeletonSpectator)
    bpy.utils.register_class(Utils)
    bpy.utils.register_class(LegoImporter)



def unregister():
    bpy.utils.unregister_class(LegoSkeletonCreator)
    bpy.utils.unregister_class(LegoSkeletonSpectator)
    bpy.utils.unregister_class(Utils)
    bpy.utils.unregister_class(LegoImporter)

if __name__ == "__main__":
    print('-------------------------------')
    register()
    #simulate a call to import
    bpy.ops.object.lego_importer('INVOKE_DEFAULT')
