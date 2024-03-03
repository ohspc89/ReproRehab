# Referenced
# stackoverflow.com/questions/39303008/load-an-opencv-video-frame-by-frame-using-pyqt
# stackoverflow.com/questions/46656634/pyqt5-qtimer-count-until-specific-seconds
import sys
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                             QPushButton, QSizePolicy, QFileDialog, QLabel,
                             QGridLayout, QMenuBar, QApplication, QMessageBox,
                             QGroupBox, QLineEdit)
from PyQt6.QtGui import QAction, QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
import cv2
import apdm

class VideoCapture(QWidget):
    """ use cv2 to 'capture' a video file
        'parent' is VideoDisplayWidget(QWidget)
    """
    def __init__(self, filename, parent):
        super().__init__()
        self.cap = cv2.VideoCapture(str(filename))
        # Frame per second
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        # Total number of frames
        self.numFrames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Frame number to be loaded
        self.frameNumber = 0
        print(f"Initial Frame: {self.frameNumber}")
        # Use QLabel to embed QImage
        self.video_frame = QLabel()
        # Still a blackbox to me, but it works
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.video_frame.setSizePolicy(sizePolicy)
        self.video_frame.setScaledContents(True)
        parent.customLayout.addWidget(self.video_frame)
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
        print(f"nextFrameSlot begins/frame_num: {self.frameNumber}")
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
        # count will be positive or negative
        # If frameNumber is 0 and you want to go back couple frame(s),
        # don't do that.
        if all((count < 0, self.frameNumber == 0)):
            pass
        # If frameNumber is maxed out and you wnat to go forward,
        # stop.
        elif all((count > 0, self.frameNumber == self.numFrames )):
            pass
        else:
            self.frameNumber += count

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
            print(f"counter: {counter}")
            print(f"handler runs/frame_num: {self.frameNumber}")
            slot(addFrame)
            if counter >= 1:
                self.timer.stop()
                self.timer.deleteLater() # What's this?
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
        self.backOneButton = QPushButton('-1 Frame', parent)
        self.backOneButton.clicked.connect(parent.backOne)
        self.backFiveButton = QPushButton('-5 Frame', parent)
        self.backFiveButton.clicked.connect(parent.backFive)
        self.backTenButton = QPushButton('-10 Frame', parent)
        self.backTenButton.clicked.connect(parent.backTen)
        self.foreOneButton = QPushButton('+1 Frame', parent)
        self.foreOneButton.clicked.connect(parent.foreOne)
        self.foreFiveButton = QPushButton('+5 Frame', parent)
        self.foreFiveButton.clicked.connect(parent.foreFive)
        self.foreTenButton = QPushButton('+10 Frame', parent)
        self.foreTenButton.clicked.connect(parent.foreTen)
        button_layout.addWidget(self.backTenButton)
        button_layout.addWidget(self.backFiveButton)
        button_layout.addWidget(self.backOneButton)
        button_layout.addWidget(self.foreOneButton)
        button_layout.addWidget(self.foreFiveButton)
        button_layout.addWidget(self.foreTenButton)

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

        # A box to show if all files are provided
        #   - h5 file
        #   - video file
        #   - approx. time when the clock appears in the video
        infogrpbox = QGroupBox("Required Info.")
        infovbox = QVBoxLayout()
        infogrpbox.setLayout(infovbox)
        h5checklbl = QLabel(".h5 file loaded")
        vidchecklbl = QLabel("video file loaded")
        infovbox.addWidget(h5checklbl)
        self.h5FileNameLabel = QLabel("")
        infovbox.addWidget(self.h5FileNameLabel)
        infovbox.addWidget(vidchecklbl)
        self.videoFileNameLabel = QLabel("")
        infovbox.addWidget(self.videoFileNameLabel)
        # Need to specify when does the clock appear in the video
        # This can also be used to move to any point in the video
        self.videoCapturePoint = QLineEdit(self)
        videoCapturePointLabel = QLabel("Time in video a clock appears (MM:SS)")
        infovbox.addWidget(videoCapturePointLabel)
        infovbox.addWidget(self.videoCapturePoint)
        # Time when the sensor button was pressed...
        # Anything on
        sensorCapturePoint = QLineEdit()
        sensorCapturePointLabel = QLabel("Time ")

        buttonhbox = QHBoxLayout()
        lock_button = QPushButton("Lock On")
        reset_button = QPushButton("Reset")
        buttonhbox.addWidget(lock_button)
        buttonhbox.addWidget(reset_button)
        infovbox.addLayout(buttonhbox)

        self.videoCapturePoint = None

        self.videoDisplayWidget = VideoDisplayWidget(self)

        # Configuring the central widget
        centralView = QGridLayout()
        centralView.addWidget(infogrpbox, 0, 0, 4, 2)
        centralView.addWidget(self.videoDisplayWidget, 2, 2, 4, 4)

        centralWidget = QWidget()
        centralWidget.setLayout(centralView)

        self.setCentralWidget(centralWidget)

    def backOne(self):
        """backOne."""
        """
        if not self.capture and self.isVideoFileLoaded:
            self.capture = VideoCapture(self.videoFileName, self.videoDisplayWidget)
        """
        print(f"Frame Number: {self.capture.frameNumber}")
        self.capture.moveByFrames(slot=self.capture.nextFrameSlot, count=-1)

    def backFive(self):
        print(f"Frame Number: {self.capture.frameNumber}")
        self.capture.moveByFrames(slot=self.capture.nextFrameSlot, addFrame=-5)

    def backTen(self):
        print(f"Frame Number: {self.capture.frameNumber}")
        self.capture.moveByFrames(slot=self.capture.nextFrameSlot, addFrame=-10)

    def foreOne(self):
        print(f"Frame Number: {self.capture.frameNumber}")
        self.capture.moveByFrames(slot=self.capture.nextFrameSlot, addFrame=1)

    def foreFive(self):
        print(f"Frame Number: {self.capture.frameNumber}")
        self.capture.moveByFrames(slot=self.capture.nextFrameSlot, addFrame=5)

    def foreTen(self):
        print(f"Frame Number: {self.capture.frameNumber}")
        self.capture.moveByFrames(slot=self.capture.nextFrameSlot, addFrame=10)

    def loadVideoFile(self):
        try:
            self.videoFileName = QFileDialog.getOpenFileName(self, "Select a .h264 video file")[0]
            shortform = self.videoFileName.split(sep="/")[-1]
            self.videoFileNameLabel.setText(shortform)
            self.isVideoFileLoaded = True
            self.capture = VideoCapture(self.videoFileName, self.videoDisplayWidget)
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
