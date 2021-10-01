# 1. Table of Contents
- [1. Table of Contents](#1-table-of-contents)
- [2. Tile Sampling Annotation](#2-fibrosis-annotation)
  - [2.1. Installation](#21-installation)
- [3. Support](#3-support)
- [4. Contributing](#4-contributing)
- [5. Authors and Acknowledgements](#5-authors-and-acknowledgements)

# 2. Fibrosis Annotation

The Fibrosis Annotation Tool is a markup application used in conjunction with svs files to  
trace and categorize fibrotic material, in addition to calculating their respective areas.
**Features**
- SQLite database of data storage
- Live updating graphs to keep track of data
- Fast and easy keybindings for tracing and marking
- Conversion to coordinates of the whole image file
- Randomized image tiling

## 2.1. Installation

- clone the github repository in your local system `git clone https://github.com/mjneel/pathology_clients/tree/master/fibrosis`
- move into the tile_sampling repository
- install all the libraries mentioned in [requirements.txt] using `pip install -r requirements.txt`
- Download the Windows openslide binaries from Openslide Website (https://openslide.org/download/). Download the 2017-11-22 version.
- Extract this folder, open this folder, and copy the path to the bin folder (should end with:  \openslide-win64\bin)
- Add this path to the PATH System Variable
- run the main python file `python app.py`

# 3. Support

If you find any bugs please open an issue [here](https://github.com/mjneel/pathology_clients/issues/new) by including information about the bug and how to reproduce it. Be sure to specify that this is for the fibrosis client

# 5. Authors and Acknowledgements

Development on the Tile Sampling Annotation Tool by TheSamG and whuang37.