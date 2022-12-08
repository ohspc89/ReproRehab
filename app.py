import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (QMessageBox, QMainWindow, QApplication, QComboBox,
        QLabel, QWidget, QToolBar, QStatusBar, QDialog, QVBoxLayout, QGridLayout,
        QFileDialog, QPushButton)

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSize

basedir = os.path.dirname(__file__)
workdir = os.path.abspath(os.curdir)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Title of the main window
        self.setWindowTitle("Sensor Data Analysis App")
        self.initUI()

    def initUI(self):
        l = QVBoxLayout()       # Box layout
        button = QPushButton("Extract times sensors were worn")
        button.clicked.connect(self.show_redcap_window)
        l.addWidget(button)     # add the button to the widget

        button2 = QPushButton("Preprocess h5 file(s)")
        button2.clicked.connect(self.show_preprocess_window)
        l.addWidget(button2)

        widget = QWidget()
        widget.setLayout(l)
        self.setCentralWidget(widget)

        #self.setStatusBar(QStatusBar(self))

        self.w = None       # This is to check if the new window has been opened
        self.w2 = None

        self.show()

    def show_redcap_window(self, checked):
        if self.w is None:
            self.w = ConvertWindow(self)
        self.w.show()

    def show_preprocess_window(self, checked):
        if hasattr(self, 'out'):
            print('out exists')
        else:
            print('redcap not yet processed')
        

# This is the window that will handle the conversion of a REDCap data export
# to whatever csv file we want for further preprocessing
class ConvertWindow(QMainWindow):

    def __init__(self, parent):
        super(ConvertWindow, self).__init__(parent)
        self.initUI()
        self.parent = parent
        print(self.parent)

    def initUI(self):

        self.setWindowTitle("Extract times from Redcap")

        layout = QGridLayout()
        #self.setLayout(layout)

        layout.addWidget(QLabel('Select corresponding columns\nfrom your csv file for each item.'), 1, 0)

        self.id_dropdown = QComboBox()
        self.fname_dropdown = QComboBox()
        self.donned_dropdown = QComboBox()
        self.doffed_dropdown = QComboBox()

        layout.addWidget(QLabel('id : '), 2, 0)
        layout.addWidget(self.id_dropdown, 2, 1)
        layout.addWidget(QLabel('filename: '), 3, 0)
        layout.addWidget(self.fname_dropdown, 3, 1)
        layout.addWidget(QLabel('time donned: '), 4, 0)
        layout.addWidget(self.donned_dropdown, 4, 1)
        layout.addWidget(QLabel('time doffed: '), 5, 0)
        layout.addWidget(self.doffed_dropdown, 5, 1)

        widget = QWidget()
        widget.setLayout(layout)            # so I think you should have a widget to place a layout
        self.setCentralWidget(widget)       # and in a window you centre the widget

        # setting a status bar
        self.setStatusBar(QStatusBar(self))

        # setting a toolbar - see that this is located at the top (0,0) of the grid layout
        toolbar = QToolBar("My main toolbar")
        toolbar.setIconSize(QSize(16,16))
        #layout.addWidget(toolbar, 0, 0)
        self.addToolBar(toolbar)

        # Icon to 'load' the file
        load_action = QAction(QIcon(os.path.join(basedir, 'icons', 'icons8-opened-folder-48.png')), "&Load", self)
        load_action.setStatusTip("Loading the REDCap export file")
        load_action.triggered.connect(self.open_filediag)
        toolbar.addAction(load_action)

        # Icon to 'convert' the file
        convert_action = QAction(QIcon(os.path.join(basedir, 'icons', 'icons8-update-left-rotation-48.png')), "&Convert", self)
        convert_action.setStatusTip("Converting the REDCap export file")
        convert_action.triggered.connect(self.file_convert)
        toolbar.addAction(convert_action)

        # It seems like Mac forces the menu bar to appear at the top, no matter what
        # So switching to a button
        #menu = self.menuBar()
        #file_menu = menu.addMenu("&File")
        #file_menu.addAction(load_action)
        #file_menu.addSeparator()

        #self.show()

    def open_filediag(self, s):
        # You will be opening a file dialogue to search for the file
        self.fileNames = QFileDialog.getOpenFileName(self, "Open File", basedir, "CSV files (*.csv)")

        ## load the file as well
        # Try if the user does not load a file at the first go
        if self.fileNames[0]:
            self.dt = pd.read_csv(self.fileNames[0])
            cols = self.dt.columns
            # Then fill in the dropdown menus with the column names of the original csv file
            self.id_dropdown.addItems(cols)
            self.fname_dropdown.addItems(cols)
            self.donned_dropdown.addItems(cols)
            self.doffed_dropdown.addItems(cols)
        else:
            return
            
    def file_convert(self):
        if hasattr(self, 'dt'):
            # Columns Of InterestS (cois)
            # Currently, the order should be [id, filename, time donned, time doffed]
            cois = [self.id_dropdown.currentText(), 
                    self.fname_dropdown.currentText(),
                    self.donned_dropdown.currentText(), 
                    self.doffed_dropdown.currentText()]
            # Get the subset
            temp = self.dt.loc[:, cois]
            # change the column names to what we want
            out = temp.rename(columns={cois[0]: 'id', 
                                       cois[1]: 'filename', 
                                       cois[2]: 'don_t',    # time donned
                                       cois[3]: 'doff_t'})  # time doffed

            # Let the person save the file at the designated location
            outname = QFileDialog.getSaveFileName(self, 'Save File', filter='*.csv')
            if (outname[0] == ''):
                pass
            else:
                # make the MainWindow to have this output
                self.parent.out = out
                out.to_csv(outname[0], index=False)

                # If things went well, throw out a message
                msg = QMessageBox(self)
                msg.setWindowTitle("Important Message")
                msg.setText("Conversion completed")
                msg.exec()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Important Message")
            msg.setText("File not loaded")
            msg.exec()

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
