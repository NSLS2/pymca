import logging
import numpy as np
import os
import time
import sys

from PyMca5.PyMcaCore import DataObject
from PyMca5.PyMcaIO import TiledFile

SOURCE_TYPE = 'Tiled'

_logger = logging.getLogger(__name__)

class TiledDataSource(object):
    """
    Creates instance of a Tiled Data Source class. This is neccesary
    to create a Tiled Tab in the QDispatcher, which houses the Tiled
    Browser.

    This is largely based on the NexusDataSource class, but all Data 
    Source tabs (Spec, EDF, SPS) have an analogous class.

    See QDataSource.py
    """

    def __init__(self, nameInput):
        if isinstance(nameInput, list):
            nameList = nameInput
        else:
            nameList = [nameInput]
        self.sourceName = nameList
        self.source_type = SOURCE_TYPE
        self.__sourceNameList = self.sourceName
        self._sourceObjectList = []
        self.refresh()

    def refresh(self):
        self._sourceObjectList = []
        for name in self.__sourceNameList:
            self._sourceObjectList.append(TiledFile.TiledFile(name))
        self.__lastKeyInfo = {}

    def getSourceInfo(self):
        """
        Returns a dictionary with the key "KeyList" (list of all available keys
        in this source). Each element in "KeyList" has the form 'n1.n2' where
        n1 is the source number and n2 entry number in file both starting at 1.
        """
        return self.__getSourceInfo()
    
    def __getSourceInfo(self):
        SourceInfo = {}
        SourceInfo["SourceType"] = SOURCE_TYPE
        SourceInfo["KeyList"] = []
        i = 0
        for sourceObject in self._sourceObjectList:
            i += 1
            nEntries = len(sourceObject["/"].keys())
            for n in range(nEntries):
                SourceInfo["KeyList"].append("%d.%d" % (i,n+1))
        SourceInfo["Size"] = len(SourceInfo["KeyList"])
        return SourceInfo
    
    def getKeyInfo(self, key):
        if key in self.getSourceInfo()['KeyList']:
            return self.__getKeyInfo(key)
        else:
            #should we raise a KeyError?
            _logger.debug("Error key not in list ")
            return {}

    def __getKeyInfo(self, key):
        try:
            index, entry = key.split(".")
            index = int(index) - 1
            entry = int(entry) - 1
        except Exception:
            #should we rise an error?
            _logger.debug("Error trying to interpret key = %s", key)
            return {}
        
        sourceObject = self._sourceObjectList[index]
        
        info = {
            "SourceType": SOURCE_TYPE,
            "SourceName": self.sourceName[index],
            "Key": key,
            "FileName": sourceObject.name,
        }

        return info
    
    def getDataObject(self, key, selection=None):
        data = DataObject.DataObject()
        index, entry = key.split(".")
        index = int(index) - 1
        entry = int(entry) - 1

        data.info = self.__getKeyInfo(key)
        data.info['selection'] = selection

        sourceObject = self._sourceObjectList[index]
        data.data = sourceObject.getData()

    def isUpdated(self, sourceName, key):
        #sourceName is redundant?
        index, entry = key.split(".")
        index = int(index)-1
        lastmodified = os.path.getmtime(self.__sourceNameList[index])
        if lastmodified != self.__lastKeyInfo[key]:
            self.__lastKeyInfo[key] = lastmodified
            return True
        else:
            return False

source_types = { SOURCE_TYPE: TiledDataSource}

def DataSource(name="", source_type=SOURCE_TYPE):
  try:
     sourceClass = source_types[source_type]
  except KeyError:
     #ERROR invalid source type
     raise TypeError("Invalid Source Type, source type should be one of %s" %\
                     source_types.keys())
  return sourceClass(name)


if __name__ == "__main__":
    try:
        sourcename = sys.argv[1]
        key = sys.argv[2]
    except Exception:
        print("Usage: TiledDataSource <file> <key>")
        sys.exit()
    #one can use this:
    obj = TiledDataSource(sourcename)
    #or this:
    obj = DataSource(sourcename)
    #data = obj.getData(key,selection={'pos':(10,10),'size':(40,40)})
    #data = obj.getDataObject(key,selection={'pos':None,'size':None})
    t0 = time.time()
    data = obj.getDataObject(key,selection=None)
    print("elapsed = ",time.time() - t0)
    print("info = ",data.info)
    if data.data is not None:
        print("data shape = ",data.data.shape)
        print(np.ravel(data.data)[0:10])
    else:
        print(data.y[0].shape)
        print(np.ravel(data.y[0])[0:10])
    data = obj.getDataObject('1.1',selection=None)
    r = int(key.split('.')[-1])
    print(" data[%d,0:10] = " % (r-1),data.data[r-1   ,0:10])
    print(" data[0:10,%d] = " % (r-1),data.data[0:10, r-1])
        