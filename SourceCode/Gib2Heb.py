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


__version__ = "1.0.0.2"


#---------- TO-DO LIST ----------#

#   1.  Add Eng2Heb to Decoders option list
#   2.  Implemenet Decoders and Encoders Selection
#   3.  Implement Reverse Only






#---------- IMPORTS ----------#

# Rhino imports
import Rhino

from Rhino.DocObjects import *
from Rhino.Commands import *
from Rhino.Geometry import *

import scriptcontext as sc
import rhinoscriptsyntax as rs


# Python Imports
import re
import string
import System

# Bidi Imports
from encodings import hex_codec
from algorithm import get_display


#---------- DEFINE CHARSETS & DECODERS ----------#

rgx = "^[A-Za-z0-9.,:;!?=\\\\+\-[\]\{\}|\' `~\"@%&*$<>()\/s]+$"
rgx2 = "^[a-z0-9.,:;!?=\\\+\-\[\]\{\}|\' `~\"@%&*$<>()\/s]+$"
hebChrs = "אבגדהוזחטיכךלמםנןסעפףצץקרשת"
strEncode = "cp1255"
strDecoders = ["cp862", "cp856", "cp424", "iso8859_8", "cp1255"]


#---------- FUNCTIONS ----------#

def isHeb(s):
    
    s = ''.join(s.split())
    i = 0
    for c in s:
        if c >= u"\u0590" and c <= u"\u05EA":
            i = i+1
    return i


def isEng(s):
    
    s = ''.join(s.split())
    if not re.match('^[0-9.,:;!?=\-\+\ \\()\/s]+$', s):
        iseng = re.match(rgx, s)
        if iseng: return True
        else: return False
    else: return False


def Eng2Heb(s):
    
    INPUT = "qwertyuiopasdfghjkl;zxcvbnm,."
    OUTPUT = "/'קראטוןםפשדגכעיחלךףזסבהנמצתץ"
    sn = ''.join(s.split())
    
    if not re.match(rgx2, sn):
        return s
    
    else:
        TABLE = string.maketrans(INPUT,OUTPUT) 
        result = s.translate(TABLE)
        return result


def ConvTxt(str, boolFlipHeb):
    
    cnvStr = str
    Engl = isEng(cnvStr)
    if Engl: return Eng2Heb(str)
    
    else:  
        hebChr = 0
        for strDecode in strDecoders:
            tmpStr = str.encode(strEncode, "replace").decode(strDecode, "replace")
            tmpChr = isHeb(tmpStr)
            if tmpChr > hebChr:
                cnvStr = tmpStr
                hebChr =  tmpChr
                meth = strDecode + "(" + hebChr.ToString() + ")"
    if cnvStr != str:
        if boolFlipHeb: return get_display(u'' + cnvStr, upper_is_rtl=False, encoding=strEncode, debug=False)
        else: return cnvStr
    else: return str


def JstFix(s):
    
    s = s.ToString()
    result = string.replace(s, 'Left', 'Right')
    if result == s: result = string.replace(s, 'Right', 'Left')
    return "TextJustification." + result 


def ReplaceAll(INPUT, OUTPUT):
    
    for rhinoObject in sc.doc.Objects.GetObjectList(ObjectType.Annotation):
        if not isinstance (rhinoObject, AnnotationObjectBase):
          continue
        
        if rhinoObject.Geometry.Text == INPUT:
            rhinoObject.Geometry.Text = OUTPUT
            if hasattr(rhinoObject.Geometry, "Justification"):
                jst = rhinoObject.Geometry.Justification
                rhinoObject.Geometry.Justification = eval(JstFix(jst))
            rhinoObject.CommitChanges()
            rhinoObject.Select(False)
    sc.doc.Views.Redraw()
    return Rhino.Commands.Result.Success

