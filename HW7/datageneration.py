# ENME 489Y: Remote Sensing
# 3D point cloud generation from line laser lidar images

# Import packages
import numpy as np
import cv2
import glob
import re
import time
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

print("All packages imported properly!")

# --------------------------------------------------
# Red laser HSV bounds
# Tune these using colorpicker.py if needed
# --------------------------------------------------

colorLower = (164, 114, 26)
colorUpper = (179, 255, 255)

# --------------------------------------------------
# Initialize plot arrays
# --------------------------------------------------

x_plot = []
y_plot = []
a_plot = []
D_plot = []
IMU_plot = []
pcX = []
pcY = []
pcZ = []

# --------------------------------------------------
# Lidar calibration parameters
# Use your calibrated values here
# --------------------------------------------------

# These should match the values that made your blue curve fit the red points
ro = 0.55
rpc = -0.0010

# 12 inch separation distance, laser to camera, in meters
H = 0.3048

# Image size
image_width = 1280
image_height = 720

# --------------------------------------------------
# Raspberry Pi camera vertical field of view mapping
# --------------------------------------------------

ang = np.zeros((image_height), dtype=float)

for i in range(0, image_height):
    ang[i] = 0.000942479485 * (i - 360)

# --------------------------------------------------
# Find images
# --------------------------------------------------

files = glob.glob("testdataraymond/*.jpg")
print(files)

# --------------------------------------------------
# Output file
# --------------------------------------------------

f = open("testdataraymond/testresults.txt", "w")

millis = int(round(time.time() * 1000))

# --------------------------------------------------
# Process each image
# --------------------------------------------------

for file in files:
    print(file)

    # Pull pointing angle from filename only
    # Example: testdataraymond/45.jpg -> 45 degrees
    filename = os.path.basename(file)
    angle_match = re.findall(r"\d+", filename)

    if len(angle_match) == 0:
        print("No angle found in filename, skipping.")
        continue

    angle = int(angle_match[0])
    print("Angle:", angle)

    # Read in image
    image = cv2.imread(file)

    if image is None:
        print("Could not read image, skipping.")
        continue

    # --------------------------------------------------
    # IMPORTANT CHANGE FOR YOUR SETUP
    # Original script blacked out the right side:
    # image[0:720, 600:1280] = (0, 0, 0)
    #
    # Your laser is on the right side, so do NOT do that.
    # Instead, optionally ignore the left side.
    # --------------------------------------------------

    image[0:image_height, 0:640] = (0, 0, 0)

    # Blur and convert to HSV
    blurred = cv2.GaussianBlur(image, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Apply mask for red laser
    mask = cv2.inRange(hsv, colorLower, colorUpper)

    for a in range(0, image_height, 1):

        # Define image row of interest
        y = a

        # Row of mask
        row = mask[y]

        # Initialize array for averaging laser pixels
        spot = []

        # Identify laser returns
        for i in range(0, len(row)):
            if row[i] > 200:
                spot.append(i)

        # Average all row pixels identified as the red laser line
        if len(spot) > 1:
            raw_pixel = int(np.average(spot))
        else:
            raw_pixel = 0

        if raw_pixel >= 1:

            # --------------------------------------------------
            # IMPORTANT CHANGE FOR YOUR CALIBRATION
            # Your laser starts on the right, so we mirror the pixel.
            # This matches the calibration graph you created.
            # --------------------------------------------------

            calibration_pixel = image_width - raw_pixel

            # Calculate range based on calibrated geometry
            # D outputs range in feet
            D = 3.28084 * H / np.tan(calibration_pixel * rpc + ro)

            IMU_plot.append(angle)
            a_plot.append(a)
            D_plot.append(D)

            x_plot.append(D * np.sin(ang[a]))

            pcX.append(D * np.sin(ang[a]) * np.cos(np.deg2rad(angle)))
            pcY.append(D * np.cos(np.deg2rad(angle)))
            pcZ.append(D * np.sin(np.deg2rad(angle)))

            # Write x, y, z coordinates of each 3D point to file
            outstring = (
                str(D * np.sin(ang[a]) * np.cos(np.deg2rad(angle))) + " " +
                str(D * np.cos(np.deg2rad(angle))) + " " +
                str(D * np.sin(np.deg2rad(angle))) + "\n"
            )

            f.write(outstring)

        else:

            IMU_plot.append(angle)
            a_plot.append(a)
            D_plot.append(0)
            x_plot.append(0)
            pcX.append(0)
            pcY.append(0)
            pcZ.append(0)

            # Write empty point
            outstring = "0 0 0\n"
            f.write(outstring)

# Close the text file
f.close()

millis_1 = int(round(time.time() * 1000))

print(" ")
print("Time required to process all data:")
print(millis_1 - millis)

# --------------------------------------------------
# Plot data in 3D point cloud scatter plot
# --------------------------------------------------

fig = plt.figure(1)
ax = fig.add_subplot(111, projection="3d")
ax.scatter(pcX, pcY, pcZ, s=1)

ax.view_init(elev=110, azim=110)

ax.set_xlabel("X Label")
ax.set_ylabel("Y Label")
ax.set_zlabel("Z Label")

plt.xlim(-40, 40)
plt.ylim(20, 100)

plt.show()

print(" ")
print("finished...bye bye!")
