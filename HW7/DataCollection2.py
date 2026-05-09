# ENME489Y: Remote Sensing

# import the necessary packages
import numpy as np
import time
import cv2
import os
import shutil
import subprocess

# allow the camera to setup
time.sleep(1)

# Base directory = folder where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALIGNMENT_DIR = os.path.join(BASE_DIR, "second_alignment_images")

# Create alignment_images folder if it does not already exist
os.makedirs(ALIGNMENT_DIR, exist_ok=True)

# Enter the initial IMU angle from user
d = input("Please enter IMU angle: ")
print("Confirming the IMU angle you entered is: ")
print(d)

# The following line should be used if interested in
# the -ss ("shutter speed") command for long exposure
# Old command:
# command = 'raspistill -w 1280 -h 720 -ss 1000000 -o blank.jpg'
# command = 'raspistill -w 1280 -h 720 -o blank.jpg'

blank_path = os.path.join(BASE_DIR, "blank.jpg")

# Use the camera command available on this Raspberry Pi OS
if shutil.which("rpicam-still"):
    command = f"rpicam-still --width 1280 --height 720 -o {blank_path}"
elif shutil.which("libcamera-still"):
    command = f"libcamera-still --width 1280 --height 720 -o {blank_path}"
elif shutil.which("raspistill"):
    command = f"raspistill -w 1280 -h 720 -o {blank_path}"
else:
    raise RuntimeError("No supported camera command found: rpicam-still, libcamera-still, or raspistill.")

subprocess.run(command, shell=True, check=True)

image = cv2.imread(blank_path)

if image is None:
    raise RuntimeError("Could not read blank.jpg. Camera capture may have failed.")

image = cv2.flip(image, -1)

# plot crosshairs for alignment
cv2.line(image, (640, 0), (640, 720), (0, 150, 150), 1)
cv2.line(image, (600, 360), (1280, 360), (0, 150, 150), 1)

# display IMU angle, for reference
#font = cv2.FONT_HERSHEY_COMPLEX_SMALL
#red = (0, 0, 255)
#cv2.putText(image, d, (800, 200), font, 10, red, 10)

# write image to file
d = int(d)
filename = "%d.jpg" % d
output_path = os.path.join(ALIGNMENT_DIR, filename)

cv2.imwrite(output_path, image)

print("Saved alignment image to:")
print(output_path)

print("All done!")
