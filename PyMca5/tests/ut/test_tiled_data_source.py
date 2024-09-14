from collections import abc

import enable_pymca_import  # noqa: F401
import pytest

from PyMca5.PyMcaCore.DataObject import DataObject
from PyMca5.PyMcaCore.TiledDataSource import SOURCE_TYPE, TiledDataSource


def test_init():
    """Can create a TiledDataSource object."""
    TiledDataSource()


def test_source_type():
    """TiledDataSource.SOURCE_TYPE is defined and contains "tiled"."""
    assert isinstance(SOURCE_TYPE, str)
    assert "tiled" in SOURCE_TYPE.lower()


def test_getDataObject():
    """TiledDataSource has a callable getDataObject method."""
    source = TiledDataSource()
    source.getDataObject("This key value is not used by this test")


def test_getDataObject_values():
    """TiledDataSourceg.getDataObject method returns a valid DataObject."""
    source = TiledDataSource()

    data = source.getDataObject("This key value is not used by this test")
    assert isinstance(data, DataObject)

    info = data.info

    labels = info["LabelNames"]
    assert isinstance(labels, abc.Sequence)
    assert all(isinstance(label, str) for label in labels)

    info["selection"]

    sel_type = info["selectiontype"]
    assert isinstance(sel_type, str)
    allowed_types = ("1D",)
    assert sel_type in allowed_types

###############################################################################
# OPTIONAL METHODS
# 
# A similar convention is followed on other DataSources for convience
# but PyMca app does not depend on these being available.
###############################################################################

def test_refresh():
    """TiledDataSource has a callable refresh method."""
    source = TiledDataSource()
    source.refresh()


@pytest.mark.xfail(reason="Method not yet needed")
def test_getSourceInfo():
    """TiledDataSource has a callable getSourceInfo method."""
    source = TiledDataSource()
    source.getSourceInfo()


@pytest.mark.xfail(reason="Method not yet needed")
def test_getSourceInfo_values():
    """TiledDataSource.getSourceInfo method returns a valid mapping."""
    source = TiledDataSource()
    info = source.getSourceInfo()
    # These fields are generally defined by other DataSources
    info["SourceName"]
    assert info["SourceType"] == SOURCE_TYPE
    info["KeyList"]
    info["Size"]


@pytest.mark.xfail(reason="Method not yet needed")
def test_getKeyInfo():
    """TiledDataSource has a callable test_getKeyInfo method."""
    source = TiledDataSource()
    source.getKeyInfo("This key value is not used by this test")


@pytest.mark.xfail(reason="Method not yet needed")
def test_getKeyInfo_values():
    """TiledDataSource.getKeyInfo method returns a valid mapping."""
    source = TiledDataSource()
    info = source.getKeyInfo("This key value is not used by this test")
    # These fields are generally defined by other DataSources
    info["SourceName"]
    assert info["SourceType"] == SOURCE_TYPE
    info["Key"]
