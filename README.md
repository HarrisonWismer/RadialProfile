# RadialProfile Script

Radial Profiling of User-Defined ROIs Using Napari

## Usage:

Currently this script is run through the command line and must have several arguments provided to it. The script was designed around reading in a .LIF file containing 1
or more scenes which can each be a Z-Stack.

Arguments that must be provided are:

-i (--input) -> The Input File Path

-o (--output) -> The Output File Path (Optional. If no path specified by user, the program will write all files to the current working directory.)

-c (--channels) -> The channel names. The user should know before hand the number of channels and the order of channels.

-s (--specifiedChannel) -> The channel used to measure intensity values as part of the Radial Profiling procedure. 
Specified channels must be one of the channels specified by the user.

An example program call is:

python RadialProfile.py -i ./Desktop/rpExample.lif -o ./Desktop/rpResults -c nucleus membrane mitochondria -s mitochondria

## Interaction:
Upon successfully running the program, a Napari Viewer with the first scene contained in the .LIF file should appear.

The general workflow is as follows:

1. Navigate to the desired Z-Plane

2. User whatever channel is needed to:
	A) Draw an ROI Using the shapes layer named "ROIs" which can be found on the left. The polygon selection function will be the most accurate.
	B) Draw a Center Point using the points layer named "Centers" which can be found on the left. Place this where you want the center of the Radial Profile circle to be.
	   Note that this center point does not need to be placed in the center of the ROI defined.
	###### IMPORTANT: ROI

3.Repeat step 2 for all desired ROI's.  




## Output: