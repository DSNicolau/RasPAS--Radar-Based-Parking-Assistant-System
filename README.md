# RasPAS: Radar-Based Parking Assistant System

## Overview

This project implements a graphical interface for a radar-based parking assistant system, displaying radar data in real-time into regions and playing sounds based on the distance to the detected objects. It is developed as part of the Radio Systems course at the Polytechnic Institute of Leiria, Portugal, under the guidance of Professor Rafael Caldeirinha.

## Contributors

- Daniel Nicolau
- Nicolas Vasconcellos

## Repository Contents

- **AWR1843.py**: A compilation of functions from the [AWR1843-Read-Data-Python-MMWAVE-SDK-3](https://github.com/ibaiGorordo/AWR1843-Read-Data-Python-MMWAVE-SDK-3-) repository with slight modifications to account for deprecated packages.
- **frequency_map.json**: A lookup table of musical notes to their respective frequencies, sourced from [music_maker](https://github.com/JamminCoder/music_maker).
- **main.py**: The main script that creates a graphical interface using a polar bar plot, receives data points from an AWR1843 radar, clusters them into regions for the plot, and plays sound based on the distance to the object.
- **Note.py**: A class representing a musical note, also from [music_maker](https://github.com/JamminCoder/music_maker).
- **Radar_config_vx.cfg**: Three radar configurations developed, with v3 being the final calibrated one for the specific scenario.
- **Tesla_Car_Crop_2.jpg**: A figure of the rear of a car used for integration into the graphical interface.
- **Tone.py**: A class to generate and play notes, also from [music_maker](https://github.com/JamminCoder/music_maker).
- **Track.py**: A class to manage to play a sequence of notes in a different thread, allowing the code to continue running while notes are played, also from [music_maker](https://github.com/JamminCoder/music_maker).
- **utils_notes.py**: Several functions for parsing and file reading to play notes correctly, also from [music_maker](https://github.com/JamminCoder/music_maker).
- **utils.py**: Functions developed for conversion between polar and Cartesian coordinates and radian to degrees.

## Dependencies

- [pygame](https://pypi.org/project/pygame/)
- [numpy](https://pypi.org/project/numpy/)
- [matplotlib](https://pypi.org/project/matplotlib/)

## Usage

To run the code, please run the `main.py` file. The graphical interface is already set up to accommodate different `.cfg` files, where the azimuth angle and distance are variable. If more radial resolution is needed or preferable, only the variable `n_levels` needs to be changed to the desired value.
