import enable_pymca_import  # noqa: F401

import numpy

import pytest

from PyQt5.QtWidgets import QApplication

from tiled.server.app import build_app
from tiled.client import Context, from_context
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
    }
)


@pytest.fixture(scope="module")
def client():
    app = build_app(tree)
    with Context.from_app(app) as context:
        client = from_context(context)
        yield client


@pytest.fixture
def dialog_model(qapp: QApplication):
    model = TiledCatalogSelector(parent=qapp)
    yield model
