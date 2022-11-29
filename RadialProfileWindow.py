import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt5.uic import loadUi

from aicsimageio import AICSImage
from pathlib import Path

import RadialProfile as rp

class MainWindow(QMainWindow):
    """
    Builds off of radialUI.ui to create a MainWindow child.

    Contains all necessary events to interface with the RadialProfile module to run
    radial profile analysis as outlined in the module.
    """

    def __init__(self):

        super(MainWindow,self).__init__()
        loadUi("radialUI.ui", self)

        # Create RadialProfile Instance Once Able to
        self.rp = None
        # Attributes needed to instantiate RadialProfile instance.
        self.image = None
        self.scenes = None
        self.sceneDict = None
        self.channels = None
        self.selectedChannel = None
        self.fraction = self.fractionIntensity.value()
        self.runAnalysis = False

        # Click Events for UI
        self.loadBrowse.clicked.connect(self.browseInputFiles)
        self.outputBrowse.clicked.connect(self.browseOutputFiles)
        self.selectAllSamples.clicked.connect(self.selectAllScenes)
        self.clearAllSamples.clicked.connect(self.clearAllScenes)
        self.sampleList.itemSelectionChanged.connect(self.loadUpScenes)
        self.channelList.itemSelectionChanged.connect(self.channelSelection)
        self.runButton.clicked.connect(self.createRadialProfile)
        self.fractionIntensity.valueChanged.connect(self.setFraction)


    def browseInputFiles(self):
        """
        This reads in an image file specified by the user (currently only tested on .LIF files)
        """
        # Allow user to browse through computer files to select input file.
        file = QFileDialog.getOpenFileName(self, "Select Input File")
        self.inputLine.setText(file[0])

        try:
            path = Path(self.inputLine.text())
            self.image = AICSImage(path)
            self.sampleList.clear()

            if path.suffix == ".czi":
                sceneNames = [str(path.name).split(".czi")[0] + "-" + str(index) for index in range(len(self.image.scenes))]
                self.sceneDict = {sceneName:scene for sceneName,scene in zip(sceneNames, self.image.scenes)}
                self.scenes = list(self.sceneDict.keys())
                self.sampleList.addItems(list(self.sceneDict.keys()))

            else:
                self.sceneDict = {scene:scene for scene in self.image.scenes}
                self.scenes = list(self.sceneDict.keys())
                self.sampleList.addItems(list(self.sceneDict.keys()))


            # Assumes each sample has the same number ofchannels
            nChannels = self.image.data.shape[1]
            self.channels = []
            self.channelList.clear()
            self.channels = ["Channel_" + str(num+1) for num in range(nChannels)]
            self.channelList.addItems(self.channels)

        except:
            self.inputLine.setText("Cannot Read Image File")

    def browseOutputFiles(self):
        """
        Allows user to select an ouput directory.
        """
        file = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        self.outputLine.setText(file)
    
    def selectAllScenes(self):
        """
        Select all scenes/samples from the QListWidget.
        """
        self.sampleList.selectAll()

    def clearAllScenes(self):
        """
        Deselect/clear all scenes/samples from QListWidget.
        """
        self.sampleList.clearSelection()

    def loadUpScenes(self):
        """
        Load the scenes upon user selecting them into the list of scenes to be run.
        """
        self.scenes = [sample.text() for sample in self.sampleList.selectedItems()]

    def channelSelection(self):
        """
        Get the single channel to be used to measure intensity upon selection in the QListWidget.
        """
        try:
            self.selectedChannel = [channel.text() for channel in self.channelList.selectedItems()][0]
        except:
            pass

    def createRadialProfile(self):
        """
        This should be the final step in the GUI procedure. If any of the attributes are None, the RadialProfiler
        object will not be able to be instantiated. This checks if any of these attributes are none and displays a
        message if one of the steps has been missed.
        """

        # Check if object can be instantiated, otherwise do nothing
        if self.image is not None and self.scenes is not None and self.channels is not None and self.selectedChannel is not None and self.sceneDict is not None:
            self.rp = rp.RadialProfiler(self.image, self.scenes, self.sceneDict, self.channels, self.selectedChannel)
            self.rp.executeScript(Path(self.outputLine.text()))
            # Run downstream analysis option is specified
            if self.analysisButton.isChecked():
                self.rp.analyzeProfiles(self.outputLine.text(),self.fraction)

            self.rp = None

        else:
            pass

    def setFraction(self):
        self.fraction = self.fractionIntensity.value()



def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    widget=QtWidgets.QStackedWidget()
    widget.addWidget(mainWindow)
    widget.setFixedWidth(530)
    widget.setFixedHeight(450)
    widget.show()
    sys.exit(app.exec())
if __name__=="__main__":
    main()





