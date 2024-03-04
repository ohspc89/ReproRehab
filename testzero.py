# Referenced
# stackoverflow.com/questions/39303008/load-an-opencv-video-frame-by-frame-using-pyqt
# stackoverflow.com/questions/46656634/pyqt5-qtimer-count-until-specific-seconds
import sys
import pytz
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                             QPushButton, QSizePolicy, QFileDialog, QLabel,
                             QGridLayout, QMenuBar, QApplication, QMessageBox,
                             QGroupBox, QLineEdit, QComboBox)
from PyQt6.QtGui import QAction, QPixmap, QImage, QPalette, QColor
from PyQt6.QtCore import Qt, QTimer
import cv2
#import apdm

class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


class VideoCapture(QWidget):
    """ use cv2 to 'capture' a video file

    Parameters
    ----------
        filename: str
            full path to the video file to be opened

        parent: obj
            VideoDisplayWidget(QWidget)

        startframe: int
            frame to start the video, default to 0

    Returns
    -------
        None (video frame visible in the QMainWindow)
    """
    def __init__(self, filename, parent, startframe=0):
        super().__init__()
        self.cap = cv2.VideoCapture(str(filename))
        # Frame per second
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        # Total number of frames
        self.numFrames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Frame number to be loaded
        self.frameNumber = startframe 
        print(f"Initial Frame: {self.frameNumber}")
        # Use QLabel to embed QImage
        self.video_frame = QLabel()
        # Still a blackbox to me, but it works
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.video_frame.setSizePolicy(sizePolicy)
        self.video_frame.setScaledContents(True)
        # You may have 'resetted' and starting anew
        if not parent.findChild(QLabel):
            parent.customLayout.addWidget(self.video_frame)
        # counter set to 0
        self.counter = 0
        # Update at the beginning?
        self.nextFrameSlot(count = 0)

    def nextFrameSlot(self, count):
        """ Updating video_frame

        Parameters
        ----------
            count : int
                number of frames moved

        Returns
        -------
            None (self.video_frame updated)
        """
        print(f"nextFrameSlot begins at: {self.frameNumber} frame")
        # If moving certain frames (-1, -5, or -10) will take you to a
        # 'negative' frame, stop at frame = 0.
        if self.frameNumber + count < 0:
            self.frameNumber = 0
            print("Frame Number reached the beginning of its range.")
        # If moving certain frames (1, 5, 10) takes you to the frame number
        # beyond the maximum number of frames, stop at frame: self.numFrames-1
        elif self.frameNumber + count > (self.numFrames-1):
            self.frameNumber = self.numFrames-1
            print("Frame Number reached the end of its range.")
        else:
            self.frameNumber += count
        print(f"count is {count}. Now you will see frame: {self.frameNumber}")

        # Set to a specific frameNumber
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frameNumber)
        _, frame = self.cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QImage(frame, frame.shape[1], frame.shape[0],
                     QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img)
        """
        try:
            pix = pix.scaled(600, 400, Qt.AspectRatioMode(1))
        except:
            print('uh-oh')
        """
        # updating QLabel with the specific pixel map
        self.video_frame.setPixmap(pix)

    def moveByFrames(self, slot, addFrame=1):
        """ Move by designated number of frames, backward or forward

        Parameters
        ----------
            slot: function

            addFrame: int
                Number of frames to move. Positive or negative.

        Returns
        -------
            None (slot runs [count] number of times)
        """
        counter = 0
        def handler():
            # nonlocal == global?
            nonlocal counter
            counter += 1
            print(f"handler runs/frame_num: {self.frameNumber}")
            slot(addFrame)
            if counter >= 1:
                self.timer.stop()
                self.timer.deleteLater()  # What's this?
                # Counter updated to 1?
                self.counter = counter
                print(f"Timer stopped / counter: {self.counter}")
        self.timer = QTimer()
        self.timer.timeout.connect(handler)
        self.timer.start(int(1000/self.fps)) # Interval does not matter much

    def deleteLater(self):
        self.cap.release()
        super().deleteLater()

class VideoDisplayWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # Make a custom Layout
        self.customLayout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self.customLayout.addLayout(button_layout)
        # b(ackward) [0-9]
        self.b1Button = QPushButton('-1 Frame', parent)
        self.b1Button.clicked.connect(lambda: parent.frameJump(addFrame=-1))
        self.b5Button = QPushButton('-5 Frame', parent)
        self.b5Button.clicked.connect(lambda: parent.frameJump(addFrame=-5))
        self.b10Button = QPushButton('-10 Frame', parent)
        self.b10Button.clicked.connect(lambda: parent.frameJump(addFrame=-10))
        # f(oreward) [0-9]
        self.f1Button = QPushButton('+1 Frame', parent)
        self.f1Button.clicked.connect(lambda: parent.frameJump(addFrame=1))
        self.f5Button = QPushButton('+5 Frame', parent)
        self.f5Button.clicked.connect(lambda: parent.frameJump(addFrame=5))
        self.f10Button = QPushButton('+10 Frame', parent)
        self.f10Button.clicked.connect(lambda: parent.frameJump(addFrame=10))
        button_layout.addWidget(self.b10Button)
        button_layout.addWidget(self.b5Button)
        button_layout.addWidget(self.b1Button)
        button_layout.addWidget(self.f1Button)
        button_layout.addWidget(self.f5Button)
        button_layout.addWidget(self.f10Button)

        # Use the custom Layout
        self.setLayout(self.customLayout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(50, 50, 800, 600)
        self.setWindowTitle("matching video and sensor data")

        self.capture = None # Why None though?
        self.isVideoFileLoaded = False
        self.h5FileName = None
        self.videoFileName = None

        self.openVideoFile = QAction("&Open Video File")
        self.openVideoFile.setShortcut("Ctrl+Shift+V")
        self.openVideoFile.setStatusTip("Open a .h264 file")
        self.openVideoFile.triggered.connect(self.loadVideoFile)

        self.openH5File = QAction("&Open h5 File")
        self.openH5File.setShortcut("Ctrl+Shift+H")
        self.openH5File.setStatusTip("Open a .h5 file")
        self.openH5File.triggered.connect(self.loadH5File)

        self.quitAction = QAction("&Exit")
        self.quitAction.setShortcut("Ctrl+Q")
        self.quitAction.setStatusTip("Close the app")
        self.quitAction.triggered.connect(self.closeApplication)

        # Menubar
        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu("&File")
        self.fileMenu.addAction(self.openVideoFile)
        self.fileMenu.addAction(self.openH5File)
        self.fileMenu.addAction(self.quitAction)

        # A box to show if all files are provided (infogrpbox)
        #   - h5 file
        #   - study timezone
        #   - label to identify Right side
        #   - video file
        #   - approx. time when the clock appears in the video
        infogrpbox = QGroupBox("Required Info.")
        # Layout of infogrpbox
        infovbox = QVBoxLayout()
        infogrpbox.setLayout(infovbox)

        h5box = QVBoxLayout()
        h5box.addWidget(QLabel(".h5 file loaded:"))
        self.h5FileNameLabel = QLabel("")
        self.h5FileNameLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h5box.addWidget(self.h5FileNameLabel)

        tzbox = QVBoxLayout()
        tzbox.addWidget(QLabel("Study Timezone:"))
        self.timezone = QComboBox()
        self.timezone.addItems(pytz.all_timezones)
        tzbox.addWidget(self.timezone)

        vidbox = QVBoxLayout()
        vidbox.addWidget(QLabel("Video file loaded:"))
        self.videoFileNameLabel = QLabel("")
        self.videoFileNameLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vidbox.addWidget(self.videoFileNameLabel)
        # Need to specify when does the clock appear in the video
        # This can also be used to move to any point in the video
        vidstartbox = QVBoxLayout()
        vidstartbox.addWidget(QLabel("Time in video a clock appears (MM:SS):"))
        self.videoCapturePoint = QLineEdit(self)
        self.videoCapturePoint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vidstartbox.addWidget(self.videoCapturePoint)
        # Time when the sensor button was pressed...
        # Anything on
        recstartbox = QVBoxLayout()
        recstartbox.addWidget(QLabel("Time recording started (HH:MM:SS):"))
        self.sensorCapturePoint = QLineEdit(self)
        self.sensorCapturePoint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        recstartbox.addWidget(self.sensorCapturePoint)

        buttonhbox = QHBoxLayout()
        lock_button = QPushButton("Initialize")
        lock_button.clicked.connect(self.lockTime)
        mod_button = QPushButton("Modify")
        mod_button.clicked.connect(lambda: self.lockTime(reverse=True))
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.resetReq)
        buttonhbox.addWidget(lock_button)
        buttonhbox.addWidget(mod_button)
        buttonhbox.addWidget(reset_button)

        infovbox.addLayout(h5box)
        infovbox.addLayout(tzbox)
        infovbox.addLayout(vidbox)
        infovbox.addLayout(vidstartbox)
        infovbox.addLayout(recstartbox)
        infovbox.addLayout(buttonhbox)

        # File info
        fmgrpbox = QGroupBox("File Monitor")
        # Layout of fmgrpbox
        fminfovbox = QVBoxLayout()
        fmgrpbox.setLayout(fminfovbox)

        # Frame rate
        fratebox = QVBoxLayout()
        fratebox.addWidget(QLabel("Video frame rate:"))
        self.fps = QLabel("")
        self.fps.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fratebox.addWidget(self.fps)

        # Frame number
        frnumbox = QVBoxLayout()
        frnumbox.addWidget(QLabel("Current Frame Number:"))
        self.curfnum = QLabel("")
        self.curfnum.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frnumbox.addWidget(self.curfnum)

        # Estimated video time
        estvidtimebox = QVBoxLayout()
        estvidtimebox.addWidget(QLabel("Current Video Time Estimate:"))
        self.estvidtime = QLabel("")
        self.estvidtime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        estvidtimebox.addWidget(self.estvidtime)

        fminfovbox.addLayout(fratebox)
        fminfovbox.addLayout(frnumbox)
        fminfovbox.addLayout(estvidtimebox)

        self.videoDisplayWidget = VideoDisplayWidget(self)

        # Configuring the central widget
        centralView = QGridLayout()
        centralView.addWidget(infogrpbox, 0, 0, 3, 2)
        centralView.addWidget(fmgrpbox, 3, 0, 2, 2)
        centralView.addWidget(self.videoDisplayWidget, 2, 2, 4, 3)

        centralWidget = QWidget()
        centralWidget.setLayout(centralView)

        self.setCentralWidget(centralWidget)

    def frameJump(self, addFrame=1):
        if self.capture is not None:
            # Why is it not working....
            self.capture.moveByFrames(slot=self.capture.nextFrameSlot, addFrame=addFrame)
            # I could not find a decent way, so...
            self.updateFrameInfo(cond=False, addFrame=addFrame)

    def lockTime(self, reverse=False):
        """
        function to adjust the video frame and graph window to display

        Parameters
        ----------
            onset_v: str
                Difference in time between 0 and the point 
                when a clock appeared in video (format: "MM:SS")

            record_onset: str
                Time displayed in the clock appearing in video
                This should the time you see from the video

            reverse: bool
                If True, make QLineEdit modifiable

        Returns
        -------
            None
            - set the video frame according to onset_v and 
                graph window to record_onset)
            - Make [Required info.] (NOT) modifiable
        """
        if self.capture is not None:
            if not reverse:
                try:
                    # Make text inputs not modifiable
                    self.videoCapturePoint.setEnabled(False)
                    self.sensorCapturePoint.setEnabled(False)
                    min_diff, sec_diff = map(int, self.videoCapturePoint.text().split(sep=':'))
                    frame_diff = (min_diff*60 + sec_diff) * self.capture.fps-1
                    # frame_diff is from frame 0, so first make frameNumber = 0
                    self.capture.frameNumber = 0
                    self.capture.nextFrameSlot(frame_diff)
                    self.updateFrameInfo()
                except:
                    print("Something's not right.\
                            Please check the time difference you entered")
            else:
                self.videoCapturePoint.setEnabled(True)
                self.sensorCapturePoint.setEnabled(True)
        else:
            print("Video not loaded. Nothing will happen")

    def resetReq(self):
        """ Reset provided input """
        self.videoCapturePoint.setEnabled(True)
        self.videoCapturePoint.clear()
        self.sensorCapturePoint.setEnabled(True)
        self.sensorCapturePoint.clear()
        self.videoFileName = ""
        self.h5FileName = ""
        self.videoFileNameLabel.setText("")
        self.h5FileNameLabel.setText("")
        self.fps.setText("")
        self.curfnum.setText("")
        self.estvidtime.setText("")
        try:
            # canvas = QPixmap(600, 400)
            # canvas.fill(QColor("white"))
            self.videoDisplayWidget.customLayout.removeWidget(self.capture.video_frame)
            # self.capture.video_frame.setPixmap(canvas)
            self.capture = None
        except:
            print("Hmm")


    def loadVideoFile(self):
        try:
            self.videoFileName = QFileDialog.getOpenFileName(self, "Select a .h264 video file")[0]
            shortform = self.videoFileName.split(sep="/")[-1]
            self.videoFileNameLabel.setText(shortform)
            self.isVideoFileLoaded = True
            self.capture = VideoCapture(self.videoFileName, self.videoDisplayWidget)
            self.updateFrameInfo()
        except:
            print("Please select a .h264 file")

    def loadH5File(self):
        try:
            self.h5FileName = QFileDialog.getOpenFileName(self, "Select a .h5 file")[0]
            shortform = self.h5FileName.split(sep="/")[-1]
            self.h5FileNameLabel.setText(shortform)
            self.isH5FileLoaded = True
        except:
            print("Please select a .h5 file")

    def updateFrameInfo(self, cond=True, addFrame=1):
        """
        Parameters
        ----------
            init: bool 
                True: initialized, False: button pressed
        """
        self.fps.setText(str(format(self.capture.fps, '2.2f')))
        # A viewer sees from frame 1, not 0
        if cond:
            fn_updated = self.capture.frameNumber
        else:
            fn_updated = self.capture.frameNumber + addFrame

        fn_updated = max(fn_updated, 0)
        fn_updated = min(fn_updated, self.capture.numFrames-1)
        # Frame Number set!
        self.curfnum.setText(str(fn_updated+1))
        # Frame Number based video time estimate
        estmsec = (fn_updated / self.capture.fps)*1000
        estsecmin = estmsec // 1000
        estmin = estsecmin // 60
        estsec = estsecmin % 60
        try:
            estvidtimetxt = str(format(estmin, '02.0f')) + " MIN " +\
                    str(format(estsec, '02.0f')) + " SEC  " +\
                    str((estmsec % 1000)) + " MSEC"
            print(estvidtimetxt)
            self.estvidtime.setText(estvidtimetxt)
        except:
            print("test concat error")

    def closeApplication(self):
        choice = QMessageBox.question(self, "Message", "Are you sure you close this app?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if choice == QMessageBox.StandardButton.Yes:
            print("Bye bye")
            sys.exit()
        else:
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
