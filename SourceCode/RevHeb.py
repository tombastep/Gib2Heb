#!/usr/bin/env python
# -*- coding: utf-8 -*-


# This file is part of Gib2Heb
#
# Gib2Heb is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2020 Tom Melloul <tom@tommelloul.com>.

__author__ = "Tom Melloul"
__copyright__ = "Copyright (C) 2020, Tom Melloul"
__credits__ = ["Tom Melloul"]
__version__ = "1.0.0"
__status__ = "beta"

#---------- IMPORTS ----------#

# Rhino imports
import Rhino
from Rhino import *
from Rhino.DocObjects import *
from Rhino.Commands import *
from Rhino.Geometry import *
import scriptcontext as sc
import rhinoscriptsyntax as rs

# Python Imports
import re
import string

# Bidi Imports
from bidi.algorithm import get_display



#---------- FUNCTIONS ----------#


def ReplaceAll(INPUT, OUTPUT):
  for annotation_object in sc.doc.Objects.GetObjectList(ObjectType.Annotation):
    if not isinstance (annotation_object, AnnotationObjectBase):
      continue

    annotation = annotation_object.Geometry

    if annotation.Text == INPUT:
        annotation.Text = OUTPUT
        annotation_object.CommitChanges()
        annotation_object.Select(False)
  sc.doc.Views.Redraw()
  return Result.Success


def RevHeb(s):
    return get_display(s, upper_is_rtl=False)


def SelTxt():
    sc.doc.Objects.UnselectAll()
    sc.doc.Views.Redraw()
    geometryFilter = Rhino.DocObjects.ObjectType.Annotation
    items = ("All", "No", "Yes"), ("Similar", "No", "Yes")
    gr = rs.GetBoolean("Selection Options", items, (False, True) )
    if gr:
        SelAll = gr[0]
        SelSimilar = gr[1]
    go = Rhino.Input.Custom.GetObject()
    go.DisablePreSelect()
    go.SetCommandPrompt("Select text Objects to reverse")
    go.GeometryFilter = geometryFilter
    go.GroupSelect = True
    if gr[0]:
        hello = "hello"
    elif gr[1]:
        go.GetMultiple(1, 1)
        if go.CommandResult()!=Rhino.Commands.Result.Success:
            return go.CommandResult()
            
        for i in range(0, go.ObjectCount):
            rhinoObject = go.Object(i).Object()
            if not rhinoObject is None:
                str = rhinoObject.Geometry.Text
                if not RevHeb(str) == str:
                    ReplaceAll(str, RevHeb(str))
    else:
        go.GetMultiple(1, 0)
        if go.CommandResult()!=Rhino.Commands.Result.Success:
            return go.CommandResult()
            
        for i in range(0, go.ObjectCount):
            rhinoObject = go.Object(i).Object()
            if not rhinoObject is None:
                str = rhinoObject.Geometry.Text
                rhinoObject.Geometry.Text = RevHeb(str)
                rhinoObject.CommitChanges()
    sc.doc.Views.Redraw()
    return Rhino.Commands.Result.Success


#---------- EXECUTE ----------#

if __name__=="__main__":
    SelTxt()