def BlockTxt(block, str = False, cstr = False, boolFlipHeb=True):
    if not block: return
    
    blockName = rs.BlockInstanceName(block)
    objref = rs.coercerhinoobject(block)
    idef = objref.InstanceDefinition
    idefIndex = idef.Index
    
    XformBlock = rs.BlockInstanceXform(block)
    blockObjects = rs.BlockObjects(blockName)
    
    txtobjs = False
    
    for obj in blockObjects:
        if rs.IsText(obj):
            if not str: txtobjs = True
            elif rs.TextObjectText(obj) == str: txtobjs = True
    
    if txtobjs:
        
        blockInstanceObjects = rs.TransformObjects(blockObjects, XformBlock, True)
        
        keep = []
        
        rs.EnableRedraw(False)
        
        for obj in blockInstanceObjects:
            if rs.IsText(obj):
                if not str and not cstr:
                    str = rs.TextObjectText(obj)
                    cstr = ConvTxt(str, boolFlipHeb)
                if not cstr == str:
                    rs.TextObjectText(obj, cstr)
                keep.append(obj)
            else: keep.append(obj)
        
        rs.TransformObjects(keep, rs.XformInverse(XformBlock), False)
        
        newGeometry = []
        newAttributes = []
        for object in keep:
            newGeometry.append(rs.coercegeometry(object))
            ref = Rhino.DocObjects.ObjRef(object)
            attr = ref.Object().Attributes
            newAttributes.append(attr)
        
        InstanceDefinitionTable = sc.doc.ActiveDoc.InstanceDefinitions
        InstanceDefinitionTable.ModifyGeometry(idefIndex, newGeometry, newAttributes)
        
        rs.DeleteObjects(keep)

def BlockTxtAll(boolFlipHeb=True):
    
    blocks = rs.ObjectsByType(4096, False, 0)
    
    for blockRef in blocks:
        BlockTxt(blockRef, False, False, boolFlipHeb)
    
    rs.EnableRedraw(True)

def BlockTxtSim(block, boolFlipHeb=True):
    
    if not block: return
    
    blockName = rs.BlockInstanceName(block)
    blockObjects = rs.BlockObjects(blockName)
    
    obj = blockObjects[0]
    str= ""
    cstr = ""
    
    if rs.IsText(obj):
        str = rs.TextObjectText(obj)
        cstr = ConvTxt(str, boolFlipHeb)
    else: return
    
    blocks = rs.ObjectsByType(4096, False, 0)
    
    for blockRef in blocks:
        BlockTxt(blockRef, str, cstr, boolFlipHeb)
    
    rs.EnableRedraw(True)


#---------- SELECTION ----------#

def SelMult(boolBlocks, boolFlipHeb):
    
    geoFilter = Rhino.DocObjects.ObjectType.Annotation
    
    gt = Rhino.Input.Custom.GetObject()
    gt.SetCommandPrompt("Please select text objects for conversion")
    
    gt.GeometryFilter = geoFilter
    gt.GroupSelect = True
    
    gt.GetMultiple(1,0)
    
    
    if gt.CommandResult()!=Rhino.Commands.Result.Success:
        return gt.CommandResult()
    
    for i in range(0, gt.ObjectCount):
        rhinoObject = gt.Object(i).Object()
        rhinoObjectType = gt.Object(i).Object.GetType()
        if not rhinoObject is None:
            if hasattr(rhinoObject.Geometry, "Text"):
                str = rhinoObject.Geometry.Text
                cstr = ConvTxt(str, boolFlipHeb)
                if not cstr == str:
                    rhinoObject.Geometry.Text = cstr
                    if hasattr(rhinoObject.Geometry, "Justification"):
                        jst = rhinoObject.Geometry.Justification
                        rhinoObject.Geometry.Justification = eval(JstFix(jst))
                    rhinoObject.CommitChanges();
                rhinoObject.Select(False)
            elif boolBlocks:
                BlockTxt(rhinoObject, False, False, boolFlipHeb)
    sc.doc.Views.Redraw()
    
    return Rhino.Commands.Result.Success

