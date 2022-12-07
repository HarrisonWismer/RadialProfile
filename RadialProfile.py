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
        self.selectedChannels = selectedChannels[0]
        print(self.selectedChannels)
        self.pixelSize = pixelSize
        self.unit = unit

    def simplePlot(self,x,y,path):
        """
        Output a simple plot for quick visualization purposes.
        Input: X values, Y values, Path that includes a file name
        Output: A Plot
        """
        plt.plot(x,y)
        plt.xlabel("Radius [" + self.unit + "]")
        plt.ylabel("Normalized Intensity")
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
                        - radial.csv -> A file containing the radial data from the ROI. Can be read using np.loadtxt()
                        - ROI_n.tiff -> A TIFF file of the ROI with bounding box blacked out.
                        - RadialPlot.png -> An image of the plotted Radial Profile.
        """

        outputPath = outputPath / Path("RadialProfiles")
        self.checkPath(outputPath)

        # The supplied .lif file has multiple scenes, each corresponding to different conditions.
        for scene in self.scenes:
            
            origScene = self.sceneDict[scene]
            index = self.image.scenes.index(origScene)
            sceneName = scene.replace(":","_").replace("/","_")

            self.image.set_scene(index)
            
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
                        roiLayer = view.add_shapes(roiLayer.data, name="ROIs")
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
            print(y,x)

            # Creates a mask for every ROI drawn which is then used to "crop" the image.
            masks = view.layers["ROIs"].to_masks(mask_shape=(y,x))

            # User can draw ROI's on whichever Z-Slice they want. Save the current Z-Slice.
            currZ = view.dims.current_step[1]

            # Create the folder within the current working directory to save all of the ROI information.
            scenePath = outputPath / sceneName
            self.checkPath(scenePath)
            with open(scenePath / Path(sceneName + "_Table.csv"), "a") as f:
                print("ROI,RelativeCenterX,RelativeCenterY,AbsoluteCenterX,AbsoluteCenterY,RadialPath,RadialPlotPath,RoiTiffPath",file=f)
            
            for index in range(len(view.layers["Centers"].data)):

                # Get current info
                currCenter = view.layers["Centers"].data[index]
                currRoi = view.layers["ROIs"].data[index]
                currMask = masks[index]

                # Create Mask for Cropping and add it as a new layer
                maskArray = np.where(currMask==1, view.layers[self.selectedChannels].data , currMask.astype(int))
                view.add_image(maskArray, name = "ROI_" + str(index))

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
                

                # Create numpy array of cropped image.
                print(ymin,ymax,xmin,xmax)
                cropped = view.layers["ROI_" + str(index)].data[0][currZ][int(ymin):int(ymax),int(xmin):int(xmax)]

                # Save cropped ROI image
                roiPath = scenePath / Path("ROI_" + str(index))
                self.checkPath(roiPath)
                imgPath = roiPath / Path("ROI_" + str(index) + ".tiff")
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
                xRad = np.asarray([ind * self.pixelSize for ind in range(len(yRad))])

                # Save the Radial Profile Data into a csv
                radPath = roiPath / Path("Radial.csv")
                with open(radPath, "w") as f:
                    for x, y in zip(xRad,yRad):
                        print(str(x) + "," + str(y), file = f)
                    #for ind,intensity in enumerate(rad):
                    #    print(str(ind * self.pixelSize) + "," + str(intensity), file=f)

                plotPath = roiPath / Path("RadialPlot.png")
                self.simplePlot(xRad, yRad, plotPath)

                with open(scenePath / Path(sceneName + "_Table.csv"), "a") as f:
                    print("{},{},{},{},{},{},{},{}".format("ROI_" + str(index), 
                                                        str(newX),
                                                        str(newY),
                                                        str(oldX),
                                                        str(oldY),
                                                        str(radPath),
                                                        str(plotPath),
                                                        str(imgPath)),
                                                        file=f)


    def analyzeProfiles(self,outputPath, fraction):
        """
        Implement the analysis protocol implemented utilized in:
            Article Source: Reversible association with motor proteins (RAMP): A streptavidin-based method to manipulate organelle positioning
            Guardia CM, De Pace R, Sen A, Saric A, Jarnik M, et al. (2019) Reversible association with motor proteins (RAMP): A streptavidin-based 
            method to manipulate organelle positioning. PLOS Biology 17(5): e3000279. 
            https://doi.org/10.1371/journal.pbio.3000279 

            1) Normalizes radius values (X-Values) between 0 and 1
            2) Finds the minimum distance that contains x (fraction specified by the user) of the total intesity
            3) Saves the radius within the ROI folder
            4) Calculates the average radius holding x of the total intensity for the entire sample.

        Input:
            - outputPath -> A specified path to write data to
            - fraction -> A specified float f (0.00 < f <= 1.00)

        Output:
            - scene_MasterTable.csv -> Output table that combines the original scene_Table.csv with analysis specific columns.
            - RadialNormalized.csv -> Normalized (x values) Radial Profile data
            - RadialPlotNormalized.png -> Normalized Radial Plot
        """

        outputPath = Path(outputPath)
        
        # List of scene average radii for each scene self.scenes
        sceneMeans = []

        # Go back over all of the scenes from the current run of the program and run the analysis protocol.
        for scene in self.scenes:

            scene = scene.replace(":","_").replace("/","_")
            scenePath = outputPath / Path("RadialProfiles/" + scene)

            minRads = []

            with open(scenePath / Path(scene + "_AnalysisTable.csv"), "a") as f:
                print("ROI,Fraction,MinimumRadius,RadialNormalizedPath,RadialPlotNormalizedPath", file=f)
            
            # Each ROI in the scene
            for roi in scenePath.iterdir():
                # Make sure roi is not a .csv file that could be residing in the directory.
                if roi.is_dir():
                
                    # Read in the previously generated Radial Profile
                    radialProfile = np.loadtxt(roi / Path("Radial.csv"),delimiter=",")

                    yValues = radialProfile[:,1]
                    xValues = radialProfile[:,0]

                    # Normalize X values between 0 and 1
                    normalizedX = xValues / np.max(xValues)

                    # Write out the normalized radial profile data
                    normPath = roi / Path("RadialNormalized.csv")
                    with open(normPath, "w") as f:
                        for x,y in zip(normalizedX, yValues):
                            print(str(x) + "," + str(y),file=f)

                    # Save the plot of the normalized data
                    plotNorm = roi / Path("RadialPlotNormalized.png")
                    self.simplePlot(normalizedX, yValues, plotNorm)

                    # Create array of cumulative intensities and look for the X that contains the fractional intensity.
                    cumulIntensity = np.cumsum(yValues)
                    # np.argmax will return the index of the first value that exceed the fractional intensity desired.
                    fracMinIndex = np.argmax(cumulIntensity >= (np.sum(yValues) * fraction))
                    # Index into normalized values to get minimum radius holding fraction f of the intensity.
                    xFractionalMin = normalizedX[fracMinIndex]
                    minRads.append(xFractionalMin)

                    # Write out the AnalysisTable
                    radPath = roi / Path("FractionalRadius.csv")
                    with open(scenePath / Path(scene + "_AnalysisTable.csv"), "a") as f:
                        print("{},{},{},{},{}".format(roi.name,
                                                        str(fraction),
                                                        str(xFractionalMin),
                                                        str(normPath),
                                                        str(radPath)), 
                                                        file=f)
                
                # Skip files that aren't directories
                else:
                    continue
            
            # Read in original table and new analysis table and combine the two, and write it out
            originalTable = pd.read_csv(scenePath / Path(scene +"_Table.csv"),index_col="ROI")
            analysisTable = pd.read_csv(scenePath / Path(scene + "_AnalysisTable.csv"),index_col="ROI")
            newTable = originalTable.join(analysisTable)
            newTable.to_csv(scenePath / Path(scene + "_MasterTable.csv"))

            # Try to remove the 2 old tables
            try:
                os.remove(scenePath / Path(scene + "_Table.csv"))
                os.remove(scenePath / Path(scene + "_AnalysisTable.csv"))
            except:
                pass
            
            # Calculate the mean minimum radius for the whole scene
            minRads = np.array(minRads)
            minMean = np.mean(minRads)
            sceneMeans.append(minMean)
        
        for scene,mean in zip(self.scenes,sceneMeans):
            with open(outputPath / Path("RadialProfiles/SceneMeanMinRads.txt"), "a") as f:
                print(scene, ":", str(mean), file=f)