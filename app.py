""" Written by Jinseok Oh, PhD
This is a python script to build a GUI
that can help preprocessing data from wearable sensors
Current implementation is limited to the data from
APDM Opal V2 only / will add more sensors in the future
"""
import sys
import os
import numpy as np
import pandas as pd
import pytz
from PyQt6.QtWidgets import (QMessageBox, QMainWindow, QApplication,
                             QComboBox, QLabel, QWidget, QToolBar,
                             QStatusBar, QDialog, QVBoxLayout, QGridLayout,
                             QHBoxLayout, QStackedLayout, QTabWidget,
                             QFileDialog, QPushButton, QGroupBox, QLineEdit)
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPalette, QColor
from PyQt6.QtCore import Qt, QSize
import apdm
import axivity

basedir = os.path.dirname(__file__)
workdir = os.path.abspath(os.curdir)

SUBJECT = None

class Color(QWidget):
    """ This should be replaced with the actual figures """
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class MainWindow(QMainWindow):
    """ This is the first window that a user will see """

    def __init__(self):
        super().__init__()

        # Title of the main window
        self.setWindowTitle("INCwear")
        self.win = None       # Check if the new window has been opened
        #self.win2 = None
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
        appname.setStyleSheet("font: bold 20px")
        copyrightlabel = QLabel('Infant Neuromotor Control Laboratory,'\
                + ' All Rights Reserved.')
        contactlabel = QLabel('Questions or issues with the app:\n'\
                +'Jinseok Oh, PhD: joh@chla.usc.edu')
        appname.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(appname)
        layout.addWidget(copyrightlabel)
        layout.addWidget(contactlabel)

        # A drop-down menu to choose which preprocessing window to open
        stype_label = QLabel('Choose your sensor')
        layout.addWidget(stype_label)
        self.sensortype = QComboBox()
        self.sensortype.addItems(['APDM Opal V2', 'Axivity Ax6'])
        self.sensortype.setCurrentIndex(-1)    # This makes the default choice blank
        self.sensortype.currentTextChanged.connect(self.show_preprocess_window)
        layout.addWidget(self.sensortype)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        #self.setStatusBar(QStatusBar(self))
        self.show()

    def show_redcap_window(self, checked):
        if self.win is None:
            self.win = ConvertWindow(self)
        self.win.show()

    def show_preprocess_window(self, checked, text=None):
        if self.win is None:
            if text is None:
                text = self.sensortype.currentText()
            if 'Opal' in text:
                self.win = APDMWindow(self)
            elif 'Ax6' in text:
                self.win = AxivityWindow(self)
        self.win.show()
        self.sensortype.blockSignals(True)
        self.sensortype.setCurrentIndex(-1)
        self.sensortype.blockSignals(False)
        self.win = None

