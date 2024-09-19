import copy

from .DataObject import DataObject


SOURCE_TYPE = "Tiled"


class TiledDataSource(object):
    """Manages a Tiled CatalogOfBlueskyRuns as a PyMca Data Source"""
    def getDataObject(self, key: str, selection=None):
        """Return data associated with 'key' and optional 'selection'."""
        data = DataObject()
        labels = ()
        if selection is not None:
            labels = selection["Channel List"].copy()
        data.info = {
            # For now, only allow one-dimensional data arrays
            "selectiontype": "1D",
            # ScanWindow expects to modify this copy of "selection"
            # TODO: It might be cleaner to leave this key undefined
            #       and instead let ScanWindow create + modify what it needs
            "selection": copy.deepcopy(selection),
            "LabelNames": labels,
        }
        data.x = ()
        data.y = ()
        data.m = ()

        return data

    def refresh(self):
        ...
