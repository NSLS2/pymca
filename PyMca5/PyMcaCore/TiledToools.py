from tiled.client import from_uri

#fixme ... needs arg to connect to corret service
def get_tiled_connection():
    return from_uri("https://tiled-demo.blueskyproject.io")