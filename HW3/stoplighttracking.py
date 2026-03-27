# ENME 489Y: Remote Sensing
# Python script tracks green 'stoplight'
# and optionally saves video of tracking to stoplight.mp4

from picamera2 import Picamera2
import numpy as np
import cv2
import time

# Define the lower and upper boundaries of the
# green circle in the HSV color space
# Note: use colorpicker.py to create a new HSV mask
colorLower = (29, 70, 6)
colorUpper = (75, 255, 255)

# Initialize the Raspberry Pi camera with OpenCV-friendly BGR output
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "BGR888"}
)
picam2.configure(config)
picam2.start()

# Allow the camera to warm up
time.sleep(0.2)

# Optional video writer
# Uncomment these two lines if you want to save MP4 video
# fourcc = cv2.VideoWriter_fourcc(*"mp4v")
# out = cv2.VideoWriter("stoplight.mp4", fourcc, 10, (640, 480))

try:
    while True:
        # Capture frame as a NumPy array in BGR format
        image = picam2.capture_array()

        # Blur the frame and convert to HSV color space
        blurred = cv2.GaussianBlur(image, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Construct a mask for the color green, then perform
        # erosions and dilations to remove small blobs
        mask = cv2.inRange(hsv, colorLower, colorUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Find contours in the mask
        contours_info = cv2.findContours(
            mask.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        cnts = contours_info[0] if len(contours_info) == 2 else contours_info[1]
        center = None

        # Proceed if at least one contour was found
        if len(cnts) > 0:
            # Find the largest contour
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)

            if M["m00"] != 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                if radius > 0:
                    # Draw the circle and centroid on the frame
                    cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                    cv2.circle(image, center, 2, (0, 0, 255), -1)

        # Optional video save
        # Uncomment this line if using VideoWriter above
        # out.write(image)

        # Show the frame
        cv2.imshow("Frame", image)
        key = cv2.waitKey(1) & 0xFF

        # Press 'q' to quit
        if key == ord("q"):
            break

finally:
    # Clean up
    # Uncomment if using video saving
    # out.release()
    picam2.stop()
    cv2.destroyAllWindows()