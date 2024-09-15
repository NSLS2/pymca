import enable_pymca_import  # noqa: F401

from PyMca5.PyMcaGui.io.TiledCatalogSelector import TiledCatalogSelector


def test_init():
    """Can create a TiledCatalogSelector object."""
    TiledCatalogSelector()
