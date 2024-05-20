import pickle
from django.conf import settings
from cam_app import views
from django.http import StreamingHttpResponse
import sqlite3
import datetime

# import some common libraries
import torch
import numpy as np
import os, json, cv2, random, glob, uuid
import matplotlib.pyplot as plt

from pathlib import Path
import time

import pathlib
from pathlib import Path

pathlib.PosixPath = pathlib.WindowsPath


class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
        model_path = os.path.join(settings.BASE_DIR, "deep_learning_models/best.pt")
        self.model = torch.hub.load(
            "ultralytics/yolov5", "custom", path=model_path, force_reload=True
        )

    def __del__(self):
        self.video.release()

    # def get_frame_with_detection(self):
    #     success, image = self.video.read()
    #     # We are using Motion JPEG, but OpenCV defaults to capture raw images,
    #     # so we must encode it into JPEG in order to correctly display the
    #     # video stream.
    #     outputs = image
    #     # if you dont want to show the detection, comment the below code till outputImage = image, and change it to outputImage = outputs
    #     face_cascade = cv2.CascadeClassifier(
    #         cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    #     )
    #     eyes_cascade = cv2.CascadeClassifier(
    #         cv2.data.haarcascades + "haarcascade_eye.xml"
    #     )
    #     gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    #     gray = cv2.equalizeHist(gray)
    #     # -- Detect faces
    #     faces = face_cascade.detectMultiScale(gray)
    #     for x, y, w, h in faces:
    #         center = (x + w // 2, y + h // 2)
    #         image = cv2.ellipse(
    #             image, center, (w // 2, h // 2), 0, 0, 360, (255, 0, 255), 4
    #         )
    #         faceROI = gray[y : y + h, x : x + w]
    #         # -- In each face, detect eyes
    #         eyes = eyes_cascade.detectMultiScale(faceROI)
    #         for x2, y2, w2, h2 in eyes:
    #             eye_center = (x + x2 + w2 // 2, y + y2 + h2 // 2)
    #             radius = int(round((w2 + h2) * 0.25))
    #             image = cv2.circle(image, eye_center, radius, (255, 0, 0), 4)
    #     outputImage = image
    #     ret, outputImagetoReturn = cv2.imencode(".jpg", outputImage)
    #     return outputImagetoReturn.tobytes(), outputImage

    # def get_frame_without_detection(self):
    #     success, image = self.video.read()
    #     # We are using Motion JPEG, but OpenCV defaults to capture raw images,
    #     # so we must encode it into JPEG in order to correctly display the
    #     # video stream.
    #     outputs = image
    #     outputImage = outputs
    #     ret, outputImagetoReturn = cv2.imencode(".jpg", outputImage)
    #     return outputImagetoReturn.tobytes(), outputImage

    def get_frame_with_detection(self):
        success, image = self.video.read()
        if not success:
            return None, None

        # Perform YOLOv5 detection
        results = self.model(image)

        # Draw bounding boxes and labels on the image
        for detection in results.xyxy[0]:  # Assuming a single image in the batch
            x1, y1, x2, y2, conf, cls = map(int, detection[:6])
            label = f"{self.model.names[cls]} {conf:.2f}"
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                image,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )

        outputImage = image
        ret, outputImagetoReturn = cv2.imencode(".jpg", outputImage)
        return outputImagetoReturn.tobytes(), outputImage

    def get_frame_without_detection(self):
        success, image = self.video.read()
        if not success:
            return None, None

        outputImage = image
        ret, outputImagetoReturn = cv2.imencode(".jpg", outputImage)
        return outputImagetoReturn.tobytes(), outputImage


def generate_frames(camera, AI):
    try:
        while True:
            if AI:
                frame, img = camera.get_frame_with_detection()
            if not AI:
                frame, img = camera.get_frame_without_detection()
            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n"
            )
    except Exception as e:
        print(e)

    finally:
        print("Reached finally, detection stopped")
        cv2.destroyAllWindows()