def SelAll(boolBlocks, boolFlipHeb):
    if boolBlocks: BlockTxtAll(boolFlipHeb)

    for rhinoObject in sc.doc.Objects.GetObjectList(ObjectType.Annotation):
        
        if not isinstance (rhinoObject, AnnotationObjectBase):
          continue
          
        str = rhinoObject.Geometry.Text
        cstr = ConvTxt(str, boolFlipHeb)
        
        if not rhinoObject is None:
            
            str = rhinoObject.Geometry.Text
            cstr = ConvTxt(str, boolFlipHeb)
            if not cstr == str:
                rhinoObject.Geometry.Text = cstr
                if hasattr(rhinoObject.Geometry, "Justification"):
                    jst = rhinoObject.Geometry.Justification
                    rhinoObject.Geometry.Justification = eval(JstFix(jst))
                rhinoObject.CommitChanges();
            rhinoObject.Select(False)
            
    sc.doc.Views.Redraw()
    return Rhino.Commands.Result.Success


    geoFilter = Rhino.DocObjects.ObjectType.Annotation
    gt = Rhino.Input.Custom.GetObject()
    gt.SetCommandPrompt("All Text Objects selected")
    
    gt.GeometryFilter = geoFilter
    gt.GroupSelect = True
    
    gt.GetMultiple(1,0)
    
    if gt.CommandResult()!=Rhino.Commands.Result.Success:
        return gt.CommandResult()
        
    for i in range(0, gt.ObjectCount):
        rhinoObject = gt.Object(i).Object()
        if not rhinoObject is None:
            str = rhinoObject.Geometry.Text
            cstr = ConvTxt(str, boolFlipHeb)
            if not cstr == str:
                rhinoObject.Geometry.Text = cstr
                if hasattr(rhinoObject.Geometry, "Justification"):
                    jst = rhinoObject.Geometry.Justification
                    rhinoObject.Geometry.Justification = eval(JstFix(jst))
                rhinoObject.CommitChanges();
            rhinoObject.Select(False)
            
    sc.doc.Views.Redraw()
    
    return Rhino.Commands.Result.Success

def SelSim(boolBlocks, boolFlipHeb):
    
    sc.doc.Objects.UnselectAll()
    sc.doc.Views.Redraw()
    geometryFilter = Rhino.DocObjects.ObjectType.Annotation

    gt = Rhino.Input.Custom.GetObject()
    gt.DisablePreSelect()
    gt.SetCommandPrompt("Select text for conversion")
    gt.GeometryFilter = geometryFilter
    gt.GroupSelect = False

    gt.GetMultiple(1, 1)
    
    if gt.CommandResult()!=Rhino.Commands.Result.Success:
        return gt.CommandResult()
    
    for i in range(0, gt.ObjectCount):
        rhinoObject = gt.Object(i).Object()
        if not rhinoObject is None:
            if hasattr(rhinoObject.Geometry, "Text"):
                str = rhinoObject.Geometry.Text
                cstr = ConvTxt(str, boolFlipHeb)
                if not cstr == str:
                    ReplaceAll(str, cstr)
            elif boolBlocks:
                BlockTxtSim(rhinoObject, boolFlipHeb)


#---------- EXECUTE ----------#

def RunCommand( is_interactive ):
    
    sc.doc.Objects.UnselectAll()
    sc.doc.Views.Redraw()

    go = Rhino.Input.Custom.GetOption()
    go.SetCommandPrompt("Gib2Heb Options")

    lstSelection = ["All", "BySelection", "AllSimilar"]
    opSelIndex = 0

    boolBlocks = Rhino.Input.Custom.OptionToggle(True, "No", "Yes")
    boolFlipHeb = Rhino.Input.Custom.OptionToggle(True, "No", "Yes")

    lstDecoders = strDecoders[:]
    lstDecoders.insert(0, "Auto")
    opDecIndex = 0

    lstEncoders = strDecoders[:]
    opEncIndex = len(lstEncoders)-1

    opSelection = go.AddOptionList("Selection", lstSelection, opSelIndex)
    opBlocks = go.AddOptionToggle("InsideBlocks", boolBlocks)
    opFlipHeb = go.AddOptionToggle("FlipHebrew", boolFlipHeb)
    opDecoding = go.AddOptionList("Decoding", lstDecoders, opDecIndex)
    opEncoding = go.AddOptionList("Encoding", lstEncoders, opEncIndex)

    while True:

        get_rc = go.Get()

        if go.CommandResult()!=Rhino.Commands.Result.Success:
            
            if opSelIndex == 0:
                SelAll(boolBlocks.CurrentValue, boolFlipHeb.CurrentValue)
            if opSelIndex == 1:
                SelMult(boolBlocks.CurrentValue, boolFlipHeb.CurrentValue)
            if opSelIndex == 2:
                SelSim(boolBlocks.CurrentValue, boolFlipHeb.CurrentValue)
            else:
                return Rhino.Commands.Result.Success

        elif get_rc==Rhino.Input.GetResult.Option:

            if go.OptionIndex()==opSelection:
              opSelIndex = go.Option().CurrentListOptionIndex
            if go.OptionIndex()==opDecoding:
              opDecIndex = go.Option().CurrentListOptionIndex
            if go.OptionIndex()==opEncoding:
              opEncIndex = go.Option().CurrentListOptionIndex
            continue

        break


RunCommand(True)
