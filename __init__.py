# Apply Pose as Rest Pose
# Copyright 2025 Foxipso
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import numpy as np


class POSE2REST_OT_apply(bpy.types.Operator):
    """Apply the current pose as the new rest pose, correctly handling shape keys"""
    bl_idname = "pose2rest.apply"
    bl_label = "Apply Pose as Rest Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE' and obj.mode == 'POSE'

    def execute(self, context):
        armature_obj = context.active_object
        mesh_objs = [
            child for child in armature_obj.children_recursive
            if child.type == 'MESH'
        ]

        for mesh_obj in mesh_objs:
            me = mesh_obj.data
            if me and me.shape_keys and me.shape_keys.key_blocks:
                key_blocks = me.shape_keys.key_blocks
                if len(key_blocks) == 1:
                    # Only a basis key — remove it, apply, then re-add
                    basis_name = key_blocks[0].name
                    mesh_obj.shape_key_remove(key_blocks[0])
                    self._apply_armature_no_shapekeys(armature_obj, mesh_obj)
                    mesh_obj.shape_key_add(name=basis_name)
                else:
                    self._apply_armature_with_shapekeys(armature_obj, mesh_obj)
            else:
                self._apply_armature_no_shapekeys(armature_obj, mesh_obj)

        # Apply current pose as the new rest pose
        with context.temp_override(active_object=armature_obj):
            bpy.ops.pose.armature_apply()

        # Clear the pose transforms (they're baked in now)
        for pb in armature_obj.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)

        self.report({'INFO'}, "Pose applied as rest pose")
        return {'FINISHED'}

    @staticmethod
    def _apply_armature_no_shapekeys(armature_obj, mesh_obj):
        """Add a temporary armature modifier set to the posed armature and apply it."""
        mod = mesh_obj.modifiers.new('_PoseToRest', 'ARMATURE')
        mod.object = armature_obj
        mod_name = mod.name
        ctx = {'object': mesh_obj}
        with bpy.context.temp_override(**ctx):
            bpy.ops.object.modifier_move_to_index(modifier=mod_name, index=0)
            bpy.ops.object.modifier_apply(modifier=mod_name)

    @staticmethod
    def _apply_armature_with_shapekeys(armature_obj, mesh_obj):
        """Apply the pose to each shape key using depsgraph evaluation."""
        me = mesh_obj.data
        key_blocks = me.shape_keys.key_blocks

        old_active_idx = mesh_obj.active_shape_key_index
        old_pin = mesh_obj.show_only_shape_key
        mesh_obj.show_only_shape_key = True

        # Save and clear vertex groups / mutes on shape keys (they affect pinned display)
        saved_vgroups = []
        saved_mutes = []
        for sk in key_blocks:
            saved_vgroups.append(sk.vertex_group)
            sk.vertex_group = ''
            saved_mutes.append(sk.mute)
            sk.mute = False

        # Disable all existing modifiers in viewport
        mods_reenabled = []
        for mod in mesh_obj.modifiers:
            if mod.show_viewport:
                mod.show_viewport = False
                mods_reenabled.append(mod)

        # Add temporary armature modifier
        arm_mod = mesh_obj.modifiers.new('_PoseToRest', 'ARMATURE')
        arm_mod.object = armature_obj

        co_len = len(me.vertices) * 3
        cos = np.empty(co_len, dtype=np.single)
        depsgraph = None
        eval_obj = None

        def get_eval_cos():
            nonlocal depsgraph, eval_obj
            if depsgraph is None:
                depsgraph = bpy.context.evaluated_depsgraph_get()
                eval_obj = mesh_obj.evaluated_get(depsgraph)
            else:
                depsgraph.update()
            eval_obj.data.vertices.foreach_get('co', cos)
            return cos

        for i, sk in enumerate(key_blocks):
            mesh_obj.active_shape_key_index = i
            evaluated = get_eval_cos()
            sk.data.foreach_set('co', evaluated)
            if i == 0:
                me.vertices.foreach_set('co', evaluated)

        # Restore everything
        for mod in mods_reenabled:
            mod.show_viewport = True
        mesh_obj.modifiers.remove(arm_mod)
        for sk, vg, mt in zip(key_blocks, saved_vgroups, saved_mutes):
            sk.vertex_group = vg
            sk.mute = mt
        mesh_obj.active_shape_key_index = old_active_idx
        mesh_obj.show_only_shape_key = old_pin


class POSE2REST_PT_panel(bpy.types.Panel):
    bl_label = "Apply Pose as Rest Pose"
    bl_idname = "POSE2REST_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Pose"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj.mode == 'POSE':
            layout.operator("pose2rest.apply", icon='ARMATURE_DATA')
        else:
            layout.label(text="Enter Pose Mode first")


def register():
    bpy.utils.register_class(POSE2REST_OT_apply)
    bpy.utils.register_class(POSE2REST_PT_panel)


def unregister():
    bpy.utils.unregister_class(POSE2REST_PT_panel)
    bpy.utils.unregister_class(POSE2REST_OT_apply)