class ProcessingWindow(QMainWindow):
    """ Template class that will be inherited by either
    APDMWindow or AxivityWindow """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.timezone = QComboBox()
        self.sensortype = ''    # will be inherited
        self.setWindowTitle('Preprocessing window')
        layout = QGridLayout()

        # GroupBox3: Study detail
        infogrpbox = QGroupBox("Study Info")
        layout.addWidget(infogrpbox, 3,0,1,9)

        infohbox = QHBoxLayout()
        infogrpbox.setLayout(infohbox)
        infolbl = QLabel("Timezone of the study site: ")
        self.timezone.addItems(pytz.all_timezones)
        infohbox.addWidget(infolbl)
        infohbox.addWidget(self.timezone)

        # GroupBox4: outcome variables
        outputgrpbox = QGroupBox("Sample output variables")
        layout.addWidget(outputgrpbox, 4,0,7,2)

        output_layout = QGridLayout()
        outputgrpbox.setLayout(output_layout)

        # output_layout is a GridLayout that will report some outputs.
        # Variables reported are:
        #   0) Record time
        #   1) Awake time
        #   2) Sleep time
        #   3) Movements per hour, left
        #   4) Movements per hour, right
        #   5) average acceleration per mov, left
        #   6) average acceleration per mov, right
        #   7) peak acceleration per mov, left
        #   8) peak acceleration per mov, right
        # Note. 5-8 are median values

        record_hours_lbl = QLabel("Record times (hour): ")
        awake_hours_lbl = QLabel("Awake times (hour): ")
        sleep_hours_lbl = QLabel("Sleep times (hour): ")
        bouts_l_cnt_lbl = QLabel("Movements per hour (L): ")
        bouts_r_cnt_lbl = QLabel("Movements per hour (R): ")
        avgacc_l_lbl = QLabel("Avg. acc per mov (L): ")
        avgacc_r_lbl = QLabel("Avg. acc per mov (R): ")
        peakacc_l_lbl = QLabel("Peak acc per mov (L): ")
        peakacc_r_lbl = QLabel("Peak acc per mov (R): ")

        output_layout.addWidget(record_hours_lbl, 0, 0)
        output_layout.addWidget(awake_hours_lbl, 1, 0)
        output_layout.addWidget(sleep_hours_lbl, 2, 0)
        output_layout.addWidget(bouts_l_cnt_lbl, 3, 0)
        output_layout.addWidget(bouts_r_cnt_lbl, 4, 0)
        output_layout.addWidget(avgacc_l_lbl, 5, 0)
        output_layout.addWidget(avgacc_r_lbl, 6, 0)
        output_layout.addWidget(peakacc_l_lbl, 7, 0)
        output_layout.addWidget(peakacc_r_lbl, 8, 0)

        self.record_hours = QLabel("")
        self.awake_hours = QLabel("")
        self.sleep_hours = QLabel("")
        self.bouts_l_cnt = QLabel("")
        self.bouts_r_cnt = QLabel("")
        self.avgacc_l = QLabel("".join(["", " m/s^2"]))
        self.avgacc_r = QLabel("".join(["", " m/s^2"]))
        self.peakacc_l = QLabel("".join(["", " m/s^2"]))
        self.peakacc_r = QLabel("".join(["", " m/s^2"]))

        output_layout.addWidget(self.record_hours, 0, 1)
        output_layout.addWidget(self.awake_hours, 1, 1)
        output_layout.addWidget(self.sleep_hours, 2, 1)
        output_layout.addWidget(self.bouts_l_cnt, 3, 1)
        output_layout.addWidget(self.bouts_r_cnt, 4, 1)
        output_layout.addWidget(self.avgacc_l, 5, 1)
        output_layout.addWidget(self.avgacc_r, 6, 1)
        output_layout.addWidget(self.peakacc_l, 7, 1)
        output_layout.addWidget(self.peakacc_r, 8, 1)

        # GroupBox5: Diagnostic plots
        plotgrpbox = QGroupBox("Diagnostic plots")
        layout.addWidget(plotgrpbox, 4, 2, 7, 7)

        plot_layout = QStackedLayout()
        plotgrpbox.setLayout(plot_layout)

        # plot_layout will display some diagnostic plots
        # from the preprocessed data.
        #   1) movements from left sensor
        #   2) movements from the right sensor
        # Note. subject to change

        tabs = QTabWidget()
        tabs.setMovable(True)

        for _, color in enumerate(["red", "green", "blue"]):
            tabs.addTab(Color(color), color)

        plot_layout.addWidget(tabs)

        # This will be used in child classes
        self.sharedlayout = layout

    def sensor_specific_housekeeping(self):
        """ This will be modified in the inherited class """

    def run_preprocess(self):
        """ This will calculate kinematic variables """
        # Let's have a sensor-specific function here
        SUBJECT = self.sensor_specific_housekeeping()

        lmovs = SUBJECT.get_mov()
        rmovs = SUBJECT.get_mov('R')
        lmovs_del, rmovs_del = map(apdm.cycle_filt, [lmovs, rmovs])

        # average acceleration per mov / peak acc per mov
        laccpmov = SUBJECT.acc_per_mov(movmat=lmovs_del)
        raccpmov = SUBJECT.acc_per_mov(side='R', movmat=rmovs_del)

        # hours (sleep, awake) calculation
        record_len = list(SUBJECT.info.recordlen.values())
        lsleep, rsleep = map(apdm.time_asleep,\
                [lmovs_del, rmovs_del], record_len)

        # Rounding up sleep times to nearest 5 minutes
        lsleep_5m, rsleep_5m = map(
                lambda x: x/1200 - np.mod(x/1200, 5), [lsleep, rsleep])

        lrec_hr = record_len[0]/72000   # 72000 = 20(Hz)*3600(seconds)
        rrec_hr = record_len[1]/72000

        lsleep_hr, rsleep_hr = map(
                lambda x: x/60, [lsleep_5m, rsleep_5m])

        awake_hrs = [lrec_hr - lsleep_hr, rrec_hr - rsleep_hr]

        lmovrate = lmovs_del.shape[0] / awake_hrs[0]
        rmovrate = rmovs_del.shape[0] / awake_hrs[1]

        record_hours_newtxt = str(np.mean([lrec_hr, rrec_hr]))
        sleep_hours_newtxt = str(np.mean([lsleep_hr, rsleep_hr]))
        awake_hours_newtxt = str(np.mean(awake_hrs))
        bouts_l_cnt_newtxt = str(lmovrate)
        bouts_r_cnt_newtxt = str(rmovrate)
        # median does not have the 'dtype' argument
        avgacc_l_newtxt = str(
                np.round(np.median(laccpmov[:,1]),2))
        avgacc_r_newtxt = str(
                np.round(np.median(raccpmov[:,1]),2))
        peakacc_l_newtxt = str(
                np.round(np.median(laccpmov[:,2]),2))
        peakacc_r_newtxt = str(
                np.round(np.median(raccpmov[:,2]),2))

        # set new texts
        self.record_hours.setText(record_hours_newtxt)
        self.awake_hours.setText(awake_hours_newtxt)
        self.sleep_hours.setText(sleep_hours_newtxt)
        self.bouts_l_cnt.setText(bouts_l_cnt_newtxt)
        self.bouts_r_cnt.setText(bouts_r_cnt_newtxt)
        self.avgacc_l.setText("".join([avgacc_l_newtxt, ' m/s^2']))
        self.avgacc_r.setText("".join([avgacc_r_newtxt, ' m/s^2']))
        self.peakacc_l.setText("".join([peakacc_l_newtxt, ' m/s^2']))
        self.peakacc_r.setText("".join([peakacc_r_newtxt, ' m/s^2']))

