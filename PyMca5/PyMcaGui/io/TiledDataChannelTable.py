from PyQt5 import QtWidgets

from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.io.SpecFileCntTable import CheckBoxItem

class TiledDataChannelTable(qt.QTableWidget):
    """
    Creates the data channel table (second table) inside the QTiledWidget.
    The selections for the x and y set the axes in the scan window.
    """
    sigTiledDataChannelTableSignal = qt.pyqtSignal(object)
    def __init__(self, parent=None):
        qt.QTableWidget.__init__(self, parent)
        self.dataChannelList = []
        self.xSelection = []
        self.ySelection = []
        self.monSelection = []
        
    def format_table(self):
        """Sets the column headers and the size of the columns for the table."""
        
        # Column Labels
        labels = ['Data Channel', 'x', 'y', 'Mon']
        self.setColumnCount(len(labels))
        for i in range(len(labels)):
            item = self.horizontalHeaderItem(i)
            if item is None:
                item = qt.QTableWidgetItem(labels[i])
            item.setText(labels[i])
            self.setHorizontalHeaderItem(i, item)

    def clear_table(self):
        """Clears the table if a different scan is selected."""
        # Clear contents of the table
        self.setRowCount(0)
        self.setColumnCount(0)

        # Reset internal state
        self.dataChannelList = []
        self.xSelection = []
        self.ySelection = []
        self.monSelection = []

        self.format_table()

    def build_table(self, channelList):
        """
        Builds the table in QTiledWidget based on the datachannels in selected
        scan file.
        """
        self.dataChannelList = channelList
        n = len(channelList)
        self.setRowCount(n)
        if n > 0:
            for i in range(n):
                self._addLine(i, channelList[i])

    def _addLine(self, i, channelLabel):
        """
        Adds individual line to Data Channel Table based on the label of the
        Data Channel in the scan file.
        """
        # Data Channel name
        item = self.item(i, 0)
        if item is None:
            item = qt.QTableWidgetItem(channelLabel)
            item.setTextAlignment(qt.Qt.AlignHCenter | qt.Qt.AlignVCenter)
            self.setItem(i, 0, item)
        else:
            item.setText(channelLabel)
        
        # Data Channel name is not selectable
        item.setFlags(qt.Qt.ItemIsEnabled)

        # Checkboxes
        for j in range(1, 4):
            widget = self.cellWidget(i, j)
            if widget is None:
                widget = CheckBoxItem(self, i, j)
                self.setCellWidget(i, j, widget)
                widget.sigCheckBoxItemSignal.connect(self._mySlot)
            else:
                pass

            # Resize columns to fit contents
        self.resizeColumnsToContents()

        # Stretch Columns to fill the table
        column_count = self.columnCount()
        for column in range(column_count):
            self.horizontalHeader().setStretchLastSection(True)
            self.horizontalHeader().setSectionResizeMode(column, QtWidgets.QHeaderView.Stretch)

    def _mySlot(self, ddict):
        row = ddict["row"]
        col = ddict["col"]
        
        # 'x' column
        if col == 1:
            if ddict["state"]:
                if row not in self.xSelection:
                    self.xSelection.append(row)
            else:
                if row in self.xSelection:
                    del self.xSelection[self.xSelection.index(row)]
        # 'y' column
        if col == 2:
            if ddict["state"]:
                if row not in self.ySelection:
                    self.ySelection.append(row)
            else:
                if row in self.ySelection:
                    del self.ySelection[self.ySelection.index(row)]

        # 'Mon' column
        if col == 3:
            if ddict["state"]:
                if row not in self.monSelection:
                    self.monSelection.append(row)
            else:
                if row in self.monSelection:
                    del self.monSelection[self.monSelection.index(row)]

        self._update()

    def _update(self):
        for i in range(self.rowCount()):
            
            # 'x' column
            j = 1
            widget = self.cellWidget(i, j)
            if i in self.xSelection:
                if not widget.isChecked():
                    widget.setChecked(True)
            else:
                if widget.isChecked():
                    widget.setChecked(False)
            
            # 'y' column
            j = 2
            widget = self.cellWidget(i, j)
            if i in self.ySelection:
                if not widget.isChecked():
                    widget.setChecked(True)
            else:
                if widget.isChecked():
                    widget.setChecked(False)

            # 'Mon' column
            j = 3
            widget = self.cellWidget(i, j)
            if i in self.monSelection:
                if not widget.isChecked():
                    widget.setChecked(True)

            else:
                if widget.isChecked():
                    widget.setChecked(False)

        ddict = {"event": "updated"}
        self.sigTiledDataChannelTableSignal.emit(ddict)

    def getChannelSelection(self):
        ddict = {
            "Data Channel List": self.dataChannelList[:],
            'x': self.xSelection[:],
            'y' : self.ySelection[:],
            'm' : self.monSelection[:],
        }
   
        return ddict
    
    def setChannelSelection(self, ddict):
        dataChannelList = ddict.get("DataChannel List", self.dataChannelList[:])

        self.xSelection = [item for item in ddict.get('x', []) if item < len(dataChannelList)]
        self.ySelection = [item for item in ddict.get('y', []) if item < len(dataChannelList)]
        self.monSelection = [item for item in ddict.get('m', []) if item < len(dataChannelList)]

        self._update()

def main():
    app = qt.QApplication([])
    table = TiledDataChannelTable()
    table.build_table(['Ch1', 'Ch2', 'Ch3'])
    table.setChannelSelection({'x': [1,2], 'y':[4], 'ChList': ['dummy', 'Ch0', 'Ch1', 'Ch2', 'Ch3']})
    table.show()
    app.exec()

if __name__ == "__main__":
    main()
