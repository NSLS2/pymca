import enable_pymca_import  # noqa: F401

from PyMca5.PyMcaCore.TiledDataSource import TiledDataSource


def test_source_init():
    """Can create a TiledDataSource object."""
    TiledDataSource()


def test_refresh_method_exists():
    """TiledDataSource has a callable refresh) method."""
    source = TiledDataSource()
    source.refresh()
