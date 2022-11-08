import napari
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
import tifffile

class RadialProfiler:
    """
    Class user to perform radial profile analysis on image data.
    Inputs:
        - image -> A AICSImage instance from the aicsimageio package
        - scenes -> Scene names from the image in which to open Napari Viewers for.
        - channels -> A List of channel names for each channel in the image
        - selectedChannel -> The name of the channel from which intensity values will be taken.
    """

    def __init__(self, image, scenes, channels, selectedChannel):
        self.image = image
        self.scenes = scenes
        self.channels = channels
        self.selectedChannel = selectedChannel

    def checkPath(self, path):
        '''
        Since the user specifies the output folder, new folders may need to be created.
        This function takes a PathLib Path object as input and created a directory at the
        path if it does not already exist.
        '''
        if not os.path.exists(path):
            os.makedirs(path)


    def radial_profile(self, data, center):
        '''
        Performs Radial Profile Calculation
        Function Comes From: https://stackoverflow.com/questions/21242011/most-efficient-way-to-calculate-radial-profile
        Answer provided on StackOverflow by user Bi Rico

        Input:
            - data: Image data in the form of an array
            - center: The center-point of the circle
        
        '''
        y, x = np.indices((data.shape))
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2).astype(int)
        
        tbin = np.bincount(r.ravel(), data.ravel())
        nr = np.bincount(r.ravel())
        
        radialprofile = tbin / nr # MEAN
        #radialprofile = tbin # SUM
        
        return radialprofile

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

            index = self.image.scenes.index(scene)

            self.image.set_scene(index)
            
            # Set appropriate channel colors and layer labels
            labels = self.channels
            colormaps = ["blue" , "red", "green"]
            
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


            # This grabs the (X x Y) image size into variables x and y
            s1, s2, x, y = view.layers[0].data.shape

            # Creates a mask for every ROI drawn which is then used to "crop" the image.
            masks = view.layers["ROIs"].to_masks(mask_shape=(x,y))

            # User can draw ROI's on whichever Z-Slice they want. Save the current Z-Slice.
            currZ = view.dims.current_step[1]

            # Create the folder within the current working directory to save all of the ROI information.
            scenePath = outputPath / scene
            self.checkPath(scenePath)
            
            for index in range(len(view.layers["Centers"].data)):

                # Get current info
                currCenter = view.layers["Centers"].data[index]
                currRoi = view.layers["ROIs"].data[index]
                currMask = masks[index]

                # Create Mask for Cropping and add it as a new layer
                maskArray = np.where(currMask==1, view.layers[self.selectedChannel].data , currMask.astype(int))
                view.add_image(maskArray, name = "ROI_" + str(index))

                # Get Min and Max x and y coordinates to create a new image from the cropped image
                xmin, ymin = np.min(currRoi, axis=0).astype(int) 
                xmax, ymax = np.max(currRoi, axis=0).astype(int)

                if xmin < 0: xmin = 0
                if xmax > x: xmax = x
                if ymin < 0: ymin = 0
                if ymax > y: ymax = y 

                # Create numpy array of cropped image.
                cropped = view.layers["ROI_" + str(index)].data[0][currZ][xmin:xmax,ymin:ymax]

                # Save cropped ROI image
                roiPath = scenePath / Path("ROI_" + str(index))
                self.checkPath(roiPath)
                imgPath = roiPath / Path("ROI_" + str(index) + ".tiff")
                tifffile.imwrite(imgPath  , cropped)

                oldX, oldY = currCenter[0], currCenter[1]
                newX, newY = int(oldX - xmin), int(oldY-ymin)

                # Save the center point information into a CSV.
                csvPath = roiPath / Path("center.csv")
                with open(csvPath, 'w') as f:
                    f.write(str(newX) + "," + str(newY))

                # Calculate the radial profile
                rad = self.radial_profile(cropped, (newY,newX))

                # Save the Radial Profile Data into a csv
                radPath = roiPath / Path("radial.csv")
                with open(radPath, "w") as f:
                    for index,intensity in enumerate(rad):
                        f.write(str(intensity))
                        f.write("\n")

                plt.plot(rad)
                plt.savefig(roiPath / Path("RadialPlot.png"))
                plt.close()
        
        self.analyzeProfiles(outputPath,.75)
        

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
        """

        outputPath = Path(outputPath)

        for scene in self.scenes:

            scenePath = outputPath / Path(scene)

            for roi in scenePath.iterdir():

                radialProfY = np.loadtxt(roi / Path("radial.csv"))
                normalizedX = np.arange(len(radialProfY)) / (len(radialProfY)-1)

                plt.plot(normalizedX,radialProfY)
                plt.savefig(roi / Path("RadialPlotNorm.png"))
                plt.close()

                
                cumulIntensity = np.cumsum(radialProfY)
                fracMinIndex = np.argmax(cumulIntensity >= (np.sum(radialProfY) * fraction))
                xFractionalMin = normalizedX[fracMinIndex]

                
                radPath = roi / Path("FractionalRadius.csv")
                # Save in format: fraction,radius
                with open(radPath, "w") as f:
                    f.write("Fraction Specified: " + str(fraction) + "\n")
                    f.write("Minimum Radius Containing Fraction f of total intensity: " + str(xFractionalMin) + "\n")
                



