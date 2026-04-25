# ENME489Y: Remote Sensing
# Line laser triangulation lidar calibration image capture
# Picamera2 version for newer Raspberry Pi OS

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
    main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "RGB888"}
)

picam2.configure(config)
picam2.start()

# Allow camera exposure to settle
time.sleep(1)


# -----------------------------
# User distance input
# -----------------------------
d_input = input("Please enter distance from wall, in inches: ").strip()

try:
    distance_inches = float(d_input)
except ValueError:
    print("ERROR: Distance must be a number, such as 6, 12, 18, or 24.")
    picam2.stop()
    exit()

print("Confirming the distance you entered is:", distance_inches)


if distance_inches.is_integer():
    filename_distance = str(int(distance_inches))
else:
    filename_distance = str(distance_inches).replace(".", "_")

filename = filename_distance + ".jpg"


# -----------------------------
# Main camera loop
# -----------------------------
try:
    while True:

        image = picam2.capture_array()

        # Convert RGB image from Picamera2 to BGR for OpenCV display/save
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Flip image if camera is mounted upside down
        image = cv2.flip(image, -1)

        # Plot semi-crosshairs for alignment
        cv2.line(image, (640, 0), (640, 720), (0, 150, 150), 1)
        cv2.line(image, (600, 360), (1280, 360), (0, 150, 150), 1)

        # Display distance from the wall
        font = cv2.FONT_HERSHEY_COMPLEX_SMALL
        red = (0, 0, 255)

        cv2.putText(
            image,
            filename_distance,
            (800, 200),
            font,
            10,
            red,
            10
        )

        cv2.imshow("Image", image)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("Quit without saving image.")
            break

        if key == ord("m"):
            cv2.imwrite(filename, image)
            print("Saved image as:", filename)
            break

finally:
    cv2.destroyAllWindows()
    picam2.stop()
