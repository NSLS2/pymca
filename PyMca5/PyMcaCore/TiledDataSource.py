SOURCE_TYPE = 'Tiled'

class TiledDataSource(object):
    def __init__(self, name):
        self.name = name
        self.sourceName = name
        self.source_type = SOURCE_TYPE
        