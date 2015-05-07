# -*- coding: utf-8 -*-

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
    "name": "Curvature to vertex colors",
    "category": "Object",
    "description": "Set object vertex colors according to mesh curvature",
    "author": "Tommi Hyppänen (ambi)",
    "location": "3D View > Object menu > Curvature to vertex colors",
    "version": (0, 1, 0),
    "blender": (2, 74, 0)
}

import bpy
import bmesh
import random
from collections import defaultdict
import mathutils
import math

class CurvatureOperator(bpy.types.Operator):
    """Curvature to vertex colors"""
    bl_idname = "object.vertex_colors_curve"
    bl_label = "Curvature to vertex colors"
    bl_options = {'REGISTER', 'UNDO'}
    
    intensity_multiplier = bpy.props.FloatProperty(
        name="Intensity Multiplier",
        default=6.0)
        
    separate = bpy.props.BoolProperty(
        name="Separate concavity and convexity",
        default=False)

    concavity = bpy.props.BoolProperty(
        name="Concavity",
        default=True)
        
    convexity = bpy.props.BoolProperty(
        name="Convexity",
        default=True)
        
    invert = bpy.props.BoolProperty(
        name="Invert",
        default=False)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.mode == 'OBJECT'

    def execute(self, context):
        vert_to_col = defaultdict(list)
        vert_to_edges = defaultdict(list)

        mesh = context.active_object.data

        # Use 'curvature' vertex color entry for results
        if "Curvature" not in mesh.vertex_colors:
            mesh.vertex_colors.new(name="Curvature")
            
        color_layer = mesh.vertex_colors['Curvature']
        mesh.vertex_colors["Curvature"].active = True

        # Map vertex colors to vertex indices
        i = 0
        for poly in mesh.polygons:
            for idx in poly.loop_indices:
                loop = mesh.loops[idx]
                vert_to_col[loop.vertex_index].append(i)
                i += 1

        # Map edges to vertex indices
        for edge in mesh.edges:
            for v in edge.vertices:
                vert_to_edges[v].append(edge)

        # Main calculation
        for vert in mesh.vertices:
            # Get connected vertices
            other_vert = []
            for edge in vert_to_edges[vert.index]:
                other_vert.append(mesh.vertices[[idx for idx in edge.vertices if idx != vert.index][0]])
                
            # Get dot products
            dotps = []
            for v in other_vert:
                dotps.append((v.co-vert.co).normalized().dot(vert.normal.normalized()))
                
            # Sum results
            a = sum(dotps)
            a /= len(dotps)
            a = 1.0 - math.acos(a)/math.pi
            
            # Format results
            if self.separate:
                if a>0.5:
                    a = (a-0.5)*2.0
                    a*=self.intensity_multiplier
                    a*=self.concavity
                    a = [a,a,a]
                else:
                    a = 1.0-a*2.0
                    a*=self.intensity_multiplier
                    a*=self.convexity
                    a = [a,a,a]             
            else:
                a-=0.5
                a*=self.intensity_multiplier
                if a<0:
                    a*=self.concavity
                else:
                    a*=self.convexity
                a+=0.5
                a = 1.0-a
                a = [a,a,a] 
                
            if self.invert:
                for i in range(3):
                    a[i] = 1.0 - a[i]
                
            for col in vert_to_col[vert.index]:        
                color_layer.data[col].color = a
                
        return {'FINISHED'}

def add_object_button(self, context):  
    self.layout.operator(  
        CurvatureOperator.bl_idname,  
        text=CurvatureOperator.__doc__,  
        icon='MESH_DATA')  

def register():
    bpy.utils.register_class(CurvatureOperator)
    bpy.types.VIEW3D_MT_object.append(add_object_button) 

def unregister():
    bpy.utils.unregister_class(CurvatureOperator)
    bpy.types.VIEW3D_MT_object.remove(add_object_button)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.vertex_colors_curve()