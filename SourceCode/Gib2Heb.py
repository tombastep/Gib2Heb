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


#---------- IMPORTS ----------#

# Rhino imports
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
from Rhino.Geometry import *

# Python Imports
import re
import string
import System

# Bidi Imports
from algorithm import get_display


#---------- DEFINE CHARSETS & DECODERS ----------#

rgx = "^[A-Za-z0-9.,:;!?=\[\]\{\}|\' `~\"@%&*$<>()\/s]+$"
hebChrs = "אבגדהוזחטיכךלמםנןסעפףצץקרשת"
strEncode = "cp1255"
strDecoders = ["cp862", "cp856", "cp424", "iso8859_8", "cp1255"]

#---------- FUNCTIONS ----------#

def isHeb(s): #Identify how many strings 
    s = ''.join(s.split())
    i = 0
    for c in s:
        if c >= u"\u0590" and c <= u"\u05EA":
            i = i+1
    return i


def isEng(s):
    s = ''.join(s.split())
    if not re.match('^[0-9.,:;!?()\/s]+$', s):
        engheb = re.match(rgx, s)
        return engheb
    else: return False


def Eng2Heb(s):

    INPUT = "qwertyuiopasdfghjkl;zxcvbnm,."
    OUTPUT = "/'קראטוןםפשדגכעיחלךףזסבהנמצתץ"
    sn = ''.join(s.split())
    
    if not re.match(rgx, sn):
        return s
    
    else:
        TABLE = string.maketrans(INPUT,OUTPUT) 
        result = s.translate(TABLE)
        return result


def usebidi(cnvStr): 
    return get_display(u'' + cnvStr, upper_is_rtl=False, encoding=strEncode debug=False)


def ConvTxt(str):

    cnvStr = str
    
    if isEng(cnvStr): return Eng2Heb(str)
    
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
        return usebidi(cnvStr)
    else: return str


def JstFix(s):
    s = s.ToString()
    result = string.replace(s, 'Left', 'Right')
    if result == s: result = string.replace(s, 'Right', 'Left')
    return "TextJustification." + result 

#---------- EXECUTE ----------#

def RunCommand( is_interactive ):
    geometryFilter = Rhino.DocObjects.ObjectType.Annotation
    go = Rhino.Input.Custom.GetObject()
    go.SetCommandPrompt("Select text objects to convert")
    go.GeometryFilter = geometryFilter
    go.GroupSelect = True
    go.GetMultiple(1, 0)
    if go.CommandResult()!=Rhino.Commands.Result.Success:
        return go.CommandResult()
        
    for i in range(0, go.ObjectCount):
        rhinoObject = go.Object(i).Object()
        if not rhinoObject is None:
            str = rhinoObject.Geometry.Text
            cstr = ConvTxt(str)
            if not cstr == str:
                rhinoObject.Geometry.Text = cstr
                if hasattr(rhinoObject.Geometry, "Justification"):
                    jst = rhinoObject.Geometry.Justification
                    rhinoObject.Geometry.Justification = eval(JstFix(jst))
                rhinoObject.CommitChanges();
            rhinoObject.Select(False)
            
    sc.doc.Views.Redraw()
    
    return Rhino.Commands.Result.Success

RunCommand(True)
