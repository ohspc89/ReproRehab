''' Written by Jinseok Oh, PhD
This is a python script to build a GUI
that can help preprocessing data from wearable sensors
Current implementation is limited to the data from
APDM Opal V2 only / will add more sensors in the future
'''
import sys
import os
import pandas as pd
import h5py
from PyQt6.QtWidgets import (QMessageBox, QMainWindow, QApplication, QComboBox,
        QLabel, QWidget, QToolBar, QStatusBar, QDialog, QVBoxLayout, QGridLayout,
        QHBoxLayout, QStackedLayout, QTabWidget, QFileDialog, QPushButton, QGroupBox)

from PyQt6.QtGui import QAction, QIcon, QPixmap, QPalette, QColor
from PyQt6.QtCore import Qt, QSize
from incwear import Subject, make_start_end_datetime

basedir = os.path.dirname(__file__)
workdir = os.path.abspath(os.curdir)

H5FILE = None       # global variable

class Color(QWidget):
    '''Demo purpose (12/11/2022)'''
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class MainWindow(QMainWindow):
    ''' This is the first window that a user will see '''

    def __init__(self):
        super().__init__()

        # Title of the main window
        self.setWindowTitle("Sensor Data Analysis App")
        self.win = None       # This is to check if the new window has been opened
        self.win2 = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        logolabel = QLabel()
        applogo = QPixmap(
                os.path.join(basedir, 'icons', 'icons8-baby-64.png'))
        logolabel.setPixmap(applogo)
        # This is how you align your label center
        logolabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logolabel)

        appname = QLabel('INCWear, v0.1')
        appname.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(appname)

        button = QPushButton("Extract times sensors were worn")
        button.clicked.connect(self.show_redcap_window)
        layout.addWidget(button)     # add the button to the widget

        button2 = QPushButton("Preprocess h5 file(s)")
        button2.clicked.connect(self.show_preprocess_window)
        layout.addWidget(button2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        #self.setStatusBar(QStatusBar(self))
        self.show()

    def show_redcap_window(self, checked):
        if self.win is None:
            self.win = ConvertWindow(self)
        self.win.show()

    def show_preprocess_window(self, checked):
        if self.win2 is None:
            self.win2 = ProcessingWindow(self)
        self.win2.show()

class ProcessingWindow(QMainWindow):
    ''' This is the window that will handle
        the preprocessing of the data stored in
        a h5 file
    '''
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        if hasattr(self.parent, 'dt'):
            self.rc_filename = self.parent.rc_filename
            self.redcap = self.parent.out
        else:
            self.rc_filename = ''
            self.redcap = None
        self.h5_filename = ''

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Preprocessing window")

        layout = QGridLayout()
        ''' Notes on the design of the layout (12/11/2022)
        The main layout will have four QGroupBox widgets.
            1) REDCap file
            2) h5 file
            3) outcome screen
            4) plots
        '''

        # GroupBox1: REDCap csv file info
        rcgrpbox = QGroupBox("Formatted REDCap file")
        layout.addWidget(rcgrpbox, 0, 0, 1, 9)

        hbox = QHBoxLayout()
        rcgrpbox.setLayout(hbox)

        self.rc_loaded = QLabel(self.rc_filename)
        button = QPushButton("load")
        button.clicked.connect(self.load_redcap)

        hbox.addWidget(self.rc_loaded)
        hbox.addStretch(4)
        hbox.addWidget(button)

        # GroupBox2: h5 file info
        h5grpbox = QGroupBox("h5 file")
        layout.addWidget(h5grpbox, 1, 0, 1, 9)

        hbox2 = QHBoxLayout()
        h5grpbox.setLayout(hbox2)

        self.h5_loaded = QLabel(self.h5_filename)
        button2 = QPushButton("load")
        button2.clicked.connect(self.load_h5)

        hbox2.addWidget(self.h5_loaded)
        hbox2.addStretch(4)
        hbox2.addWidget(button2)

        # GroupBox3: outcome variables
        outputgrpbox = QGroupBox("Sample output variables")
        layout.addWidget(outputgrpbox, 2, 0, 7, 2)

        output_layout = QGridLayout()
        outputgrpbox.setLayout(output_layout)
        ''' output_layer is a GridLayout that will report some outputs.
        Variables reported are:
            1) Awake hours
            2) Bouts per hour, left
            3) Bouts per hour, right
            4) average acceleration per bout, left
            5) average acceleration per bout, right
            6) peak acceleration per bout, left
            7) peak acceleration per bout, right
        Note: 3)-7) are median vales
        '''
        awake_hours_lbl = QLabel('Awake hours: ')
        bouts_l_cnt_lbl = QLabel('Bouts per hour (L): ')
        bouts_r_cnt_lbl = QLabel('Bouts per hour (R): ')
        avgacc_l_lbl = QLabel('Avg. acc per bout (L): ')
        avgacc_r_lbl = QLabel('Avg. acc per bout (R): ')
        peakacc_l_lbl = QLabel('Peak acc per bout (L): ')
        peakacc_r_lbl = QLabel('Peak acc per bout (R): ')

        output_layout.addWidget(awake_hours_lbl, 0, 0)
        output_layout.addWidget(bouts_l_cnt_lbl, 1, 0)
        output_layout.addWidget(bouts_r_cnt_lbl, 2, 0)
        output_layout.addWidget(avgacc_l_lbl, 3, 0)
        output_layout.addWidget(avgacc_r_lbl, 4, 0)
        output_layout.addWidget(peakacc_l_lbl, 5, 0)
        output_layout.addWidget(peakacc_r_lbl, 6, 0)

        awake_hours = QLabel('')
        bouts_l_cnt = QLabel('')
        bouts_r_cnt = QLabel('')
        avgacc_l = QLabel(''.join(['', " m/s%2"]))
        avgacc_r = QLabel(''.join(['', " m/s%2"]))
        peakacc_l = QLabel(''.join(['', " m/s%2"]))
        peakacc_r = QLabel(''.join(['', " m/s%2"]))

        output_layout.addWidget(awake_hours, 0, 1)
        output_layout.addWidget(bouts_l_cnt, 1, 1)
        output_layout.addWidget(bouts_r_cnt, 2, 1)
        output_layout.addWidget(avgacc_l, 3, 1)
        output_layout.addWidget(avgacc_r, 4, 1)
        output_layout.addWidget(peakacc_l, 5, 1)
        output_layout.addWidget(peakacc_r, 6, 1)

        plotgrpbox = QGroupBox("Diagnostic plots")
        layout.addWidget(plotgrpbox, 2, 2, 7, 7)

        plot_layout = QStackedLayout()
        plotgrpbox.setLayout(plot_layout)
        ''' plot_layer will display some diagnostic
        plots from the preprocessed data.
            1) movement from left sensor
            2) movement from the right sensor
        Note: subject to change
        '''
        tabs = QTabWidget()
        tabs.setMovable(True)

        for _, color in enumerate(["red", "green", "blue"]):
            tabs.addTab(Color(color), color)

        plot_layout.addWidget(tabs)

        # Last row: run/clear buttons
        hbox_bottom = QHBoxLayout()

        run_button = QPushButton("Run")
        run_button.clicked.connect(self.run_preprocess)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_screen)

        hbox_bottom.addStretch(7)
        hbox_bottom.addWidget(run_button)
        hbox_bottom.addWidget(clear_button)

        layout.addLayout(hbox_bottom, 9, 0, 1, 9)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def load_redcap(self):
        rc_tempname = QFileDialog.getOpenFileName(self,
                                                  "Open File",
                                                  basedir,
                                                  "CSV files (*.csv)")
        if rc_tempname[0]:
            self.rc_filename = rc_tempname[0]
            self.redcap = pd.read_csv(self.rc_filename)
            self.rc_loaded.setText(rc_tempname[0])
        else:
            return

    def load_h5(self):
        h5_tempname = QFileDialog.getOpenFileName(self,
                                                  "Open File",
                                                  basedir,
                                                  "h5 files (*.h5)")
        if h5_tempname[0]:
            self.h5_filename = h5_tempname[0]
            self.f = h5py.File(h5_tempname[0])
            self.h5_loaded.setText(h5_tempname[0])

    def run_preprocess(self):
        pass

    def clear_screen(self):
        pass


