import enable_pymca_import  # noqa: F401

from unittest.mock import Mock, call, patch

from pytestqt.qtbot import QtBot

from PyMca5.PyMcaGui.io.TiledRunSelector import TiledRunSelector
from PyMca5.PyMcaGui.io.QTiledDataChannelTable import QTiledDataChannelTable
from PyMca5.PyMcaGui.io.QTiledWidget import QTiledWidget


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
            # The 0 column is the name of the channel
            widget = data_channel_table.cellWidget(i, i + 1)
            # User clicks the checkbox, which is a CheckBoxItem
            widget.click()

            # sigTiledDataChannelTableSignal should be emitted once every time
            # we click a checkbox
            assert mock_signal.emit.call_count == i + 1

        # Check items marked as checked in QTiledDataChannelTable
        assert data_channel_table.xSelection == [0]
        assert data_channel_table.ySelection == [1]
        assert data_channel_table.monSelection == [2]


def test_add_button_gets_plottable_data(
        qtbot: QtBot,
        tiled_client_run_selector_model: TiledRunSelector
):
    """Add button gets data that can be plotted."""
    widget = QTiledWidget(model=tiled_client_run_selector_model)
    widget.show()
    qtbot.addWidget(widget)

    # Create data channel table
    widget.data_channel_table.setVisible(True)
    widget.data_channel_table.format_table()
    widget.command_button_widget.setVisible(True)

    channel_list = ["a", "b", "c"]

    widget.data_channel_table.clear_table()
    widget.data_channel_table.build_table(channel_list)

    # Mark items as checked
    for i in range(widget.data_channel_table.rowCount()):
        cell_widget = widget.data_channel_table.cellWidget(i, i + 1)
        cell_widget.click()

    # Click ADD
    widget.add_button.click()  # TODO: this is not connected to anything yet
    # TODO: Maybe here we can just set the x(y/mon)Selection lists instead
    # of creating the entire QTiledWidget

    # data channel table should getChannelSelection

    # Check that data is coming out in a way that can be plotted
    # i.e. data_names, x_selection, y_selection, m_selection

    # Check sigAddSelection emitted with list of:
    # {
    #     'SourceName': self.data.sourceName,
    #     'SourceType': self.data.sourceType,
    #     'Key': self.node_path,
    #     'legend': '/'.join(self.node_path),
    #     'selection': {'x': channel_sel['x'],
    #                     'y': channel_sel['y'],
    #                     'm': channel_sel['m'],
    #                     'Channel List': channel_sel['Data Channel List']},
    #     'scanselection': True,
    # }
    ...
