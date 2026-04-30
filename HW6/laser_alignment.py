# ENME 435 / ENME489Y: Remote Sensing
# Assignment 6: Line laser lidar calibration
#
# Improved version for:
# - Picamera/right-side laser setup
# - saved images with red text in the top region
# - mirrored pixel coordinate so graph matches assignment example

import numpy as np
import cv2
import glob
import re
import os
import matplotlib.pyplot as plt


print("All packages imported properly!")


# --------------------------------------------------
# Settings
# --------------------------------------------------

IMAGE_CENTER_X = 640

# Ignore the top region because the red distance number is saved there
Y_IGNORE_TOP = 260

# Search only the right half of the image because your laser appears on the right
X_SEARCH_START = IMAGE_CENTER_X
X_SEARCH_END = 1280

# HSV red threshold
# Looser values because your images have red/pink background shading
lower_red_1 = (0, 50, 45)
upper_red_1 = (20, 255, 255)

lower_red_2 = (155, 50, 45)
upper_red_2 = (179, 255, 255)

# Red dominance threshold
# Rejects weak pink/red background by requiring red to be stronger than blue/green
MIN_RED_VALUE = 50
MIN_RED_EXCESS = 5

# Connected component filtering
MIN_COMPONENT_AREA = 3
MIN_COMPONENT_HEIGHT = 2

# Expected physical trend:
# closer wall -> laser farther right in raw image
# farther wall -> laser moves closer to center
#
# After mirroring:
# closer wall -> smaller calibration_pixel
# farther wall -> larger calibration_pixel
MAX_LEFT_JUMP_RAW = 30

# Baseline distance between camera and laser axes, inches
# Update this if your measured camera-laser separation is different
H_inches = 12.0


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def get_distance_from_filename(file):
    filename = os.path.basename(file)
    distance_match = re.findall(r"\d+", filename)

    if len(distance_match) == 0:
        return None

    return int(distance_match[0])


def build_laser_mask(image):
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Red wraps around HSV hue, so use two masks
    mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
    mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
    hsv_mask = cv2.bitwise_or(mask1, mask2)

    # Red channel dominance check
    b, g, r = cv2.split(blurred)

    red_excess = r.astype(np.int16) - np.maximum(
        g.astype(np.int16),
        b.astype(np.int16)
    )

    dominance_mask = np.zeros_like(hsv_mask)
    dominance_mask[(r > MIN_RED_VALUE) & (red_excess > MIN_RED_EXCESS)] = 255

    # Final mask must pass HSV red and red-channel dominance
    mask = cv2.bitwise_and(hsv_mask, dominance_mask)

    # Remove red text at the top
    mask[:Y_IGNORE_TOP, :] = 0

    # Remove left half, since your laser is on the right side
    mask[:, :X_SEARCH_START] = 0

    # Remove anything beyond image width/search region
    mask[:, X_SEARCH_END:] = 0

    # Connect weak vertical laser pixels
    vertical_kernel = np.ones((9, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, vertical_kernel)

    # Light cleanup
    small_kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, small_kernel)

    return mask


def find_laser_candidates(mask):
    """
    Finds connected red components in the right-side search region.
    Returns candidate dictionaries sorted by score.
    """

    roi = mask[Y_IGNORE_TOP:, X_SEARCH_START:X_SEARCH_END]

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        roi,
        connectivity=8
    )

    candidates = []

    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        cx, cy = centroids[label]

        if area < MIN_COMPONENT_AREA:
            continue

        if h < MIN_COMPONENT_HEIGHT:
            continue

        raw_pixel = int(cx + X_SEARCH_START)
        raw_y = int(cy + Y_IGNORE_TOP)
        pixel_from_center = raw_pixel - IMAGE_CENTER_X

        if pixel_from_center <= 0:
            continue

        component_mask = (labels == label).astype(np.uint8)
        column_count = np.sum(component_mask > 0, axis=0)
        peak_score = int(np.max(column_count))

        # Score favors stronger/taller line-like red features
        score = area + 2 * h + peak_score

        candidates.append({
            "raw_pixel": raw_pixel,
            "raw_y": raw_y,
            "pixel_from_center": pixel_from_center,
            "area": int(area),
            "width": int(w),
            "height": int(h),
            "peak_score": peak_score,
            "score": float(score)
        })

    candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)

    return candidates


