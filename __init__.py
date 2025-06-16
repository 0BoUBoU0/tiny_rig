    # ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Tiny Rig",
    "author": "Yannick 'BoUBoU' Castaing",
    "description": "create a very small rig with few essential bones",
    "location": "View3D > Add > Armature Menu",
    "doc_url": "",
    "warning": "",
    "category": "Rigging",
    "blender": (3,60,0),
    "version": (0,2,263)
}

# get addon name and version to use them automaticaly in the addon
Addon_Name = str(bl_info["name"])
Addon_Version = str(bl_info["version"]).replace(",",".").replace("(","").replace(")","")

### import modules ###
import bpy
import os
from statistics import mean
from importlib.util import find_spec

### define global variables ###
debug_mode = False
separator = "-" * 20

### create functions ###
def append_coll(coll_name):
    # get addon's name
    for addon_name in bpy.context.preferences.addons.keys():
        addon_name_b = addon_name.replace("-","_") # to avoid name changes beacause of gitlab
        if addon_name_b.startswith("tiny_rig"):
            addon = bpy.context.preferences.addons.get(addon_name)

    if coll_name not in bpy.data.collections.keys():
        ## append camera in the scene
        module_name = addon.module # Obtenir le nom du module
        # Utiliser importlib pour localiser le fichier source du module
        spec = find_spec(module_name)
        if spec and spec.origin:
            addon_path = os.path.dirname(spec.origin)
            # Chemin complet vers le fichier .blend
            camera_file = "Tiny_Rig.blend"
            blend_file_path = os.path.join(addon_path, camera_file)
            #print(blend_file_path)

            # Append the collection
            with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
                #print(data_from.collections)
                if coll_name in data_from.collections:
                    data_to.collections.append(coll_name)

### create property ###
class TINYRIG_properties (bpy.types.PropertyGroup):
    #rigscale_prop : bpy.props.FloatProperty (name="",default=1, min=0.001,description = "rig scale")
    pass

# add tool to armature
def menu_func(self, context):
    self.layout.operator(
        TINYRIG_OT_rig.bl_idname,
        text=TINYRIG_OT_rig.bl_label,
        icon='CON_SPLINEIK'
    )

### create operators ###        
class TINYRIG_OT_rig(bpy.types.Operator):
    bl_idname = "tinyrig.rig"
    bl_label = f"{Addon_Name} - {Addon_Version}"
    bl_description = "description operator"
    bl_options = {"REGISTER", "UNDO"}
    
    # redo panel = user interraction
    rigscale_prop: bpy.props.FloatProperty(
            name = "Rig Scale",
            description = "descripyion",
            default=1,min=0.001,
    )

    rigloc_opt = [
                ('Object to Center','Object to Center','Object to Center',0),
                ('Object Still','Object Still','Object Still',1),
                ('Bone to Object','Bone to Object','Bone to Object',2),
                  ]
    rigloc_prop: bpy.props.EnumProperty (items = rigloc_opt,
                                        default=2,
                                        name = 'Location',
    )
    storeobjinrigcoll_prop: bpy.props.BoolProperty(
            name = "Store into rig collection",
            description = "if checked, the object will be stored in the new rig collection",
            default=True,
    )

    def execute(self, context):
        print(f"\n {separator} Begin {self.bl_label} {separator} \n")

        ## set names
        collRig_name = 'TinyRig'
        objRig_name = f'RIG_{collRig_name}'
        bonesname_dict = {
                        'root':'CTRL_root',
                        'move':'CTRL_move',
                        }

        # store selection infos
        sel_obj = bpy.context.selected_objects
        obj_active = bpy.context.view_layer.objects.active

        # deselect
        bpy.ops.object.select_all(action='DESELECT')

        # if not in file, append the rig
        if objRig_name not in bpy.data.objects.keys():            
            append_coll(collRig_name)
        # Link it in the current scene
        for coll in bpy.data.collections:
            if coll.name == collRig_name:
                # link into main object collections
                for coll in obj_active.users_collection:
                    if collRig_name not in coll.children.keys():
                        coll.children.link(bpy.data.collections[collRig_name])
                    #bpy.context.scene.collection.children.link(coll)
        objRig = bpy.data.objects[objRig_name]
        collrig = bpy.data.collections[collRig_name]

        # rename regarding selected obj
        objRig.name = f'{obj_active.name}-{objRig_name}'
        collrig.name = f'{obj_active.name}-{collRig_name}'


        orig_loc_key = obj_active.location
        if self.rigloc_prop == 'Bone to Object':
            objRig.pose.bones[bonesname_dict['move']].location[0] = orig_loc_key[0]
            objRig.pose.bones[bonesname_dict['move']].location[1] = orig_loc_key[2]
            objRig.pose.bones[bonesname_dict['move']].location[2] = -orig_loc_key[1]
        if self.rigloc_prop == 'Object to Center' or self.rigloc_prop == 'Bone to Object':
            for obj in sel_obj:
                for i in range(0,3):
                    obj.location[i] -= orig_loc_key[i]
        elif self.rigloc_prop == 'Object Still' :
            pass
            
        ## scale the rig regarding what user wants
        for key,value in bonesname_dict.items():
            objRig.pose.bones[bonesname_dict["root"]]['visual_scale'] = self.rigscale_prop
            #objRig.pose.bones[value].custom_shape_scale_xyz*= self.rigscale_prop
        #setattr(bpy.context.scene.tinyrigprops, 'rigscale_prop', self.rigscale_prop)
        

        # parent rig + bone
        for obj in sel_obj:
            obj.select_set(True)
            objRig.select_set(True)    
            bpy.context.view_layer.objects.active = objRig
            bpy.ops.object.parent_set(type='BONE_RELATIVE', keep_transform=True)
            obj.parent = objRig
            obj.parent_type = 'BONE'
            obj.parent_bone = bonesname_dict['move']
            # deselect
            bpy.ops.object.select_all(action='DESELECT')

        # if store in rig collection
        if self.storeobjinrigcoll_prop:
            for user_coll in obj.users_collection:
                user_coll.objects.unlink(obj)
            collrig.objects.link(obj)

        print(f"{Addon_Name} done on : selected objects \n")
        print(f"\n {separator} {self.bl_label} finished {separator} \n")
        
        return {"FINISHED"}


# list all classes
classes = (
    TINYRIG_properties,
    TINYRIG_OT_rig,
    )

# create keymap list
addon_keymaps = []

# register classes
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tinyrigprops = bpy.props.PointerProperty (type = TINYRIG_properties)
    bpy.types.VIEW3D_MT_armature_add.append(menu_func)

    # add keymap
    # if bpy.context.window_manager.keyconfigs.addon:
    #     keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="3D View", space_type="VIEW_3D")
    #     keymapitem = keymap.keymap_items.new("operator.details", #operator
    #                                          "S", #key
    #                                         "PRESS", # value
    #                                         ctrl=True, alt=True
    #                                         )
    #     addon_keymaps.append((keymap, keymapitem))

#unregister classes 
def unregister():   
    bpy.types.VIEW3D_MT_armature_add.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.tinyrigprops

    # remove keymap
    # for keymap, keymapitem in addon_keymaps:
    #     keymap.keymap_items.remove(keymapitem)
    # addon_keymaps.clear()
        