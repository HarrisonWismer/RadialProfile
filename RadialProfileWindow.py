import sys
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
        self.selectedChannels = None
        self.pixelSize = None
        self.unit = None
        self.reload = False
        self.maxIntensity = False
        self.doBackgroundSubtract = False
        self.backgroundChannels = []
        self.numStdDevs = 0

        # Click Events for UI
        self.loadBrowse.clicked.connect(self.browseInputFiles)
        self.outputBrowse.clicked.connect(self.browseOutputFiles)
        self.selectAllSamples.clicked.connect(self.selectAllScenes)
        self.clearAllSamples.clicked.connect(self.clearAllScenes)
        self.selectAllChannels.clicked.connect(self.selectChannels)
        self.clearAllChannels.clicked.connect(self.clearChannels)

        self.sampleList.itemSelectionChanged.connect(self.loadUpScenes)
        self.channelList.itemSelectionChanged.connect(self.channelSelection)
        self.backSubChannels.itemSelectionChanged.connect(self.backChannelSelection)
        self.xyScale.valueChanged.connect(self.setPixelSize)
        self.stdDevs.valueChanged.connect(self.setStdDevs)
        self.unitLabel.textChanged.connect(self.setUnit)
        self.reloadROI.stateChanged.connect(self.reloadROIs)
        self.maxIntCheck.stateChanged.connect(self.maxIntChanged)
        self.backgroundSubtract.stateChanged.connect(self.doBackgroundSubtraction)
        self.runButton.clicked.connect(self.createRadialProfile)

    def openFile(self, fpath):
        """
        Opens the file path specified by the user
        """

        path = Path(fpath)
        self.image = AICSImage(path)
        self.sampleList.clear()

        xScale = self.image.physical_pixel_sizes[2]
        if xScale == None:
            self.xyScale.setValue(1)
            self.pixelSize = self.xyScale.value()
            self.unitLabel.setText("Pixels")
        else:
            self.pixelSize = xScale
            self.xyScale.setValue(self.pixelSize)
            self.unitLabel.setText("Microns")

        self.unit = self.unitLabel.text()

        if path.suffix != ".lif":
            sceneNames = [str(path.name).split(".")[0] + "_" + str(index) for index in range(len(self.image.scenes))]
            self.sceneDict = {sceneName:scene for sceneName,scene in zip(sceneNames, self.image.scenes)}
            self.scenes = list(self.sceneDict.keys())
            self.sampleList.addItems(list(self.sceneDict.keys()))

        else:
            self.sceneDict = {scene:scene for scene in self.image.scenes}
            self.scenes = list(self.sceneDict.keys())
            self.sampleList.addItems(list(self.sceneDict.keys()))


        # Assumes each sample has the same number of channels
        nChannels = self.image.data.shape[1]
        self.channels = []
        self.channelList.clear()
        self.backSubChannels.clear()
        self.channels = ["Channel_" + str(num+1) for num in range(nChannels)]
        self.channelList.addItems(self.channels)
        self.backSubChannels.addItems(self.channels)

    def browseInputFiles(self):
        """
        This reads in an image file specified by the user (currently only tested on .LIF files)
        """
        # Allow user to browse through computer files to select input file.
        file = QFileDialog.getOpenFileName(self, "Select Input File")
        self.inputLine.setText(file[0])

        try:
            self.openFile(self.inputLine.text())
        except:
            self.inputLine.setText("Error Reading Image File")

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

    def selectChannels(self):
        self.channelList.selectAll()

    def clearChannels(self):
        self.channelList.clearSelection()

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
            self.selectedChannels = [channel.text() for channel in self.channelList.selectedItems()]
        except:
            pass

    def backChannelSelection(self):
        try:
            self.backgroundChannels = [channel.text() for channel in self.backSubChannels.selectedItems()]
        except:
            pass

    def reloadROIs(self):
        self.reload = self.reloadROI.isChecked()

    def maxIntChanged(self):
        self.maxIntensity = self.maxIntCheck.isChecked()

    def doBackgroundSubtraction(self):
        self.doBackgroundSubtract = self.backgroundSubtract.isChecked()

    def createRadialProfile(self):
        """
        This should be the final step in the GUI procedure. If any of the attributes are None, the RadialProfiler
        object will not be able to be instantiated. This checks if any of these attributes are none and displays a
        message if one of the steps has been missed.
        """

        # Check if object can be instantiated, otherwise do nothing
        if (self.image is not None and self.scenes is not None and 
            self.channels is not None and self.selectedChannels is not None and 
            self.sceneDict is not None and self.pixelSize is not None 
            and self.unit is not None and len(self.selectedChannels) != 0):

            self.rp = rp.RadialProfiler(self.image, 
                                        self.scenes, 
                                        self.sceneDict, 
                                        self.channels, 
                                        self.selectedChannels, 
                                        self.pixelSize, 
                                        self.unit,
                                        self.reload,
                                        self.maxIntensity,
                                        self.doBackgroundSubtract,
                                        self.backgroundChannels,
                                        self.numStdDevs)
            self.rp.executeScript(Path(self.outputLine.text()))
            self.rp = None
            self.openFile(self.inputLine.text())

        else:
            pass

    def setPixelSize(self):
        self.pixelSize = self.xyScale.value()

    def setUnit(self):
        self.unit = self.unitLabel.text()

    def setStdDevs(self):
        self.numStdDevs = self.stdDevs.value()

def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
if __name__=="__main__":
    main()





