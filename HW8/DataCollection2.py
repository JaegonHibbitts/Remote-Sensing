# ENME489Y: Remote Sensing

import time
import cv2
import os
from picamera2 import Picamera2

time.sleep(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALIGNMENT_DIR = os.path.join(BASE_DIR, "right_alignment_images")
os.makedirs(ALIGNMENT_DIR, exist_ok=True)

d = input("Please enter IMU angle: ")
print("Confirming the IMU angle you entered is:")
print(d)

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

picam2 = Picamera2()

config = picam2.create_still_configuration(
    main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "RGB888"}
)

picam2.configure(config)
picam2.start()

time.sleep(1)

image = picam2.capture_array()

# Convert RGB from Picamera2 to BGR for OpenCV
image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# Use the SAME flip as HW6 calibration
image = cv2.flip(image, -1)

# Plot crosshairs for alignment
cv2.line(image, (640, 0), (640, 720), (0, 150, 150), 1)
cv2.line(image, (600, 360), (1280, 360), (0, 150, 150), 1)

d = int(d)
filename = "%d.jpg" % d
output_path = os.path.join(ALIGNMENT_DIR, filename)

cv2.imwrite(output_path, image)

print("Saved alignment image to:")
print(output_path)

picam2.stop()

print("All done!")
