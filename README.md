# Plot-Bot
Desktop application to load in .csv, .txt, and .xlsx files and create a multitude of interactive plots. Uses the PyQt5 backend and Plotly for generating plots. Plot types include Time-Series, X-Y, 3D Scatter, Histograms/Bar Chart, Pair Plots

## Functionality
### Files
Text files with delimination and Excel workbook files can be imported. The import method can be configured depending on the file and a file import method must be selected whenever loading a file.

Multiple files can be imported and they are simply concatenated. This is very useful for time-series data taken over multiple files.

### Math
There are several built in unit conversions that can be created. There is also the capability to add custom math channels.

### Data
The data stored in the application can be exported to a CSV file. This is extremely useful for concatenated files or data with custom math channels or unit conversions.

### Profiles
If the same plots are going to be created often, the chart settings can be saved in a profile and loaded later. This is very useful.

### Saving Charts
Charts can be saved via the toolbar included with Plotly. Otherwise, the chart html can be exported and svaed for later viewing with interactivity.

## Repository Setup
Run the following sets of commands from inside the Plot-Bot repository:

### Linux/Mac
`python3 -m venv .venv`
`source .venv/bin/activate`
`pip3 install -r venv_pkg.txt`

### Windows
`python -m venv .venv`
`source .venv/bin/activate`
`pip install -r venv_pkg.txt`

## Configuration
There is a config file that can be changed based on user preferences and operating system. Currently *Plot_Bot.config* is setup for Linux and installing folders into the Home directory. Windows users will need to change this to their preferred locations.

## Detailed Usage
See User Manual under Documentation for more info.