class AxivityWindow(ProcessingWindow):
    """ This is the window that will handle
    the processing of the data stored in two .cwa files """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.cwa_l_filename = ""
        self.cwa_r_filename = ""

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Preprocessing Axivity Ax6 data")

        layout = self.sharedlayout
        # Notes on the design of the layout (3/24/2023)
        # The main layout will have five QGroupBox QtWidgets
        #   0) cwa file - left
        #   1) cwa file - right
        #   2) Study detail
        #   3) outcome screen
        #   4) plots

        # GroupBox2: cwa file - left info
        lcwagrpbox = QGroupBox("cwa file: LEFT")
        layout.addWidget(lcwagrpbox, 0,0,1,9)

        lcwahbox = QHBoxLayout()
        lcwagrpbox.setLayout(lcwahbox)

        self.lcwa_loaded = QLabel(self.cwa_l_filename)
        button1 = QPushButton("load")
        button1.clicked.connect(self.load_cwa)

        lcwahbox.addWidget(self.lcwa_loaded)
        lcwahbox.addStretch(4)
        lcwahbox.addWidget(button1)

        # GroupBox2: cwa file - right info
        rcwagrpbox = QGroupBox("cwa file: RIGHT")
        layout.addWidget(rcwagrpbox, 1,0,1,9)

        rcwahbox = QHBoxLayout()
        rcwagrpbox.setLayout(rcwahbox)

        self.rcwa_loaded = QLabel(self.cwa_r_filename)
        button2 = QPushButton("load")
        button2.clicked.connect(self.load_cwa)

        rcwahbox.addWidget(self.rcwa_loaded)
        rcwahbox.addStretch(4)
        rcwahbox.addWidget(button2)

        # Last row: run/clear buttons
        hbox_bottom = QHBoxLayout()

        # This should be 'deactivated' when there's no file loaded
        run_button = QPushButton("Run")
        run_button.clicked.connect(self.run_preprocess)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_screen)

        hbox_bottom.addStretch(7)
        hbox_bottom.addWidget(run_button)
        hbox_bottom.addWidget(clear_button)

        layout.addLayout(hbox_bottom, 11,0,1,9)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def load_cwa(self, side='L'):
        """ open up a file dialog window, select cwa files """
        cwa_tempname = QFileDialog.getOpenFileName(self,
                "Open File",
                basedir,
                "cwa files (*.cwa)")
        if cwa_tempname[0]:
            if side == "L":
                self.cwa_l_filename = cwa_tempname[0]
                self.lcwa_loaded.setText(cwa_tempname[0])
            else:
                self.cwa_r_filename = cwa_tempname[0]
                self.rcwa_loaded.setText(cwa_tempname[0])

    def sensor_specific_housekeeping(self):
        SUBJECT = axivity.Ax6(self.cwa_l_filename, 
                self.cwa_r_filename)
        return SUBJECT

    def clear_screen(self):
        """ clear_screen is a function that clears
        all the input so far passed to this window
            0) self.cwa_l_filename
            1) self.cwa_r_filename
            2) self.lcwa_loaded
            3) self.rcwa_loaded
        """
        self.cwa_l_filename = ""
        self.cwa_r_filename = ""
        self.lcwa_loaded.setText("")
        self.rcwa_loaded.setText("")
        # clear outcome variables
        self.record_hours.setText("")
        self.awake_hours.setText("")
        self.sleep_hours.setText("")
        self.bouts_l_cnt.setText("")
        self.bouts_r_cnt.setText("")
        self.avgacc_l.setText(" m/s^2")
        self.avgacc_r.setText(" m/s^2")
        self.peakacc_l.setText(" m/s^2")
        self.peakacc_r.setText(" m/s^2")