def choose_candidate(candidates, previous_raw_pixel):
    """
    Choose the physically reasonable candidate.

    In your setup:
    - close distance should be farther right in raw pixels
    - farther distance should move left toward the center

    So as distance increases, raw_pixel should generally decrease.
    """

    if len(candidates) == 0:
        return None

    # First image, usually the closest distance.
    # Choose the strongest/rightmost candidate.
    if previous_raw_pixel is None:
        candidates_by_right = sorted(
            candidates,
            key=lambda c: (c["raw_pixel"], c["score"]),
            reverse=True
        )
        return candidates_by_right[0]

    physically_valid = []

    for c in candidates:
        # Allow small noise, but reject candidates that jump far right again
        if c["raw_pixel"] <= previous_raw_pixel + MAX_LEFT_JUMP_RAW:
            physically_valid.append(c)

    if len(physically_valid) > 0:
        physically_valid = sorted(
            physically_valid,
            key=lambda c: c["score"],
            reverse=True
        )
        return physically_valid[0]

    return None


# --------------------------------------------------
# Find and sort calibration images
# --------------------------------------------------

files = glob.glob("improved_alignment_images/*.jpg")

file_distance_pairs = []

for file in files:
    distance = get_distance_from_filename(file)

    if distance is not None:
        file_distance_pairs.append((distance, file))

file_distance_pairs = sorted(file_distance_pairs, key=lambda x: x[0])

print("Files found in sorted order:")
for distance, file in file_distance_pairs:
    print(distance, file)

if len(file_distance_pairs) == 0:
    print("No valid .jpg files found in alignment_images/")
    print("Make sure your structure is:")
    print("  current_folder/")
    print("    laser_alignment.py")
    print("    alignment_images/")
    print("      24.jpg")
    print("      30.jpg")
    print("      ...")
    exit()


# --------------------------------------------------
# Process images
# --------------------------------------------------

x_plot = []
y_plot = []

previous_raw_pixel = None

os.makedirs("debug_detection", exist_ok=True)

with open("laserlog.txt", "w") as f:
    f.write(
        "distance_inches calibration_pixel raw_pixel "
        "pixel_from_center raw_y area width height peak_score score\n"
    )

