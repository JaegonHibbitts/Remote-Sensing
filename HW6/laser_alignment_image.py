# ENME489Y: Remote Sensing
# Camera alignment viewer - Picamera2 version

from picamera2 import Picamera2
import time
import cv2


# -----------------------------
# Camera setup
# -----------------------------
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={
        "size": (FRAME_WIDTH, FRAME_HEIGHT),
        "format": "RGB888"
    }
)

picam2.configure(config)
picam2.start()

# Allow camera exposure/sensor to settle
time.sleep(1)

print("Camera started.")
print("Click on the image window, then press q to quit.")


try:
    while True:
        # Capture frame from Picamera2
        image = picam2.capture_array()

        # Picamera2 gives RGB, OpenCV expects BGR
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Flip image depending on mechanical setup
        image = cv2.flip(image, -1)

        # Plot crosshairs for alignment
        cv2.line(image, (640, 0), (640, 720), (0, 150, 150), 1)
        cv2.line(image, (0, 360), (1280, 360), (0, 150, 150), 1)

        # Plot green vertical lines every 50 pixels
        for i in range(50, 1280, 50):
            cv2.line(image, (i, 0), (i, 720), (0, 150, 0), 2)

        # Display the image
        cv2.imshow("Image", image)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("Exiting camera viewer.")
            break

finally:
    cv2.destroyAllWindows()
    picam2.stop()