class ConvertWindow(QMainWindow):
    ''' This is the window that will handle
        the conversion of a REDCap data export to
        whatever csv file we want for further preprocessing
    '''
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()
        self.parent = parent

    def initUI(self):
        self.setWindowTitle("Extract times from Redcap")

        layout = QGridLayout()
        #self.setLayout(layout)

        layout.addWidget(QLabel(
            'Select corresponding columns\nfrom your csv file for each item.'),
                         1, 0)

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
        load_action = QAction(QIcon(
            os.path.join(basedir, 'icons', 'icons8-opened-folder-48.png')),
                              "&Load", self)
        load_action.setStatusTip("Loading the REDCap export file")
        load_action.triggered.connect(self.open_filediag)
        toolbar.addAction(load_action)

        # Icon to 'convert' the file
        convert_action = QAction(QIcon(
            os.path.join(basedir, 'icons', 'icons8-update-left-rotation-48.png')),
                                 "&Convert", self)
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
        self.fileNames = QFileDialog.getOpenFileName(self,
                                                     "Open File",
                                                     basedir,
                                                     "CSV files (*.csv)")

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
            if outname[0] == '':
                pass
            else:
                # make the MainWindow to 'contain' this output
                self.parent.out = out
                self.parent.rc_filename = outname[0]
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
    win = MainWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
