import napari
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
import tifffile
import pandas as pd
import diplib as dip

class RadialProfiler:
    """
    Class user to perform radial profile analysis on image data.
    Inputs:
        - image -> A AICSImage instance from the aicsimageio package
        - scenes -> Scene names from the image in which to open Napari Viewers for.
        - channels -> A List of channel names for each channel in the image
        - selectedChannel -> The name of the channel from which intensity values will be taken.
    """

    def __init__(self, image, scenes, sceneDict, channels, selectedChannels, pixelSize, unit):
        self.image = image
        self.scenes = scenes
        self.sceneDict = sceneDict
        self.channels = channels
        self.selectedChannels = sorted(selectedChannels)
        self.pixelSize = pixelSize
        self.unit = unit

    def simplePlot(self, x, y, channels, path):
        """
        Output a simple plot for quick visualization purposes.
        Input:  List of 1 of x values with same length as each list in y
                List of 1 or more lists of y values
                Channel names for labels (should be length of x and y)
                Path that includes a file name
        Output: A Plot of radial profiles for each channel
        """
        
        for yVals,channel in zip(y,channels):
            plt.plot(x, yVals, label = channel)

        plt.xlabel("Radius [" + self.unit + "]")
        plt.ylabel("Normalized Intensity")
        plt.legend()
        plt.savefig(path)
        plt.close()

    def checkPath(self, path):
        '''
        Since the user specifies the output folder, new folders may need to be created.
        This function takes a PathLib Path object as input and created a directory at the
        path if it does not already exist.
        '''
        if not os.path.exists(path):
            os.makedirs(path)

    def executeScript(self, outputPath):
        """
        This script executes the entire radial profile analysis:

        Input:
            - outputPath: An output path specified by the user

        Output:
            - A folder called RadialProfiles containing:
                - A single folder for each sample labeled with the sample name each containing:
                    - A folder for each ROI drawn, named with convention ROI_n, each containing:
                        - center.csv -> A file containing the center point of the circle used for analysis/
                        - radial.csv -> A csv file with x values and subsequent y values for each channel
                        - ROI_n.tiff -> A TIFF file of the ROI with bounding box blacked out.
                        - RadialPlot.png -> An image of the plotted Radial Profile.
        """

        outputPath = outputPath / Path("RadialProfiles")
        self.checkPath(outputPath)

        # Iterate through the selected scenes/samples
        for scene in self.scenes:
            
            # Using the friendly scene name, get the original scene name from the AICSImage object.
            origScene = self.sceneDict[scene]
            ind = self.image.scenes.index(origScene)
            sceneName = scene.replace(":","_").replace("/","_")

            self.image.set_scene(ind)
            
            # Set appropriate channel colors and layer labels
            labels = self.channels
            colormaps = ["blue" , "red", "green"] + ["gray" for i in range(self.image.data.shape[1])]
            
            # In Case the # Of Points != # ROIs
            dimMatch = False
            # Stores previous iterations ROI and center information to be added back to re-opened viewer after it
            # is closed in the case that the # points != # ROIs.
            roiLayer = None
            centerLayer = None

            while dimMatch == False:

                # Create a viewer of the current image.
                view = napari.Viewer(show=False)
                view.add_image(self.image.data,
                            channel_axis=1, 
                            name=labels,
                            colormap=colormaps)
                

                # Create the roiLayer (either with pre-existing or no data)
                if roiLayer == None:
                    roiLayer = view.add_shapes(name="ROIs")
                else:
                    if len(roiLayer.data) != 0:

                        # Try adding each type of shape to avoid type errors
                        try:
                            roiLayer = view.add_shapes(roiLayer.data, name="ROIs", shape_type="ellipse")
                        except:
                            try:
                                roiLayer = view.add_shapes(roiLayer.data, name="ROIs", shape_type="polygon")
                            except:
                                try:
                                    roiLayer = view.add_shapes(roiLayer.data, name="ROIs", shape_type="rectangle")
                                except:
                                    print("WARNING: UNABLE TO CREATE ADD SHAPES (Use only Polygon, Ellipse, Rectangle")
                                    pass

                    else:
                        roiLayer = view.add_shapes(name="ROIs")

                # Create Center Layer (")
                if centerLayer == None:
                    centerLayer = view.add_points(name="Centers")
                else:
                    centerLayer = view.add_points(centerLayer.data, name="Centers")

                # Halt execution here while user draws ROI's
                # When the viewer is closed, the rest of the code will run.
                view.show(block=True)

                # If the # Centers == # ROIs, clear pevious data (moves on to next slide)
                # Else the viewer will re-open with previous data.
                if len(centerLayer.data) == len(roiLayer.data):
                    dimMatch = True
                    roiLayer = False
                    centerLayer = False

            # This grabs the (Y X X) image size into variables x and y
            y, x = view.layers[0].data.shape[2:]

            # Creates a mask for every ROI drawn which is then used to "crop" the image.
            masks = view.layers["ROIs"].to_masks(mask_shape=(y,x))

            # User can draw ROI's on whichever Z-Slice they want. Save the current Z-Slice.
            currZ = view.dims.current_step[1]

            # Create the folder within the current working directory to save all of the ROI information.
            scenePath = outputPath / sceneName
            self.checkPath(scenePath)
            with open(scenePath / Path(sceneName + "_Table.csv"), "w") as f:
                print("ROI,RelativeCenterY,RelativeCenterX,AbsoluteCenterY,AbsoluteCenterX,RadialPath,RadialPlotPath", file=f)
            
            for index in range(len(view.layers["Centers"].data)):

                # Get current info
                currCenter = view.layers["Centers"].data[index]
                currRoi = view.layers["ROIs"].data[index]
                currMask = masks[index]

                # Get Min and Max x and y coordinates to create a new image from the cropped image
                ymin, xmin = np.min(currRoi, axis=0).astype(int) 
                ymax, xmax = np.max(currRoi, axis=0).astype(int)

                if xmin < 0: xmin = 0
                if xmin > x: xmin = x
                if xmax > x: xmax = x
                if xmax < 0: xmax = 0
                if ymin < 0: ymin = 0
                if ymin > y: ymin = y
                if ymax > y: ymax = y
                if ymax < 0: ymax = 0


                # List of lists to hold each set of intensity values from each channel
                yRPs = []
                # Create Mask for Cropping and add it as a new layer
                for channel in self.selectedChannels:

                    maskArray = np.where(currMask==1, view.layers[channel].data , currMask.astype(int))
                    view.add_image(maskArray, name = "ROI_" + str(index) + channel)

                    # Create numpy array of cropped image.
                    cropped = view.layers["ROI_" + str(index) + channel].data[0][currZ][ymin:ymax,xmin:xmax]

                    # Save cropped ROI image
                    roiPath = scenePath / Path("ROI_" + str(index))
                    self.checkPath(roiPath)
                    imgPath = roiPath / Path("ROI_" + str(index) + "_" + channel + ".tiff")
                    tifffile.imwrite(imgPath  , cropped)

                    oldY, oldX = int(currCenter[0]), int(currCenter[1])
                    newX, newY = int(oldX - xmin), int(oldY-ymin)

                    # Calculate the radial profile
                    rp = dip.RadialMean(cropped, binSize=1, center=(newX,newY))

                    # Find the longest distance from center to one of the edges and use that distance as the radius
                    maxRads = [abs(xmin-oldX), abs(xmax-oldX), abs(ymin-oldY), abs(ymax-oldY)]
                    radius = max(maxRads)
                    if radius > len(rp):
                        radius = len(rp)

                    yRad = np.asarray(rp[:int(radius)])
                    yRPs.append(yRad)

                # Adjust x (Distance) values using specified pixel size
                xRad = np.asarray([ind * self.pixelSize for ind in range(len(yRPs[0]))])

                radPath = roiPath / Path("Radial.csv")
                with open(radPath, "w") as f:
                    print("Distance [" + self.unit + "]", file=f, end = "")
                    for channel in self.selectedChannels:
                        print("," + channel, file=f, end = "")
                    print(file=f)

                    for xIndex in range(len(xRad)):
                        print(xRad[xIndex], file=f, end ="")
                        for currChannel in range(len(yRPs)):
                            print("," + str(yRPs[currChannel][xIndex]), file=f, end = "")
                        print(file=f)
                    
            
                plotPath = roiPath / Path("RadialPlot.png")
                self.simplePlot(xRad, yRPs, self.selectedChannels, plotPath)

                with open(scenePath / Path(sceneName + "_Table.csv"), "a") as f:
                    print("{},{},{},{},{},{},{}".format("ROI_" + str(index), 
                                                        str(newX),
                                                        str(newY),
                                                        str(oldX),
                                                        str(oldY),
                                                        str(radPath),
                                                        str(plotPath)),
                                                        file=f)