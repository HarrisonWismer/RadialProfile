# RadialProfile Script

Radial Profiling of User-Defined ROIs Using Napari

## Usage:

Currently this script is run through the command line and must have several arguments provided to it. The script was designed around reading in a .LIF file containing 1
or more scenes which can each be a Z-Stack.

Arguments that must be provided are:
-i --input -> The Input File Path
-o --output -> The Output File Path (Optional. If no path specified by user, the program will write all files to the current working directory.)
-c --channels -> The channel names. The user should know before hand the number of channels and the order of channels.
-s --specifiedChannel -> The channel used to measure intensity values as part of the Radial Profiling procedure. Specified channels must be one of the channels specified by the user.