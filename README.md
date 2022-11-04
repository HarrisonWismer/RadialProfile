# RadialProfile Script

Radial Profiling of User-Defined ROIs Using Napari

## Dependencies:
The following packages must be installed to use the script:
- napari
- numpy
- aicsimageio
- readlif
- matplotlib
- pathlib
- tifffile
- os
- argparse

## Usage:
To run the program, simply run the RunRadialProfile.py file.

Ex: >$ python RunRadialProfile.py

This will bring up the GUI through which all necessary interaction with the program can be done Once in the GUI complete each step in the orders shown.

1. Specify an input file.
2. Specify an output directory.
3. Use the mouse to select which samples will be run through the program.
4. Use the mouse to select which channel intenstity values will be taken from in the analysis.
5. Toggle the "Ignore Zeros" option to whichever setting is desired.
6. Click Run

## Interaction:
Upon successfully running the program through the GUI, a Napari Viewer with the first scene contained in the .LIF file should appear.

The general workflow is as follows:

1. Navigate to the desired Z-Plane

2. User whatever channel is needed to:

	A) Draw an ROI Using the shapes layer named "ROIs" which can be found on the left. The polygon selection function will be the most accurate.

	B) Draw a Center Point using the points layer named "Centers" which can be found on the left. Place this where you want the center of the Radial Profile circle to be.
	   Note that this center point does not need to be placed in the center of the ROI defined.

	#### IMPORTANT: ROI's and Center Points must be created in the same order to be associated with each other. That means you should probably draw 1 ROI and then immediately place its center point. Less feasible but still OK would be to draw all ROIs and then place all center points in the SAME ORDER the ROIs were added. What you CANNOT do is to create ROI_1, create ROI_2, place ROI_2's center point and then place ROI_1's center point. This will associate ROI_2 with ROI_1's center point and vice versa.

3. Repeat step 2 for all desired ROI's.

4. When done, close down the Napari Viewer by clicking the X in the top right corner. The Viewer may re-open with the same scene and same ROIs, in which case the number of ROI's
is not the same as the number of center points placed. In this case it may be easier to delete all ROIs and points to make sure that each ROI is correctly associated with each point.
If the number of ROIs matches the number of center points, a new viewer displaying the next scene will pop up. Repeat steps 1-3 for each scene until no new Viewer pops up.

Note: If you just want to analyze 1 scene you can keep closing out of undesired scenes without defining and ROIs or center points (this will NOT overwrite any previous analysis on these scenes).

## Output:

Once the steps above are complete there should be a new folder called RadialProfiles present at the specified output path.

The organization is as follows:

RadialProfiles -> Folder For Each Sample -> Folder For Each ROI Within Sample

Each ROI folder contains:
- ROI_n.tiff -> Cropped ROI region saved in a .tiff file for the nth ROI defined.
- RadialPlot.png -> A basic plot of the radial profile.
- radial.csv -> The resulting data from the radial profile analysis. (Read into numpy with np.loadtxt() function).
- center.csv -> File containing the ROI's specified center point, adjusted to the coordinates of the cropped ROI image (ROI_n.tff).