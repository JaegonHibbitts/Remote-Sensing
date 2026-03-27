# ENME 489Y: Remote Sensing
# Tracks green 'stoplight' and saves 45 seconds of tracking video

from picamera2 import Picamera2
import cv2
import time

# Define the lower and upper boundaries of the
# green circle in the HSV color space
colorLower = (29, 70, 6)
colorUpper = (75, 255, 255)

# Initialize the Raspberry Pi camera with OpenCV-friendly BGR output
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "BGR888"}
)
picam2.configure(config)
picam2.start()

# Allow camera to warm up
time.sleep(0.2)

# Video settings
frame_size = (640, 480)
fps = 20
duration_seconds = 45

# Create video writer
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter("stoplight_tracking.mp4", fourcc, fps, frame_size)

start_time = time.time()

try:
    while True:
        # Capture frame in BGR
        image = picam2.capture_array()

        # Blur and convert to HSV
        blurred = cv2.GaussianBlur(image, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Create green mask
        mask = cv2.inRange(hsv, colorLower, colorUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Find contours
        contours_info = cv2.findContours(
            mask.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        cnts = contours_info[0] if len(contours_info) == 2 else contours_info[1]

        # Track largest green object
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)

            if M["m00"] != 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                if radius > 0:
                    cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                    cv2.circle(image, center, 3, (0, 0, 255), -1)

        # Show live frame
        cv2.imshow("Frame", image)

        # Save tracked frame to video
        out.write(image)

        # Stop after 45 seconds
        elapsed = time.time() - start_time
        if elapsed >= duration_seconds:
            print("45 second video complete.")
            break

        # Allow manual quit with q
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("Recording stopped early.")
            break

finally:
    out.release()
    picam2.stop()
    cv2.destroyAllWindows()