import enable_pymca_import  # noqa: F401

from pytestqt.qtbot import QtBot
from tiled.client.base import BaseClient

from PyMca5.PyMcaGui.io.QTiledDataChannelTable import QTiledDataChannelTable


def test_selected_items_in_data_channel_table(qtbot: QtBot):
    """Checked items in data channel table are selected."""
    # Create data channel table
    data_channel_table = QTiledDataChannelTable()
    data_channel_table.show()
    qtbot.addWidget(data_channel_table)

    channel_list = ["a", "b", "c"]

    data_channel_table.clear_table()
    data_channel_table.build_table(channel_list)

    # Mark items as checked
    for i in range(data_channel_table.rowCount()):
        widget = data_channel_table.cellWidget(i, i + 1)
        widget.setChecked(True)

    # FIXME: failing test, x(y/mon)Selection not being set yet

    # Check items marked as checked in QTiledDataChannelTable
    assert data_channel_table.xSelection == ["a"]
    assert data_channel_table.ySelection == ["b"]
    assert data_channel_table.monSelection == ["c"]

    # sigTiledDataChannelTableSignal emitted here


def test_add_button_gets_plottable_data(qtbot: QtBot):
    """Add button gets data that can be plotted."""
    # Create data channel table

    # Mark items as checked

    # Click ADD

    # data channel table should getChannelSelection

    # Check that data is coming out in a way that can be plotted
    # i.e. data_names, x_selection, y_selection, m_selection
    # Check that items appear in selected items in model
    # assert model.
    # ddict = {
    #         "Data Channel List": self.dataChannelList[:],
    #         'x': self.xSelection[:],
    #         'y' : self.ySelection[:],
    #         'm' : self.monSelection[:],
    #     }

    # Check sigAddSelection emitted with list of:
    # 'SourceName', 'SourceType', 'selection', 'scanselection'
    ...
