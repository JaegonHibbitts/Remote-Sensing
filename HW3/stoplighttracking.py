# ENME 489Y: Remote Sensing
# Tracks green 'stoplight' and saves 45 seconds of tracking video
# Optimized for Raspberry Pi / Picamera2 / OpenCV

from picamera2 import Picamera2
import cv2
import time

# Define HSV bounds for green object
colorLower = (29, 70, 6)
colorUpper = (75, 255, 255)

# -----------------------------
# Camera / video settings
# -----------------------------
frame_width = 480
frame_height = 360
fps_request = 40.0
video_fps = 30
duration_seconds = 45

# Initialize Pi camera with OpenCV-friendly BGR output
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (frame_width, frame_height), "format": "BGR888"},
    controls={"FrameRate": fps_request}
)
picam2.configure(config)
picam2.start()

# Let camera warm up
time.sleep(0.2)

# Create video writer for processed/tracked output
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(
    "Jason's_stoplight_tracker.mp4",
    fourcc,
    video_fps,
    (frame_width, frame_height)
)

# Timing
start_time = time.time()

try:
    while True:
        # Capture frame in BGR
        image = picam2.capture_array()

        # Convert directly to HSV for speed
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create mask for green object
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

        # Track largest green contour
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)

            if M["m00"] != 0:
                center = (
                    int(M["m10"] / M["m00"]),
                    int(M["m01"] / M["m00"])
                )

                if radius > 0:
                    # Draw enclosing circle
                    cv2.circle(
                        image,
                        (int(x), int(y)),
                        int(radius),
                        (0, 255, 255),
                        2
                    )

                    # Draw center point
                    cv2.circle(
                        image,
                        center,
                        3,
                        (0, 0, 255),
                        -1
                    )

        # Show live frame
        cv2.imshow("Frame", image)

        # Save tracked frame to video
        out.write(image)

        # Stop after set duration
        elapsed = time.time() - start_time
        if elapsed >= duration_seconds:
            print("45 second video complete.")
            break

        # Manual quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("Recording stopped early.")
            break

finally:
    out.release()
    picam2.stop()
    cv2.destroyAllWindows()