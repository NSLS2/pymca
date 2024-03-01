#/*##########################################################################
#
# The PyMca X-Ray Fluorescence Toolkit
#
# Copyright (c) 2004-2023 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#############################################################################*/
__author__ = "V.A. Sole - ESRF"
__contact__ = "sole@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
import sys
import os
import numpy
try:
    # try to import hdf5plugin
    import hdf5plugin
except Exception:
    # but do not crash just because of it
    pass
import h5py
from operator import itemgetter
import re
import posixpath
import logging
phynx = h5py

if sys.version_info >= (3,):
    basestring = str

from . import DataObject
from . import NexusTools
from .NexusDataSource import *

from . import TiledToools

SOURCE_TYPE = "TILED"

def isTiledDataSource(filename):
    if 'http' in filename:
        return True
        #FIXME: this should be done better...

class TiledDataSource(NexusDataSource):
    def __init__(self,nameInput):
        print("TiledDataSource__init__")
        super().__init__(nameInput) 
    
    def refresh(self):
        print("TiledDataSource refresh")
        for instance in self._sourceObjectList:
            instance.close()
        self._sourceObjectList=[]
        #for name in self.__sourceNameList:
        #    if True: #FIXME: maybe some check to be done here?
        #        self._sourceObjectList.append(name)
        #        continue
        for name in self._NexusDataSource__sourceNameList:
            phynxInstance = TiledToools.TiledAdaptor(name)
            phynxInstance._sourceName = name
            self._sourceObjectList.append(phynxInstance)
        self.__lastKeyInfo = {}

source_types = { SOURCE_TYPE: TiledDataSource}

#def DataSource(name="", source_type=SOURCE_TYPE):
#  try:
#     sourceClass = source_types[source_type]
#  except KeyError:
     #ERROR invalid source type
#     raise TypeError("Invalid Source Type, source type should be one of %s" %\
#                     source_types.keys())
#  return sourceClass(name)

