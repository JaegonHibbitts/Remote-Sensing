# ENME489Y Spring 2019
# Updated Python 3 / Raspberry Pi OS version
# Code implements Ring Doorbell functionality on the Raspberry Pi

import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import numpy as np
from datetime import datetime
import time
import os
import cv2
import shutil
import subprocess


# ---------------- USER SETTINGS ----------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DROPBOX_UPLOADER = os.path.join(
    BASE_DIR,
    "Dropbox-Uploader",
    "dropbox_uploader.sh"
)

DROPBOX_REMOTE_FOLDER = "/ring_videos/"

# Email settings
# Replace these before testing email.
smtpUser = "jhaegon123@gmail.com"
smtpPass = "rvxy usqa bfku efwy"
toAdd = "jhaegon123@gmail.com"

# Detection settings
PIXEL_THRESHOLD = 50
DETECTOR_TRIGGER_THRESHOLD = 30000
VIDEO_DURATION_MS = 30000


# ---------------- HELPER FUNCTIONS ----------------

def run_command(command):
    """Run shell command and print it for debugging."""
    print("Running command:", command)
    result = subprocess.run(command, shell=True)
    return result.returncode


def get_camera_still_command(output_file):
    """
    Uses modern Raspberry Pi camera command if available.
    Newer Pi OS uses rpicam-still or libcamera-still instead of raspistill.
    """
    if shutil.which("rpicam-still"):
        return f"rpicam-still --width 640 --height 480 --vflip --hflip -o {output_file}"
    elif shutil.which("libcamera-still"):
        return f"libcamera-still --width 640 --height 480 --vflip --hflip -o {output_file}"
    elif shutil.which("raspistill"):
        return f"raspistill -w 640 -h 480 -vf -hf -o {output_file}"
    else:
        raise RuntimeError("No supported camera still command found: rpicam-still, libcamera-still, or raspistill.")


def get_camera_video_command(output_file):
    """
    Uses modern Raspberry Pi camera video command if available.
    Newer Pi OS uses rpicam-vid or libcamera-vid instead of raspivid.
    """
    if shutil.which("rpicam-vid"):
        return f"rpicam-vid -t {VIDEO_DURATION_MS} --width 640 --height 480 --framerate 30 --vflip --hflip -o {output_file}"
    elif shutil.which("libcamera-vid"):
        return f"libcamera-vid -t {VIDEO_DURATION_MS} --width 640 --height 480 --framerate 30 --vflip --hflip -o {output_file}"
    elif shutil.which("raspivid"):
        return f"raspivid -t {VIDEO_DURATION_MS} -w 640 -h 480 -fps 30 -vf -hf -o {output_file}"
    else:
        raise RuntimeError("No supported camera video command found: rpicam-vid, libcamera-vid, or raspivid.")


def capture_image(filename):
    """Capture an image and verify OpenCV can read it."""
    output_path = os.path.join(BASE_DIR, filename)
    command = get_camera_still_command(output_path)
    ret = run_command(command)

    if ret != 0:
        raise RuntimeError(f"Camera command failed while capturing {filename}")

    img = cv2.imread(output_path)

    if img is None:
        raise RuntimeError(f"OpenCV could not read {output_path}. Image may not have been created correctly.")

    return img


def record_video(timestr):
    """Record video and return h264 path."""
    h264_path = os.path.join(BASE_DIR, timestr + ".h264")
    command = get_camera_video_command(h264_path)
    ret = run_command(command)

    if ret != 0:
        raise RuntimeError("Video recording command failed.")

    return h264_path


def convert_h264_to_mp4(timestr):
    """Convert .h264 to .mp4 using MP4Box if available, otherwise ffmpeg."""
    h264_path = os.path.join(BASE_DIR, timestr + ".h264")
    mp4_path = os.path.join(BASE_DIR, timestr + ".mp4")

    if shutil.which("MP4Box"):
        command = f"MP4Box -add {h264_path} {mp4_path}"
    elif shutil.which("ffmpeg"):
        command = f"ffmpeg -y -i {h264_path} -c copy {mp4_path}"
    else:
        raise RuntimeError("Neither MP4Box nor ffmpeg was found. Install one of them to convert video.")

    ret = run_command(command)

    if ret != 0:
        raise RuntimeError("Video conversion command failed.")

    return mp4_path


def upload_to_dropbox(local_file):
    """Upload the video to Dropbox using Dropbox-Uploader script."""
    if not os.path.exists(DROPBOX_UPLOADER):
        raise RuntimeError(f"Dropbox uploader script not found at: {DROPBOX_UPLOADER}")

    command = f"{DROPBOX_UPLOADER} upload {local_file} {DROPBOX_REMOTE_FOLDER}"
    ret = run_command(command)

    if ret != 0:
        raise RuntimeError("Dropbox upload failed.")


