import base64

import cv2
import numpy as np

# Lazy-loaded Haar cascade for face detection (lightweight, no model download needed)
_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
_eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")


def decode_base64_image(image_base64: str) -> np.ndarray:
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    img_bytes = base64.b64decode(image_base64)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)


def analyze_frame(image_base64: str) -> dict:
    """
    Analyzes a webcam frame for proctoring purposes.
    Returns face count, gaze/looking-away heuristic, and flagged events.
    """
    img = decode_base64_image(image_base64)
    if img is None:
        return {"faces_detected": 0, "looking_away": False, "flagged_events": ["invalid_frame"]}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    flagged_events = []
    looking_away = False

    if len(faces) == 0:
        flagged_events.append("face_not_detected")
    elif len(faces) > 1:
        flagged_events.append("multiple_faces")
    else:
        # Single face: heuristic for "looking away" via eye detection within face ROI
        (x, y, w, h) = faces[0]
        face_roi = gray[y:y + h, x:x + w]
        eyes = _eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=5, minSize=(15, 15))
        if len(eyes) < 1:
            looking_away = True
            flagged_events.append("looking_away")

    return {
        "faces_detected": int(len(faces)),
        "looking_away": looking_away,
        "flagged_events": flagged_events,
    }
