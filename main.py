import numpy as np
from matplotlib import pyplot as plt
import utils
import AWR1843 as awr
from PIL import Image
import copy
import sys

# Import files for sound tone
import pygame

pygame.init()
from Note import Note
from Track import Track

# Set the BPM
BPM = 360
beat = 60 / BPM

# Set the tone for the sound
notes = [Note.rest(beat), Note("c5", beat), Note("e5", beat), Note("g5", beat)]


track = Track(notes)
track.play()


# Configuration file name
configFileName = "Radar_config_v3.cfg"

# Configure serial ports
CLIport = {}
Dataport = {}
CLIport, Dataport = awr.serialConfig(configFileName)

# Parse radar configuration parameters
configParameters = awr.parseConfigFile(
    configFileName=configFileName, numRxAnt=1, numTxAnt=1
)
file = open(configFileName).read().splitlines()
first_FovCfg = True
for i in file:
    if i.startswith("aoaFovCfg"):
        _, _, thetamin, thetamax, _, _ = i.split(" ")
        thetamax = float(thetamax)
        thetamin = float(thetamin)
    if i.startswith("cfarFovCfg") and first_FovCfg:
        first_FovCfg = False
        _, _, _, _, maxdistance = i.split(" ")
        maxdistance = float(maxdistance)

# Calculate the number of levels for the polar plot
n_levels = 4
if n_levels < 3:
    raise ValueError("n_levels should be greater than 3")

# Define colors for different levels
colors = ["red", "orange"]
for i in range(n_levels - 2):
    colors.append("green")

# Calculate height and width for each level and sector
height = maxdistance / n_levels
width = utils.deg_to_rad((thetamax - thetamin) / 3)

# Calculate radial distances for each level
r_distances = [i * height for i in range(0, n_levels + 1)]

# Create polar plot
fig = plt.figure()


img = Image.open("Tesla_Car_Crop_2.jpg")
img = np.array(img)
img_height, img_width, img_depth = img.shape
ax2 = fig.add_subplot(212, polar=False)
ax2.imshow(img)
ax2.axis("off")

ax = fig.add_subplot(projection="polar")
theta_grids = [
    thetamin,
    (thetamax - thetamin) / 3 + thetamin,
    thetamax - (thetamax - thetamin) / 3,
    thetamax,
]
ax.set_thetagrids(theta_grids)
ax.set_rorigin(-0.5)
ax.set_theta_zero_location("N")
ax.set_thetamin(thetamin)
ax.set_thetamax(thetamax)

text_box = ax.text(
    0, 2.2, "Distance: --.-- m", fontsize=13, horizontalalignment="center"
)

# Calculate sector centers
centers = [
    (theta_grids[1] - theta_grids[0]) / 2 + theta_grids[0],
    (theta_grids[2] - theta_grids[1]) / 2 + theta_grids[1],
    (theta_grids[3] - theta_grids[2]) / 2 + theta_grids[2],
]
centers = [utils.deg_to_rad(x) for x in centers]

x1 = x2 = x3 = None
first_time = True
remove_point = 0
previous_positions = [-1, -1, -1]