def send_email(f_time, t_video):
    """Send email with test1.jpg and test2.jpg attached."""
    fromAdd = smtpUser
    subject = "Ring recording from: " + f_time

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = fromAdd
    msg["To"] = toAdd
    msg.preamble = "Photo @ " + f_time

    body = MIMEText("Ring Video: " + f_time + ", video length: " + str(t_video))
    msg.attach(body)

    for image_name in ["test1.jpg", "test2.jpg"]:
        image_path = os.path.join(BASE_DIR, image_name)

        with open(image_path, "rb") as fp:
            img = MIMEImage(fp.read())
            img.add_header("Content-Disposition", "attachment", filename=image_name)
            msg.attach(img)

    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(smtpUser, smtpPass)
    s.sendmail(fromAdd, toAdd, msg.as_string())
    s.quit()

    print("Email delivered " + f_time)


def mask_image(img):
    """
    Mask image such that the algorithm is triggered only by someone at the front door.
    This replaces imutils.resize() with cv2.resize().
    """
    mask = np.zeros((img.shape[0], img.shape[1]), dtype="uint8")

    pts = np.array(
        [[240, 475], [240, 420], [310, 420], [375, 410],
         [525, 350], [550, 100], [635, 100], [635, 475]],
        dtype=np.int32
    )
    cv2.fillConvexPoly(mask, pts, 255)

    pts = np.array(
        [[1, 395], [1, 315], [110, 305], [110, 365]],
        dtype=np.int32
    )
    cv2.fillConvexPoly(mask, pts, 255)

    masked = cv2.bitwise_and(img, img, mask=mask)

    scale = 200 / masked.shape[1]
    gray = cv2.resize(masked, (200, int(masked.shape[0] * scale)))

    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    return gray


def compute_detector_total(gray1, gray2):
    """Compare two masked grayscale images and return detector_total."""
    detector = np.zeros((gray2.shape[0], gray2.shape[1], 3), dtype="uint8")

    for i in range(0, gray2.shape[0]):
        for j in range(0, gray2.shape[1]):
            diff = abs(int(gray1[i, j]) - int(gray2[i, j]))

            if diff > PIXEL_THRESHOLD and int(gray1[i, j]) > 0:
                detector[i, j] = 255

    detector_total = np.uint64(np.sum(detector))
    return detector_total


def log_detector_total(detector_total):
    """Write detector_total values to ringlog.txt for post-processing."""
    log_path = os.path.join(BASE_DIR, "ringlog.txt")

    with open(log_path, "a") as f:
        now = datetime.now()
        timestamp = now.strftime("%Y/%m/%d %H:%M")
        outstring = str(timestamp) + " " + str(detector_total) + "\n"
        f.write(outstring)


# ---------------- MAIN PROGRAM ----------------

def main():
    os.chdir(BASE_DIR)

    print("Capturing first image...")
    test1 = capture_image("test1.jpg")
    gray1 = mask_image(test1)

    abs1 = np.uint64(np.sum(gray1))
    print("Sum of gray1:")
    print(abs1)
    print("Captured 1st image & performed analytics...moving on to video loop")

    counter = -1

    while True:
        counter += 1
        print(counter)
        time.sleep(0.01)

        print("Capturing second image...")
        test2 = capture_image("test2.jpg")
        gray2 = mask_image(test2)

        abs2 = np.uint64(np.sum(gray2))
        print("Sum of gray2:")
        print(abs2)

        if abs1 >= abs2:
            abs_diff = np.uint64(abs1 - abs2)
        else:
            abs_diff = np.uint64(abs2 - abs1)

        print(" ")
        print("Absolute difference of gray1 - gray2:")
        print(abs_diff)
        print(" ")

        detector_total = compute_detector_total(gray1, gray2)

        print("detector_total =")
        print(detector_total)
        print(" ")

        log_detector_total(detector_total)

        if counter > 0 and detector_total > DETECTOR_TRIGGER_THRESHOLD:
            print("Ring has detected someone/something at the door!")

            f_time = datetime.now().strftime("%a %d %b @ %H:%M")
            timestr = time.strftime("ringcameraview-%Y%m%d-%H%M%S")

            t_start = time.time()

            print("Recording video...")
            record_video(timestr)

            t_stop = time.time()
            t_video = t_stop - t_start

            time.sleep(0.1)

            print("Finished recording .h264...now converting to .mp4")
            mp4_path = convert_h264_to_mp4(timestr)

            print("Finished converting...now uploading to Dropbox...")
            upload_to_dropbox(mp4_path)

            print("Finished uploading...now sending email...")
            send_email(f_time, t_video)

            counter = 0

            print("Resetting first image after detection...")
            test1 = capture_image("test1.jpg")
            gray1 = mask_image(test1)

            abs1 = np.uint64(np.sum(gray1))
            print("Sum of gray1:")
            print(abs1)
            print("Captured 1st image & performed analytics...moving on to video loop")

        else:
            print("Nothing detected...yet!")

            test1 = capture_image("test1.jpg")
            gray1 = mask_image(test1)

            abs1 = np.uint64(np.sum(gray1))
            print("Sum of gray1:")
            print(abs1)
            print("Captured 1st image & performed analytics...moving on to video loop")


if __name__ == "__main__":
    main()
