import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (QMessageBox, QMainWindow, QApplication, QComboBox,
        QLabel, QWidget, QToolBar, QStatusBar, QDialog, QVBoxLayout, QGridLayout,
        QFileDialog)

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSize

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    # A different way of organizing an app.
    def initUI(self):

        self.setWindowTitle("Redcap Export App")

        layout = QGridLayout()

        layout.addWidget(QLabel('Select corresponding columns\nfrom your csv file\nfor each item.'), 0, 0)

        self.id_dropdown = QComboBox()
        self.visit_dropdown = QComboBox()
        self.donned_dropdown = QComboBox()
        self.doffed_dropdown = QComboBox()

        layout.addWidget(QLabel('id : '),          1, 0)
        layout.addWidget(self.id_dropdown,         1, 1)
        layout.addWidget(QLabel('visit number: '), 2, 0)
        layout.addWidget(self.visit_dropdown,      2, 1)
        layout.addWidget(QLabel('time donned: '),  3, 0)
        layout.addWidget(self.donned_dropdown,     3, 1)
        layout.addWidget(QLabel('time doffed: '),  4, 0)
        layout.addWidget(self.doffed_dropdown,     4, 1)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        toolbar = QToolBar("My main toolbar")
        toolbar.setIconSize(QSize(16,16))
        self.addToolBar(toolbar)

        # Icon to 'load' the file
        load_action = QAction(QIcon('icons8-opened-folder-48.png'), "&Load", self)
        load_action.setStatusTip("Loading the REDCap export file")
        load_action.triggered.connect(self.open_filediag)
        toolbar.addAction(load_action)

        # Icon to 'convert' the file
        convert_action = QAction(QIcon('icons8-update-left-rotation-48.png'), "&Convert", self)
        convert_action.setStatusTip("Converting the REDCap export file")
        convert_action.triggered.connect(self.file_convert)
        toolbar.addAction(convert_action)

        # setting a status bar
        self.setStatusBar(QStatusBar(self))

        # It seems like Mac forces the menu bar to appear at the top, no matter what
        # So switching to a button
        #menu = self.menuBar()
        #file_menu = menu.addMenu("&File")
        #file_menu.addAction(load_action)
        #file_menu.addSeparator()

        self.show()

    def open_filediag(self, s):
        # You will be opening a file dialogue to search for the file
        dialog = QFileDialog(self)
        dialog.exec()
        self.fileNames = dialog.selectedFiles()

        ## load the file as well
        self.dt = pd.read_csv(self.fileNames[0])
        cols = self.dt.columns

        # Then fill in the dropdown menus with the column names of the original csv file
        self.id_dropdown.addItems(cols)
        self.visit_dropdown.addItems(cols)
        self.donned_dropdown.addItems(cols)
        self.doffed_dropdown.addItems(cols)

    def file_convert(self):
        # Columns Of InterestS
        # Currently, the order should be [id, visit number, time donned, time dofed]
        cois = [self.id_dropdown.currentText(), self.visit_dropdown.currentText(),
                self.donned_dropdown.currentText(), self.doffed_dropdown.currentText()]
        # Get the subset
        temp = self.dt.loc[:, cois]
        # change the column names to what we want
        out = temp.rename(columns={cois[0]: 'id', cois[1]: 'visit_num', cois[2]: 'time_donned', cois[3]: 'time_doffed'})

        # It is better to save it at the current working directory
        curdir = os.path.abspath(os.curdir)
        out.to_csv('/'.join([curdir, 'extracted_times.csv']), index=False)
        # If things went well, throw out a message
        msg = QMessageBox(self)
        msg.setWindowTitle("Important Message")
        msg.setText("Conversion completed")
        msg.exec()

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
