# ENME 489Y: Remote Sensing
# Assignment 6: Line laser lidar alignment calibration

import numpy as np
import cv2
import glob
import re
import os
import matplotlib.pyplot as plt

print("All packages imported properly!")

# Find all calibration images
files = glob.glob("improved_alignment_images/*.jpg")
print(files)

# HSV bounds for red laser
# Tune these using colorpicker.py if needed
colorLower = (164, 114, 26)
colorUpper = (179, 255, 255)

# Image width
image_width = 1280

# Arrays for measured data
x_plot = []
y_plot = []

# Clear old laserlog file before writing new data
with open("laserlog.txt", "w") as f:
    f.write("distance_inches calibration_pixel raw_pixel\n")

for file in files:
    print("\nProcessing:", file)

    # Get distance from filename only
    # Example: alignment_images/36.jpg -> 36
    filename = os.path.basename(file)
    distance_match = re.findall(r"\d+", filename)

    if len(distance_match) == 0:
        print("No distance found in filename, skipping.")
        continue

    distance = int(distance_match[0])
    print("Distance:", distance)

    image = cv2.imread(file)

    if image is None:
        print("Could not read image, skipping.")
        continue

    # Blur and convert to HSV
    blurred = cv2.GaussianBlur(image, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Mask red laser
    mask = cv2.inRange(hsv, colorLower, colorUpper)

    # Center row of image
    y = 360
    row = mask[y, :]

    # Find laser pixels along row
    laser_pixels = []

    for i in range(len(row)):
        if row[i] > 200:
            laser_pixels.append(i)

    if len(laser_pixels) > 0:
        raw_pixel = int(np.average(laser_pixels))
    else:
        print("No laser detected, skipping.")
        continue

    # Mirror raw pixel so graph matches assignment example orientation
    calibration_pixel = image_width - raw_pixel

    print("Raw pixel:", raw_pixel)
    print("Calibration pixel:", calibration_pixel)

    # Save to log
    with open("laserlog.txt", "a") as f:
        f.write(f"{distance} {calibration_pixel} {raw_pixel}\n")

    x_plot.append(calibration_pixel)
    y_plot.append(distance)

    # Optional display for checking
    cv2.line(mask, (0, y), (1280, y), 255, 2)
    cv2.circle(mask, (raw_pixel, y), 20, 255, 2)

# Convert lists to arrays
x_plot = np.array(x_plot)
y_plot = np.array(y_plot)

if len(x_plot) == 0:
    print("No valid laser points were detected.")
    exit()

# Sort by distance
order = np.argsort(y_plot)
x_plot = x_plot[order]
y_plot = y_plot[order]

# ---------------- Calibration model ----------------

# Radian offset
ro = 0.41

# Radians per pixel
rpc = -0.00068

# Pixel values
pfc = np.arange(1, 640, 2)

# Separation distance between laser and camera axes
# 12 inches = 0.3048 meters
H = 0.3048

# Theoretical distance in meters
D_meters = H / np.tan(pfc * rpc + ro)

# Convert meters to inches
D_inches = D_meters * 39.37

# Remove bad/negative values
valid = (D_inches > 0) & (D_inches < 200)

pfc_valid = pfc[valid]
D_valid = D_inches[valid]

# Plot
plt.figure()
plt.plot(x_plot, y_plot, "ro", label="Measured data")
plt.plot(pfc_valid, D_valid, "b-", linewidth=3, label="Theoretical model")

plt.title("Lidar Calibration Curve")
plt.xlabel("Pixel")
plt.ylabel("Distance to Target (inches)")
plt.axis([0, 640, 0, 120])
plt.grid(True)
plt.legend()
plt.show()