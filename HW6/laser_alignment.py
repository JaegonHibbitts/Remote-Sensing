# ENME 489Y: Remote Sensing
# Assignment 5: Line laser lidar alignment calibration

import numpy as np
import cv2
import glob
import re
import os
import matplotlib.pyplot as plt

print("All packages imported properly!")

# --------------------------------------------------
# Find all calibration images
# --------------------------------------------------

files = glob.glob("alignment_images/*.jpg")
print("Files found:")
print(files)

if len(files) == 0:
    print("No .jpg files found in alignment_images/")
    exit()

# --------------------------------------------------
# Detection settings
# --------------------------------------------------

# Your images are 1280 x 720
IMAGE_CENTER_X = 640

# Ignore the top of the image because the red distance text is there
Y_IGNORE_TOP = 260

# Search only the right half because laser should be from center to right
X_SEARCH_START = IMAGE_CENTER_X
X_SEARCH_END = 1280

# Optional: ignore extreme right edge if there are border artifacts
# Keep 1280 unless needed
# X_SEARCH_END = 1220

# HSV red threshold
lower_red_1 = (0, 70, 60)
upper_red_1 = (20, 255, 255)

lower_red_2 = (155, 70, 60)
upper_red_2 = (179, 255, 255)

# Red dominance thresholds
MIN_RED_VALUE = 70
MIN_RED_EXCESS = 10

# Minimum number of red pixels in a column to count as a line
MIN_COLUMN_PIXELS = 5

# Number of neighboring columns to average around detected peak
PEAK_WINDOW = 5

# --------------------------------------------------
# Data arrays
# --------------------------------------------------

x_plot = []
y_plot = []

with open("laserlog.txt", "w") as f:
    f.write("distance_inches pixel_from_center raw_pixel raw_y peak_score\n")

# --------------------------------------------------
# Process images
# --------------------------------------------------

