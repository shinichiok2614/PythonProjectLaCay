"""
Leaf detector from camera or video using OpenCV — rewritten clean version.
- Chọn video bằng hộp thoại
- Tự động thu nhỏ để không vượt quá màn hình
- HSV trackbar tùy chỉnh
- Vẽ contour + bounding box
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import ctypes
from datetime import datetime
import os


def pick_video():
    root = tk.Tk(); root.withdraw()
    file = filedialog.askopenfilename(title='Chọn file video',
                                      filetypes=[('Video files','*.mp4 *.avi *.mkv *.mov')])
    return file


def preprocess_frame(frame, width=900):
    h, w = frame.shape[:2]
    if w != width:
        scale = width / w
        frame = cv2.resize(frame, (width, int(h * scale)))
    return frame


def detect_leaves(frame, lower, upper, min_area=500):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detections = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        detections.append((c, x, y, w, h, area))
    return mask, detections


def draw_detections(img, detections):
    out = img.copy()
    for c, x, y, w, h, area in detections:
        cv2.rectangle(out, (x,y), (x+w,y+h), (0,255,0), 2)
        cv2.putText(out, str(int(area)), (x,y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        cv2.drawContours(out, [c], -1, (0,128,255), 1)
    return out


def get_screen_resolution():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def main():
    print("Đang mở hộp thoại chọn video...")
    video = pick_video()
    if not video:
        print("Không chọn video → dùng camera")
        video = 0

    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        print("Không mở được video/camera")
        return

    lower = np.array([25, 40, 40], np.uint8)
    upper = np.array([95, 255, 255], np.uint8)

    screen_w, screen_h = get_screen_resolution()
    print(f"Độ phân giải màn hình: {screen_w}x{screen_h}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = preprocess_frame(frame)
        mask, det = detect_leaves(frame, lower, upper)
        out = draw_detections(frame, det)

        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        combined = np.hstack((out, mask_bgr))

        # scale to fit screen
        scale = min(screen_w / combined.shape[1], screen_h / combined.shape[0], 1)
        if scale < 1:
            combined = cv2.resize(combined, (int(combined.shape[1]*scale), int(combined.shape[0]*scale)))

        cv2.namedWindow('LeafDetector', cv2.WINDOW_NORMAL)
        cv2.imshow('LeafDetector', combined)

        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()