import napari
from magicgui import magicgui
import numpy as np
from aicsimageio import AICSImage
import matplotlib.pyplot as plt
import os
from pathlib import Path
import tifffile
import argparse

# Performs Radial Profile Calculation
# Function Comes From: https://stackoverflow.com/questions/21242011/most-efficient-way-to-calculate-radial-profile
# Answer provided on StackOverflow by user Bi Rico
def radial_profile(data, center):
    y, x = np.indices((data.shape))
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2).astype(int)
    
    tbin = np.bincount(r.ravel(), data.ravel())
    nr = np.bincount(r.ravel())
    
    radialprofile = tbin / nr # MEAN
    #radialprofile = tbin # SUM
    
    return radialprofile

# Checks if a path exists, creating it if it does not
def checkPath(path):
    if not os.path.exists(path):
        os.makedirs(path)


def main():

    parser = argparse.ArgumentParser(description='Performs a Radial Profile Analysis on User-Defined ROIs')
    parser.add_argument('-i','--input', help='Provide the Input File Path', required=True)
    parser.add_argument('-o','--output', help='Provide the Output file Path. If unspecified, write all files to current working directory', required=False)
    parser.add_argument('-c','--channels', nargs='+', help='Define Channel Names to View in Napari', required=True)
    parser.add_argument('-s', '--specifiedChannel', help = "Specifiy the Channel Intensity Will Be Measured From", required=True)
    args = parser.parse_args()

    # Do Error Handling of Command Line Arguments.
    if args.specifiedChannel not in args.channels:
        print('Specified Channel "' + args.specifiedChannel + '" is not in List of Channels')
        exit(1)

    # Read this in with the command line.
    inputPath = Path(args.input)
    outputPath = Path(args.output) / Path("RadialProfiles") if args.output != None else Path("./RadialProfiles")
    checkPath(outputPath)


    # Try to open the specified image.
    try:
        img = AICSImage(inputPath)
    except:
        print("Invalid Input File: " + str(inputPath))
        print("Check If Specified Path is Incorrect")
        exit(1)


    # The supplied .lif file has multiple scenes, each corresponding to different conditions.
    for index,scene in enumerate(img.scenes):

        img.set_scene(index)
        
        # Set appropriate channel colors and layer labels
        labels = args.channels + ["Unspecified" for channel in range(len(args.channels) - 3)]
        colormaps = ["blue" , "red", "green"] + ["grey" for channel in range(len(args.channels) - 3)]
        
        # In Case the # Of Points != # ROIs
        dimMatch = False
        # Stores previous iterations ROI and center information to be added back to re-opened viewer after it
        # is closed in the case that the # points != # ROIs.
        roiLayer = None
        centerLayer = None

        while dimMatch == False:

            # Create a viewer of the current image.
            view = napari.Viewer()
            view.add_image(img.data,
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
            napari.run()

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
        checkPath(scenePath)
            
        
        for index in range(len(view.layers["Centers"].data)):

            # Get current info
            currCenter = view.layers["Centers"].data[index]
            currRoi = view.layers["ROIs"].data[index]
            currMask = masks[index]

            # Create Mask for Cropping and add it as a new layer
            maskArray = np.where(currMask==1, view.layers[args.specifiedChannel].data , currMask.astype(int))
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
            checkPath(roiPath)
            imgPath = roiPath / Path("ROI_" + str(index) + ".tiff")
            tifffile.imwrite(imgPath  , cropped)

            oldX, oldY = currCenter[0], currCenter[1]
            newX, newY = int(oldX - xmin), int(oldY-ymin)

            # Save the center point information into a CSV.
            csvPath = roiPath / Path("center.csv")
            with open(csvPath, 'w') as f:
                f.write(str(newX) + "," + str(newY))

            # Calculate the radial profile
            rad = radial_profile(cropped, (newY,newX))

            # Save the Radial Profile Data into a csv
            radPath = roiPath / Path("radial.csv")
            with open(radPath, "w") as f:
                for index,intensity in enumerate(rad):
                    f.write(str(intensity))
                    f.write("\n")

            plt.plot(rad)
            plt.savefig(roiPath / Path("RadialPlot.png"))
            plt.close()

if __name__ == "__main__":
    main()