for file in files:
    print("\nProcessing:", file)

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

    height, width = image.shape[:2]

    # --------------------------------------------------
    # Build red laser mask
    # --------------------------------------------------

    blurred = cv2.GaussianBlur(image, (7, 7), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
    mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
    hsv_mask = cv2.bitwise_or(mask1, mask2)

    b, g, r = cv2.split(blurred)

    red_excess = r.astype(np.int16) - np.maximum(
        g.astype(np.int16),
        b.astype(np.int16)
    )

    dominance_mask = np.zeros_like(hsv_mask)
    dominance_mask[(r > MIN_RED_VALUE) & (red_excess > MIN_RED_EXCESS)] = 255

    mask = cv2.bitwise_and(hsv_mask, dominance_mask)

    # --------------------------------------------------
    # Remove the top region containing red distance text
    # --------------------------------------------------

    mask[:Y_IGNORE_TOP, :] = 0

    # Optional: remove left side
    mask[:, :X_SEARCH_START] = 0

    # Optional: remove anything past search end
    mask[:, X_SEARCH_END:] = 0

    # Clean noise lightly
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # --------------------------------------------------
    # Detect laser by strongest vertical column
    # --------------------------------------------------

    roi = mask[Y_IGNORE_TOP:height, X_SEARCH_START:X_SEARCH_END]

    # Count laser pixels per x-column
    column_count = np.sum(roi > 0, axis=0)

    # Find best column
    peak_index = int(np.argmax(column_count))
    peak_score = int(column_count[peak_index])

    if peak_score < MIN_COLUMN_PIXELS:
        print("No strong laser column detected, skipping.")
        print("Peak score:", peak_score)

        cv2.imshow("Original", image)
        cv2.imshow("Mask", mask)
        cv2.waitKey(300)
        continue

    # Average around the local peak for sub-region stability
    left = max(0, peak_index - PEAK_WINDOW)
    right = min(len(column_count), peak_index + PEAK_WINDOW + 1)

    local_columns = np.arange(left, right)
    local_weights = column_count[left:right]

    if np.sum(local_weights) > 0:
        refined_index = int(np.average(local_columns, weights=local_weights))
    else:
        refined_index = peak_index

    raw_pixel = refined_index + X_SEARCH_START

    # Find average y location only for debugging
    ys, xs = np.where(roi[:, max(0, refined_index - PEAK_WINDOW):refined_index + PEAK_WINDOW + 1] > 0)

    if len(ys) > 0:
        raw_y = int(np.average(ys) + Y_IGNORE_TOP)
    else:
        raw_y = Y_IGNORE_TOP

    pixel_from_center = raw_pixel - IMAGE_CENTER_X

    print("Raw pixel:", raw_pixel)
    print("Pixel from center:", pixel_from_center)
    print("Detected laser y:", raw_y)
    print("Peak score:", peak_score)

    # Sanity check
    if pixel_from_center <= 0:
        print("Laser is not right of center, skipping.")
        continue

    with open("laserlog.txt", "a") as f:
        f.write(f"{distance} {pixel_from_center} {raw_pixel} {raw_y} {peak_score}\n")

    x_plot.append(pixel_from_center)
    y_plot.append(distance)

    # --------------------------------------------------
    # Debug display
    # --------------------------------------------------

    debug_image = image.copy()

    # Draw ignored top region
    cv2.rectangle(
        debug_image,
        (0, 0),
        (width, Y_IGNORE_TOP),
        (80, 80, 80),
        2
    )

    # Draw center line
    cv2.line(
        debug_image,
        (IMAGE_CENTER_X, 0),
        (IMAGE_CENTER_X, height),
        (0, 255, 255),
        2
    )

    # Draw detected laser column
    cv2.line(
        debug_image,
        (raw_pixel, Y_IGNORE_TOP),
        (raw_pixel, height),
        (0, 255, 0),
        2
    )

    cv2.circle(debug_image, (raw_pixel, raw_y), 15, (0, 255, 0), 2)

    cv2.imshow("Detection Debug", debug_image)
    cv2.imshow("Laser Mask", mask)

    key = cv2.waitKey(300) & 0xFF

    if key == ord("q"):
        print("Stopped by user.")
        break

cv2.destroyAllWindows()

# --------------------------------------------------
# Convert and sort data
# --------------------------------------------------

x_plot = np.array(x_plot)
y_plot = np.array(y_plot)

if len(x_plot) == 0:
    print("No valid laser points were detected.")
    exit()

order = np.argsort(y_plot)
x_plot = x_plot[order]
y_plot = y_plot[order]

print("\nRaw detected calibration points:")
for y, x in zip(y_plot, x_plot):
    print(f"Distance: {y} in, Pixel from center: {x}")

# --------------------------------------------------
# Monotonic sanity filter
# --------------------------------------------------
# Expected physics:
# As distance increases, pixel_from_center should generally decrease.
# This filter removes points that jump right as distance increases.

filtered_x = []
filtered_y = []

last_x = None

for y, x in zip(y_plot, x_plot):
    if last_x is None:
        filtered_x.append(x)
        filtered_y.append(y)
        last_x = x
    else:
        # Allow small noise, but reject large jumps to the right
        if x <= last_x + 8:
            filtered_x.append(x)
            filtered_y.append(y)
            last_x = x
        else:
            print(f"Rejecting nonphysical point: distance={y}, pfc={x}")

x_plot = np.array(filtered_x)
y_plot = np.array(filtered_y)

print("\nFiltered calibration points:")
for y, x in zip(y_plot, x_plot):
    print(f"Distance: {y} in, Pixel from center: {x}")

if len(x_plot) < 3:
    print("Not enough valid calibration points after filtering.")
    exit()

# --------------------------------------------------
# Fit calibration model
# --------------------------------------------------

# Baseline distance between laser and camera axes, inches
H_inches = 12.0

# Model:
# D = H / tan(pfc * rpc + ro)
#
# Rearranged:
# atan(H / D) = pfc * rpc + ro

theta = np.arctan(H_inches / y_plot)

rpc, ro = np.polyfit(x_plot, theta, 1)

print("\nEstimated calibration constants:")
print("rpc =", rpc)
print("ro  =", ro)

# Generate fitted model curve
pfc = np.arange(1, 640, 1)
D_inches = H_inches / np.tan(pfc * rpc + ro)

valid = (D_inches > 0) & (D_inches < 200)

pfc_valid = pfc[valid]
D_valid = D_inches[valid]

# --------------------------------------------------
# Plot
# --------------------------------------------------

plt.figure()
plt.plot(x_plot, y_plot, "ro", label="Filtered measured data")
plt.plot(pfc_valid, D_valid, "b-", linewidth=3, label="Fitted theoretical model")

plt.title("Lidar Calibration Curve")
plt.xlabel("Pixel from Center")
plt.ylabel("Distance to Target (inches)")
plt.axis([0, 640, 0, 120])
plt.grid(True)
plt.legend()
plt.show()