for distance, file in file_distance_pairs:
    print("\nProcessing:", file)
    print("Distance:", distance)

    image = cv2.imread(file)

    if image is None:
        print("Could not read image, skipping.")
        continue

    height, width = image.shape[:2]

    mask = build_laser_mask(image)
    candidates = find_laser_candidates(mask)

    print("Candidates found:", len(candidates))

    for i, c in enumerate(candidates[:5]):
        print(
            f"  Candidate {i}: "
            f"raw_x={c['raw_pixel']}, "
            f"pfc={c['pixel_from_center']}, "
            f"raw_y={c['raw_y']}, "
            f"area={c['area']}, "
            f"h={c['height']}, "
            f"peak={c['peak_score']}, "
            f"score={c['score']}"
        )

    chosen = choose_candidate(candidates, previous_raw_pixel)

    if chosen is None:
        print("No physically valid laser candidate detected, skipping.")

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

        debug_path = f"debug_detection/{distance}_failed.jpg"
        mask_path = f"debug_detection/{distance}_mask_failed.jpg"

        cv2.imwrite(debug_path, debug_image)
        cv2.imwrite(mask_path, mask)

        continue

    raw_pixel = chosen["raw_pixel"]
    raw_y = chosen["raw_y"]
    pixel_from_center = chosen["pixel_from_center"]

    # --------------------------------------------------
    # Assignment-style pixel coordinate
    # --------------------------------------------------
    # The assignment graph uses pixel coordinate, not pixel-from-center.
    # Since your laser starts on the right, mirror the x-coordinate so
    # your graph follows the same orientation as the assignment example.
    calibration_pixel = width - raw_pixel

    print("Chosen raw pixel:", raw_pixel)
    print("Mirrored calibration pixel:", calibration_pixel)
    print("Pixel from center:", pixel_from_center)
    print("Detected laser y:", raw_y)

    with open("laserlog.txt", "a") as f:
        f.write(
            f"{distance} "
            f"{calibration_pixel} "
            f"{raw_pixel} "
            f"{pixel_from_center} "
            f"{raw_y} "
            f"{chosen['area']} "
            f"{chosen['width']} "
            f"{chosen['height']} "
            f"{chosen['peak_score']} "
            f"{chosen['score']}\n"
        )

    x_plot.append(calibration_pixel)
    y_plot.append(distance)

    previous_raw_pixel = raw_pixel

    # --------------------------------------------------
    # Debug image output
    # --------------------------------------------------

    debug_image = image.copy()

    # Ignored text area
    cv2.rectangle(
        debug_image,
        (0, 0),
        (width, Y_IGNORE_TOP),
        (80, 80, 80),
        2
    )

    # Centerline
    cv2.line(
        debug_image,
        (IMAGE_CENTER_X, 0),
        (IMAGE_CENTER_X, height),
        (0, 255, 255),
        2
    )

    # Detected raw laser column
    cv2.line(
        debug_image,
        (raw_pixel, Y_IGNORE_TOP),
        (raw_pixel, height),
        (0, 255, 0),
        2
    )

    cv2.circle(
        debug_image,
        (raw_pixel, raw_y),
        15,
        (0, 255, 0),
        2
    )

    cv2.putText(
        debug_image,
        f"raw={raw_pixel}, cal={calibration_pixel}",
        (30, height - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        2
    )

    debug_path = f"debug_detection/{distance}_detected.jpg"
    mask_path = f"debug_detection/{distance}_mask.jpg"

    cv2.imwrite(debug_path, debug_image)
    cv2.imwrite(mask_path, mask)


# --------------------------------------------------
# Convert and validate data
# --------------------------------------------------

x_plot = np.array(x_plot)
y_plot = np.array(y_plot)

if len(x_plot) == 0:
    print("No valid laser points were detected.")
    exit()

print("\nAccepted calibration points:")
for y, x in zip(y_plot, x_plot):
    print(f"Distance: {y} in, Calibration pixel: {x}")

if len(x_plot) < 3:
    print("Not enough points for calibration.")
    exit()


# --------------------------------------------------
# Fit calibration model
# --------------------------------------------------

# Model:
# D = H / tan(pixel * rpc + ro)
#
# Rearranged:
# atan(H / D) = pixel * rpc + ro

theta = np.arctan(H_inches / y_plot)

rpc, ro = np.polyfit(x_plot, theta, 1)

print("\nEstimated calibration constants:")
print("rpc =", rpc)
print("ro  =", ro)


# --------------------------------------------------
# Generate theoretical/fitted curve
# --------------------------------------------------

pixel_values = np.arange(1, width, 1)

D_inches = H_inches / np.tan(pixel_values * rpc + ro)

valid = (D_inches > 0) & (D_inches < 200)

pixel_valid = pixel_values[valid]
D_valid = D_inches[valid]


# --------------------------------------------------
# Plot
# --------------------------------------------------

plt.figure()
plt.plot(x_plot, y_plot, "ro", label="Measured data")
plt.plot(pixel_valid, D_valid, "b-", linewidth=3, label="Fitted theoretical model")

plt.title("Lidar Calibration Curve")
plt.xlabel("Pixel")
plt.ylabel("Distance to Target (inches)")
plt.axis([0, 640, 0, 120])
plt.grid(True)
plt.legend()
plt.show()