class APDMWindow(ProcessingWindow):
    """ This is the window that will handle
    the processing of the data stored in a h5 file using
    metadata from REDCap """

    def __init__(self, parent):
        super().__init__(parent)
        self.win = None
        self.parent = parent
        self.rc_filename = ""
        self.redcap = None
        self.h5_filename = ""

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Processing APDM Opal V2 data")

        layout = self.sharedlayout
        # Notes on the design of the layout (3/23/2023)
        # The main layout will have six QGroupBox widgets.
        #   0) REDCap reformation (optional)
        #   1) REDCap file - metadata (.csv)
        #   2) h5 file - raw data
        #   3) study detail
        #   4) outcome screen
        #   5) plots

        # GroupBox0 (Optional): REDCap export reformatting
        rcreformbox = QGroupBox("Reformat REDCap export (Optional)")
        layout.addWidget(rcreformbox, 0,0,1,9)

        reformhbox = QHBoxLayout()
        rcreformbox.setLayout(reformhbox)
        reform_button = QPushButton("Begin reformatting")
        reform_button.clicked.connect(self.show_redcap_window)

        reformhbox.addStretch(4)
        reformhbox.addWidget(reform_button)

        # GroupBox1: REDCap csv file info
        rcgrpbox = QGroupBox("Formatted REDCap file")
        layout.addWidget(rcgrpbox, 1,0,1,9)

        rchbox = QHBoxLayout()
        rcgrpbox.setLayout(rchbox)

        self.rc_loaded = QLabel(self.rc_filename)
        button = QPushButton("load")
        button.clicked.connect(self.load_redcap)

        rchbox.addWidget(self.rc_loaded)
        rchbox.addStretch(4)
        rchbox.addWidget(button)

        # GroupBox2: h5 file info
        h5grpbox = QGroupBox("h5 file")
        layout.addWidget(h5grpbox, 2,0,1,9)

        h5hbox = QHBoxLayout()
        h5grpbox.setLayout(h5hbox)

        self.h5_loaded = QLabel(self.h5_filename)
        button2 = QPushButton("load")
        button2.clicked.connect(self.load_h5)

        h5hbox.addWidget(self.h5_loaded)
        h5hbox.addStretch(4)
        h5hbox.addWidget(button2)

        # GreoupBox3: Study detail
        infogrpbox = QGroupBox("Study Info")
        layout.addWidget(infogrpbox, 3,0,1,9)

        infohbox = QHBoxLayout()
        infogrpbox.setLayout(infohbox)
        infolbl = QLabel("Timezone of the study site: ")
        self.timezone.addItems(pytz.all_timezones)

        # user input for the label used to identify the 'Right' side
        self.label_r = QLineEdit(self)
        label_r_lbl = QLabel("Label used for the right side identification: ")

        infohbox.addWidget(infolbl)
        infohbox.addWidget(self.timezone)
        infohbox.addWidget(label_r_lbl)
        infohbox.addWidget(self.label_r)

        # Last row: run/clear buttons
        hbox_bottom = QHBoxLayout()

        # This should be 'deactivated' when there's no file loaded
        run_button = QPushButton("Run")
        run_button.clicked.connect(self.run_preprocess)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_screen)

        hbox_bottom.addStretch(7)
        hbox_bottom.addWidget(run_button)
        hbox_bottom.addWidget(clear_button)

        layout.addLayout(hbox_bottom, 11,0,1,9)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def show_redcap_window(self, checked):
        """ This will load the ConvertWindow
        which will help a user with reformatting the REDCap export
        """
        if self.win is None:
            self.win = ConvertWindow(self)
            self.win.show()
            self.win = None     # reset

    def load_redcap(self):
        """ This will open up a file dialogue
        so that a user can select the re-formatted REDCap export file
        """
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
        """ similar to load_redcap, select h5 file """
        h5_tempname = QFileDialog.getOpenFileName(self,
                "Open File",
                basedir,
                "h5 files (*.h5)")
        if h5_tempname[0]:
            self.h5_filename = h5_tempname[0]
            self.h5_loaded.setText(h5_tempname[0])

    def sensor_specific_housekeeping(self):
        in_en_dt = apdm.make_start_end_datetime(self.redcap,
                self.h5_filename,
                self.timezone.currentText())
        SUBJECT = apdm.OpalV2(self.h5_filename,
                in_en_dt,
                self.label_r.text())
        return SUBJECT

    def clear_screen(self):
        """ clear_screen is a function that clears
        all the input so far passed to this window 
            0) self.redcap
            1) self.rc_filename
            2) self.rc_loaded
            3) self.h5_filename
            4) self.h5_loaded
            5) self.label_r
        """
        self.recap = None
        self.rc_filename = ""
        self.h5_filename = ""
        self.rc_loaded.setText("")
        self.h5_loaded.setText("")
        self.label_r.clear()
        # clear outcome variables
        self.record_hours.setText("")
        self.awake_hours.setText("")
        self.sleep_hours.setText("")
        self.bouts_l_cnt.setText("")
        self.bouts_r_cnt.setText("")
        self.avgacc_l.setText(" m/s^2")
        self.avgacc_r.setText(" m/s^2")
        self.peakacc_l.setText(" m/s^2")
        self.peakacc_r.setText(" m/s^2")

class ConvertWindow(QMainWindow):
    """ This is the window that will handle
        the conversion of a REDCap data export to
        whatever csv file we want for further preprocessing
    """
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
        widget.setLayout(layout)   # a widget to place a layout
        self.setCentralWidget(widget)   # in a window you centre the widget

        # setting a status bar
        self.setStatusBar(QStatusBar(self))

        # setting a toolbar - see that this is located 
        #   at the top (0,0) of the grid layout
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

        # It seems like Mac forces the menu bar to appear always at the top
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
            # Then fill in the dropdown menus with 
            #   the column names of the original csv file
            self.id_dropdown.addItems(cols)
            self.fname_dropdown.addItems(cols)
            self.donned_dropdown.addItems(cols)
            self.doffed_dropdown.addItems(cols)
        else:
            return

    def file_convert(self):
        if hasattr(self, 'dt'):
            # Columns Of InterestS (cois)
            # Currently, the order should be:
            #   [id, filename, time donned, time doffed]
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
