import numpy as np
import time
import sys

from PyMca5.PyMcaCore import DataObject
from PyMca5.PyMcaGui.io.TiledDataChannelTable import TiledDataChannelTable
from PyMca5.PyMcaGui.io.QTiledWidget import TiledBrowser

SOURCE_TYPE = 'Tiled'

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
        print("-------- TiledDataSource init")
        if isinstance(nameInput, list):
            nameList = nameInput
        else:
            nameList = [nameInput]
        self.sourceName = nameList
        self.sourceType = SOURCE_TYPE
        self.__sourceNameList = self.sourceName
        self.refresh()

    def refresh(self):
        pass
       

    def _set_key(self):
        """Sets key once a scan has been selected in Tiled Browser."""
        
        selection = TiledBrowser.set_data_source_key()
        key = {
            "scan": selection.metadata['start']['uid'],
            "scan_id": selection.metadata['start']['scan_id'],
            "streams": list(selection),
            "selection": selection, 
        }

        return key
    
    def _set_data_channel_selection(self):
        """Retrieve Data Channel Selections from Tiled Data Channel Table."""
        print("-------- TiledDataSource _set_data_channel_selection")
        channel_sel = TiledDataChannelTable.getChannelSelection()
        self.chan_sel = {
            'x': channel_sel['x'],
            'y': channel_sel['y'],
            'm': channel_sel['m'],
            'Channel List': channel_sel['Data Channel List'],
        }
    
    def _get_key_info(self, selection):
        """Retrives key info."""

        key = self._set_key()
        key_info = {
            "SourceType": SOURCE_TYPE,
            "selection": selection,
            "key": key,
        }

        return key_info
    
    def get_data_object(self, key, selection=None):
        """Generate a dataObject that will be used to plot scan data."""
        print("-------- TiledDataSource get_data_object")
        dataObject = DataObject.DataObject()
        dataObject.info = self._get_key_info(selection)
        dataObject.data = key['selection']

        chan_sel = self.chan_sel

        # What data.info attributes to add?
        dataObject.info['selection'] = selection
        
        # data = [key['selection']][datachannel][data]
        # If data channel selected in x axis go to data and time
        dataObject.data.x = dataObject.data.chan_sel['x']['data']['time']
        # If data channel selected in y axis plot everything
        dataObject.data.y = dataObject.data.chan_sel['y']['data']
        # If data selected in m divide y by m and plot
        dataObject.data.m = dataObject.data.chan_sel['m']['data']

        return dataObject

    def isUpdated(self,key):
        pass
    
    
def _is_Tiled_Source(filename):
    try:
        if hasattr(filename, self.node_path):
            return True
    except Exception:
        return False
    
source_types = {SOURCE_TYPE: TiledDataSource}

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
        