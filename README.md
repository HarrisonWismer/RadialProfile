# RadialProfile Script

Radial Profiling of User-Defined ROIs Using Napari

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
- matplotlib
- pathlib
- tifffile
- argparse

## Usage:
To run the program, simply run the RunRadialProfile.py file.

Ex: >$ python RunRadialProfile.py

This will bring up the GUI through which all necessary interaction with the program can be done Once in the GUI complete each step in the orders shown.

1. Specify an input file.
2. Specify an output directory.
3. Use the mouse to select which samples will be run through the program.
4. Use the mouse to select which channel intenstity values will be taken from in the analysis.
5. Specify whether downstream analysis is to be run. Set associated values accordingly.
6. Click Run

## Interaction:
Upon successfully running the program through the GUI, a Napari Viewer with the first scene contained in the .LIF file should appear.

The general workflow is as follows:

1. Navigate to the desired Z-Plane

2. Use any channel as a guide to:

	A) Draw an ROI Using the shapes layer named "ROIs" which can be found on the left. The polygon selection will be the most accurate.

	B) Place a Center Point using the points layer named "Centers" which can be found on the left. Place this where you want the center of the Radial Profile circle to be.
	   Note that this center point does not need to be placed in the center of the ROI defined.

	**IMPORTANT: ROI's and Center Points must be created in the same order to be properly registed with each other. It is recommend to draw 1 ROI and then 
	immediately place its center point. A less feasible but still valid approach would be to draw all ROIs and then place all center points in the SAME ORDER the ROIs were added. 
	What CANNOT be done is creating ROI_1, create ROI_2, place ROI_2's center point and then place ROI_1's center point. This will associate ROI_2 with ROI_1's 
	center point and vice versa.**

3. Repeat step 2 for all desired ROI's.

4. When done, close down the Napari Viewer by clicking the X in the top right corner. The Viewer may re-open with the same scene and same ROIs, in which case the number of ROI's is not the same as the number of center points placed. In this case it may be easier to delete all ROIs and points to make sure that each ROI is correctly associated with each point. If the number of ROIs matches the number of center points, a new viewer displaying the next scene will pop up. Repeat steps 1-3 for each scene until no new Viewer pops up.

5. View the specified output folder to see the results.

## Output:

Once the steps above are complete there should be a new folder called RadialProfiles present at the specified output path.

Note that the files present will differ slightly depending on whether or not the downstream analysis was run. Any difference will be noted below with **DS** tag.
The organization is as follows:

RadialProfiles (folder) -> Folder For Each Sample -> Folder For Each ROI Within Sample

The RadialProfiles folder contains:
- A folder for each scene
- **DS:** SceneMeanMinRads.txt -> A file containing the mean minimum radius which contains the specified fraction of the total intensity for each scene/sample.

Each Sample folder contains:
- A folder for each ROI
- sceneName_table.csv -> A CSV file with a row for each ROI in the scene/sample with the following columns/attributes:
	- The ROI Number
	- The relative X coordinate of the radial centerpoint (Adjusted in terms of the cropped image coordinates)
	- The relative Y coordinate of the radial centerpoint (Adjusted in terms of the cropped image coordinates)
	- The absolute X coordinate of the radial centerpoint (In terms of the original image)
	- The absolute Y coordinate of the radial centerpoint (In terms of the original image)
	- The path to the Radial.csv file which contains the (x,y) pairs generated from the radial profile analysis
	- The path to the radial profile plot
	- The path to the ROI TIFF image file

- **DS:** sceneName_table.csv will be **replaced** by **SceneName_MasterTable.csv** a CSV file containing a row for each ROI with the following columns/attributes:
	- All of the afformentioned fields contained in sceneName_table.csv
	- The Fraction specified by the user
	- The Minimum Radius containing the specified fraction of the total intensity for each ROI
	- RadialNormalizedPath -> Contains the paht to the radial profile data where x values have been normalized per the protocol (see below)
	- RadialPlotNormalizedPath.csv -> Contains the path to the plot of the normalized radial profile data

Each ROI folder contains:
- ROI_n.tiff -> Cropped ROI region saved in a .tiff file for the nth ROI defined
- RadialPlot.png -> A basic plot of the radial profile
- Radial.csv -> The resulting data from the radial profile analysis containing (x,y) pairs. (Can be read into numpy with the np.loadtxt() function)

- **DS:**
	- RadialNormalized.csv -> (x,y) pairs resulting from the radial profile analysis in which x values (distances) have been normalized per the protocol (see below)
	- RadialPlotNormalized.png -> Plot of normalized radial profile

- **Note:**
	- Both Radial.csv and RadialNormalized.csv can be read into an array easily with numpy using np.loadtxt(path, delimiter=",")
	- Any of the CSV tables can be read in with pandas using pd.read_csv(path, index_col="ROI")

## Optional Analysis:

Currently there is only 1 downstream analysis procedure implemented, though it wouldn't be exceptionally difficuly to expand in the future. Currently, a variation of the RAMP protocol as described in [Guardia et al. 2019](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3000279#sec002) is implemented with the following steps:

1. Given the Radial Profile plot distribution calculated for each ROI, normalize the distances (X-Values) using the largest circle present. This effectively normalizes all distance values to be between 0 and 1.
2. Define a fraction f (0.00 < f <= 1.00). The analysis procedure finds the minimum radius size that incorporates fraction f of the total itensity.
3. 