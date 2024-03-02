from tiled.client import from_uri

##fixme ... needs arg to connect to corret service
#def get_tiled_connection():
#    return from_uri("https://tiled-demo.blueskyproject.io")

class TiledAdaptor(object):
    def __init__(self,host,prefix=''):
        print("init TiledAdaptor",host)
        self._client = from_uri(host)
        self.__sourceName=''
        self.__prefixed=prefix
        print(self._client)

    @property
    def client(self):
        return self._client
    
    @property
    def _sourceName(self):
        return self.__sourceName
    
    @_sourceName.setter
    def _sourceName(self,sn):
        self.__sourceName = sn

    def close(self):
        #not sure if there is anything that needs to happen here
        return
    
    def getSourceInfo(self):
        """
        Returns a dictionary with the key "KeyList" (list of all available keys
        in this source). Each element in "KeyList" has the form 'n1.n2' where
        n1 is the source number and n2 entry number in file both starting at 1.
        """
        print("TiledAdaptor getSourceInfo")
        return {"KeyList":["1.1"]}
    
    @property
    def name(self):
        return "/"
    
    @property
    def filename(self):
        return "toto"