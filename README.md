# RadialProfile Script

Radial Profiling of User-Defined ROIs Using Napari.

Radial Profile analysis measures the intensity around a specified point as a function of distance. The basic idea is that a
center point and radius are specified, and pixel intensity values within each ring (at each radius value) around the center are added up and divided by the total number of pixels in that ring. This is done at each radius value up until the specified radius.

This script in particular, aims to make performing this type of radial profile analysis easier and faster. All that needs to be done is to manually draw ROIs with their center points. The smallest possible bounding box is then fit around the drawn ROI with pixels within the bounding box but outside of the ROI blacked out. The radial profile is then taken, with radius values increasing until reaching the edge of the image.

This plugin was inspired by the ImageJ [Radial Profile Plugin](https://imagej.nih.gov/ij/plugins/radial-profile.html) and [Radial Profile Extended Plugin](https://imagej.nih.gov/ij/plugins/radial-profile-ext.html). This plugin aims to perform the same kind of analysis as these plugins while also being easier to use when profiling multiple/many regions of interest.

## Dependencies:
There is a provided Conda Environment file camed rpEnv.yml that can be used to create a Conda environment with all dependencies already installed.

To create the environment open the conda command prompt and enter the following command to create an environment named napariEnv:

conda env create -f rpEnv.yml

This will create a new Conda environment named napariEnv with all dependencies installed.

If performing a manual installation of necessary packages, the following packages must be installed to use the script:
- napari
- numpy
- aicsimageio
- readlif
- aicspylibczi
- matplotlib
- pathlib
- tifffile
- diplib

## Usage:
To run the program, simply run the RunRadialProfile.py file.

Ex: >$ python RunRadialProfile.py

This will bring up the GUI through which all necessary interaction with the program can be done Once in the GUI complete each step in the orders shown.

NOTE: When specifying an output directory, a folder called RadialProfiles is created. IF re-running the plugin, currently if the same scene/sample is run again and the same output directory specified, contents will be OVERWRITTEN. However, if using the same output directory and running the plugin on a new scene/sample, a new folder for that sample will be created.

1. Specify an input file.
2. Specify an output directory. 
3. Use the mouse to select which samples will be run through the program.
4. Use the mouse to select which channel intenstity values will be taken from in the analysis.
5. Verify Pixel Scales & Units and set values manually if needed.
6. If using the same output directory used in a previous run, decide if ROIs should be reloaded for scenes already run.
7. Click Run

## Interaction:
Upon successfully running the program through the GUI, a Napari Viewer with the first scene contained in the image file should appear.

The general workflow is as follows:

1. Navigate to the desired Z-Plane

2. Use any channel as a guide to:

	A) Draw an ROI Using the shapes layer named "ROIs" which can be found on the left. Using the polygon shape tool is encouraged.

	B) Place a Center Point using the points layer named "Centers" which can be found on the left. Place this where you want the center of the Radial Profile circle to be.
	   Note that this center point does not need to be placed in the center of the ROI defined.

	**IMPORTANT: ROI's and Center Points must be created in the same order to be properly associated with each other. It is recommend to draw 1 ROI and then 
	immediately place its center point or vice versa. A less feasible but still valid approach would be to draw all ROIs and then place all center points in the SAME ORDER the ROIs were added. 
	What CANNOT be done is to create ROI_1, create ROI_2, place ROI_2's center point and then place ROI_1's center point. This will associate ROI_2 with ROI_1's 
	center point and vice versa.**

3. Repeat step 2 for all desired ROI's.

4. When done, close down the Napari Viewer by clicking the X in the top right corner. The Viewer may re-open with the same scene and same ROIs, in which case the number of ROI's is not the same as the number of center points placed. In this case it may be easier to delete all ROIs and points to make sure that each ROI is correctly associated with each point. If the number of ROIs matches the number of center points, a new viewer displaying the next scene will pop up. Repeat steps 1-3 for each scene until no new Viewer pops up.

5. View the specified output folder to see the results.

- **Note:**
	- Currently, the plugin does not know if it has already been run on a certain image. If you missed some ROIs in a certain pass of the program, if you re-run usign the same output folder, the previous results will be overwritten. It is advised to try to run all in one go, or change output folder, manually change ROI numbers, and consolidate manually if needed.

## Output:

Once the steps above are complete there should be a new folder called RadialProfiles present at the specified output path.

RadialProfiles (folder) -> Folder For Each Sample/Scene -> Folder For Each ROI Within Sample

The RadialProfiles folder contains:
- A folder for each scene

Each Sample/Scene folder contains:
- A folder for each ROI
- sceneName_Table.csv -> A CSV file with a row for each ROI in the scene/sample with the following columns/attributes:
	- The ROI Number
	- The relative Y coordinate of the radial centerpoint (Adjusted in terms of the cropped image coordinates)
	- The relative X coordinate of the radial centerpoint (Adjusted in terms of the cropped image coordinates)
	- The absolute Y coordinate of the radial centerpoint (In terms of the original image)
	- The absolute X coordinate of the radial centerpoint (In terms of the original image)
	- The path to the Radial.csv file which contains the radial profile values for each specified channel for each ROI
	- The path to the radial profile plot
	- The path to the ROI_n_Coordinates.csv file with coordinate points to reload each ROI
	- The type of shape for the ROI to be used when loading ROIs back in


Each ROI folder contains:
- ROI_n_Channel_m.tiff -> Cropped ROI region saved in a .tiff file for the nth ROI defined and the mnth channel specified.
- RadialPlot.png -> A basic plot of the radial profile
- Radial.csv -> The resulting data from the radial profile analysis with x values in the Distance column and y values in the channel_n column.
- ROI_n_Coordinates.csv -> The coordinates of the ROI itself. Used to reload in previous ROIs.

- **Note:**
	- Radial.csv can be read into a dataframe easily with pandas using pd.read_csv("Radial.csv"). After doing this the plots can be easily recreated by calling .plot() on the dataframe.
	- The master scene tables can be read in with pandas using pd.read_csv(path)
