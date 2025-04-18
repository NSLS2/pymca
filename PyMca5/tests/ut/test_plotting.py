import enable_pymca_import  # noqa: F401

from unittest.mock import Mock, call, patch

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

    with patch.object(data_channel_table, "sigTiledDataChannelTableSignal") as mock_signal:
        mock_signal.emit = Mock()

        # Mark items as checked
        for i in range(data_channel_table.rowCount()):
            widget = data_channel_table.cellWidget(i, i + 1)
            widget.setChecked(True)
            data_channel_table._mySlot({"row": i, "col": i + 1, "state": True})

            # sigTiledDataChannelTableSignal should be emitted once every time
            # we call _mySlot
            assert mock_signal.emit.call_count == i + 1

        # Check items marked as checked in QTiledDataChannelTable
        assert data_channel_table.xSelection == [0]
        assert data_channel_table.ySelection == [1]
        assert data_channel_table.monSelection == [2]


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
