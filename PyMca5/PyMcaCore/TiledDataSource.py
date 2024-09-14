from .DataObject import DataObject


class TiledDataSource(object):
    """Manages a Tiled CatalogOfBlueskyRuns as a PyMca Data Source"""
    def getDataObject(self, key: str, selection=None):
        """Return data associated with 'key' and optional 'selection'."""
        return DataObject()

    def refresh(self):
        ...
