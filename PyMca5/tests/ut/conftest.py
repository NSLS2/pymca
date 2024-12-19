import enable_pymca_import  # noqa: F401

import pytest

import numpy
from PyQt5.QtWidgets import QApplication
from tiled.server.app import build_app
from tiled.client import Context, from_context
from tiled.client.base import BaseClient
from tiled.adapters.array import ArrayAdapter
from tiled.adapters.mapping import MapAdapter

from PyMca5.PyMcaGui.io.TiledCatalogSelector import TiledCatalogSelector


tree = MapAdapter(
    {
        "a": ArrayAdapter.from_array(
            numpy.arange(10), metadata={"apple": "red", "animal": "dog"}
        ),
        "b": ArrayAdapter.from_array(
            numpy.arange(10), metadata={"banana": "yellow", "animal": "dog"}
        ),
        "c": ArrayAdapter.from_array(
            numpy.arange(10), metadata={"cantalope": "orange", "animal": "cat"}
        ),
        "d": ArrayAdapter.from_array(
            numpy.arange(10), metadata={"durian": "green", "animal": "turtle"}
        ),
        "e": ArrayAdapter.from_array(
            numpy.arange(10), metadata={"elderberry": "purple", "animal": "cat"}
        ),
        "f": ArrayAdapter.from_array(
            numpy.arange(10), metadata={"fig": "purple", "animal": "cat"}
        ),
        "structured_data": MapAdapter(
        {
            "pets": ArrayAdapter.from_array(
                numpy.array(
                    [("Rex", 9, 81.0), ("Fido", 3, 27.0)],
                    dtype=[("name", "U10"), ("age", "i4"), ("weight", "f4")],
                )
            ),
            "people": ArrayAdapter.from_array(
                numpy.array(
                    [("Alice", 24), ("Bob", 37)],
                    dtype=[("name", "U10"), ("age", "i4")],
                )
            ),
        },
        metadata={"animal": "cat", "color": "green"},
    ),
    }
)


@pytest.fixture(scope="module")
def tiled_client():
    """A fully functional Tiled client suitable for tests."""
    app = build_app(tree)
    with Context.from_app(app) as context:
        client = from_context(context)
        yield client


# TODO: This fixture should probably be renamed or moved back to the test module
#       where it more clearly referred to a model for QTiledCatalogSelectorDialog
@pytest.fixture
def dialog_model(qapp: QApplication):
    """TiledCatalogSelector that is compatible with QtBot-based tests."""
    model = TiledCatalogSelector(parent=qapp)
    yield model


@pytest.fixture
def tiled_client_dialog_model(qapp: QApplication, tiled_client: BaseClient):
    """TiledCatalogSelector that is compatible with QtBot-based tests."""
    model = TiledCatalogSelector(parent=qapp, client=tiled_client)
    yield model