# Function to update the plot with new data
def update():
    dataOk = 0
    global detObj, first_time, x1, x2, x3, remove_point, previous_positions, text_box
    x = []
    y = []
    graphical_flag = False

    # Read and parse the received data
    dataOk, frameNumber, detObj = awr.readAndParseData18xx_2d(
        Dataport, configParameters
    )
    if dataOk and len(detObj["x"]) > 0:
        x = detObj["x"]
        y = detObj["y"]
        x = [round(i, 6) for i in x]
        y = [round(i, 6) for i in y]

        # Remove previous plot elements
        if x1 is not None:
            x1.remove()
        if x2 is not None:
            x2.remove()
        if x3 is not None:
            x3.remove()
        x1 = x2 = x3 = None

        # Convert object positions to polar coordinates and plot
        positions = list(zip(x, y))
        positions_np = np.array(positions)
        r_np, theta_np = utils.position_to_polar(
            x=positions_np[:, 0], y=positions_np[:, 1]
        )
        r_np -= 0.1
        r_np = [r_i + 0.01 for r_i in r_np if r_i > 0]
        graphical_positions = [-1, -1, -1]
        for pos in positions:
            r, theta = utils.position_to_polar(x=pos[0], y=pos[1])
            r -= 0.1
            if r < 0:
                continue
            r += 0.01
            theta = theta - np.pi / 2
            theta = utils.rad_to_deg(theta)
            for i in range(3):
                if theta >= theta_grids[i] and theta <= theta_grids[i + 1]:
                    for j in range(n_levels):
                        if r >= r_distances[j] and r <= r_distances[j + 1]:
                            if (
                                graphical_positions[i] != -1
                                and j < graphical_positions[i]
                            ) or graphical_positions[i] == -1:
                                graphical_positions[i] = j
        if graphical_positions == [-1, -1, -1]:
            track.note(0)
            text_box.set_text("Distance: --.-- m")
        else:
            if (
                graphical_positions[0] != -1
                and graphical_positions[0] == previous_positions[0]
            ):
                graphical_flag = True
                pos = graphical_positions[0]
                x1 = ax.bar(
                    x=centers[0],
                    height=height,
                    width=width,
                    bottom=r_distances[pos],
                    color=colors[pos],
                )
            elif previous_positions[0] != -1:
                graphical_flag = True
                pos = previous_positions[0]
                x1 = ax.bar(
                    x=centers[0],
                    height=height,
                    width=width,
                    bottom=r_distances[pos],
                    color=colors[pos],
                )
            if (
                graphical_positions[1] != -1
                and graphical_positions[1] == previous_positions[1]
            ):
                graphical_flag = True
                pos = graphical_positions[1]
                x2 = ax.bar(
                    x=centers[1],
                    height=height,
                    width=width,
                    bottom=r_distances[pos],
                    color=colors[pos],
                )
            elif previous_positions[1] != -1:
                graphical_flag = True
                pos = previous_positions[1]
                x2 = ax.bar(
                    x=centers[1],
                    height=height,
                    width=width,
                    bottom=r_distances[pos],
                    color=colors[pos],
                )
            if (
                graphical_positions[2] != -1
                and graphical_positions[2] == previous_positions[2]
            ):
                graphical_flag = True
                pos = graphical_positions[2]
                x3 = ax.bar(
                    x=centers[2],
                    height=height,
                    width=width,
                    bottom=r_distances[pos],
                    color=colors[pos],
                )
            elif previous_positions[2] != -1:
                graphical_flag = True
                pos = previous_positions[2]
                x3 = ax.bar(
                    x=centers[2],
                    height=height,
                    width=width,
                    bottom=r_distances[pos],
                    color=colors[pos],
                )
            if graphical_flag:
                min_r_np = np.min(r_np)
                text_box.set_text("Distance: %0.02f m" % min_r_np)
            else:
                text_box.set_text("Distance: --.-- m")

            previous_positions = [x for x in previous_positions if x != -1]
            if previous_positions != []:
                closest = min(previous_positions)
                if closest == 3 or closest == 2:
                    track.note(1)
                elif closest == 1:
                    track.note(2)
                else:
                    track.note(3)
        previous_positions = copy.copy(graphical_positions)
        ax.set_rticks(r_distances)
        ax.set_rmax(maxdistance)


# Main loop to continuously update the plot
detObj = {}
while True:
    try:
        update()
        plt.pause(0.05)

    # Stop the program and close everything if Ctrl + c is pressed or if anything goes wrong
    except KeyboardInterrupt or Exception:
        CLIport.write(("sensorStop\n").encode())
        CLIport.close()
        Dataport.close()
        track.stop()
        pygame.quit()
        sys.exit()
