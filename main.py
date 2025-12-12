"""
Leaf detector from camera or video using OpenCV.

Features:
- Capture from camera (default) or video file
- Real-time color segmentation in HSV to detect green leaves
- Optional trackbars to tune HSV lower/upper thresholds live
- Morphological filtering, contour detection, bounding boxes
- Area and contour filtering to reduce noise
- Save detected frames/masks with 's' key

Dependencies: opencv-python, numpy
Install: pip install opencv-python numpy

Usage:
    python leaf_detector.py            # open default camera
    python leaf_detector.py --video path/to/video.mp4

Controls while running:
    q - quit
    t - toggle trackbar (HSV tuning)
    s - save current frame + mask
    c - toggle contour boxes

Notes: This method uses color segmentation which works best under
consistent lighting and for green leaves. For broader datasets or
non-green leaves, consider training a segmentation or object detection
model (U-Net / Mask R-CNN / YOLO) and replacing the color-threshold
step with the model inference.
"""

import argparse
import os
import time
from datetime import datetime

import cv2
import numpy as np


def create_trackbar_window(window_name, initial_low=(25, 40, 40), initial_high=(90, 255, 255)):
    cv2.namedWindow(window_name)
    # Create trackbars for HSV lower and upper bounds
    cv2.createTrackbar('H_low', window_name, initial_low[0], 179, lambda x: None)
    cv2.createTrackbar('S_low', window_name, initial_low[1], 255, lambda x: None)
    cv2.createTrackbar('V_low', window_name, initial_low[2], 255, lambda x: None)
    cv2.createTrackbar('H_high', window_name, initial_high[0], 179, lambda x: None)
    cv2.createTrackbar('S_high', window_name, initial_high[1], 255, lambda x: None)
    cv2.createTrackbar('V_high', window_name, initial_high[2], 255, lambda x: None)


def get_trackbar_values(window_name):
    h1 = cv2.getTrackbarPos('H_low', window_name)
    s1 = cv2.getTrackbarPos('S_low', window_name)
    v1 = cv2.getTrackbarPos('V_low', window_name)
    h2 = cv2.getTrackbarPos('H_high', window_name)
    s2 = cv2.getTrackbarPos('S_high', window_name)
    v2 = cv2.getTrackbarPos('V_high', window_name)
    lower = np.array([h1, s1, v1], dtype=np.uint8)
    upper = np.array([h2, s2, v2], dtype=np.uint8)
    return lower, upper


def preprocess_frame(frame, width=None):
    if width is not None:
        h, w = frame.shape[:2]
        if w != width:
            scale = width / float(w)
            frame = cv2.resize(frame, (width, int(h * scale)))
    # optional: apply slight blur to reduce noise
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    return blurred


def detect_leaves(frame, lower_hsv, upper_hsv, min_area=500, kernel_size=5):
    # Convert to HSV and threshold
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)

    # Morphological operations to clean up mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Optional: fill small holes using dilation then erosion
    # mask = cv2.dilate(mask, kernel, iterations=1)
    # mask = cv2.erode(mask, kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detections = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        # Optionally compute solidity, aspect ratio, extent, etc.
        rect = (x, y, w, h)
        detections.append({'contour': cnt, 'area': area, 'rect': rect})

    return mask, detections


def draw_detections(frame, detections, show_contours=True):
    out = frame.copy()
    for det in detections:
        x, y, w, h = det['rect']
        area = det['area']
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(out, f"{int(area)}", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if show_contours:
            cv2.drawContours(out, [det['contour']], -1, (0, 128, 255), 1)
    return out


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def main():
    parser = argparse.ArgumentParser(description='Leaf detector from camera or video (OpenCV)')
    parser.add_argument('--video', '-v', help='Path to video file (omit to use camera)')
    parser.add_argument('--camera', '-c', type=int, default=0, help='Camera index (default 0)')
    parser.add_argument('--width', type=int, default=800, help='Resize width for processing (speeds up)')
    parser.add_argument('--min-area', type=int, default=800, help='Minimum contour area to keep')
    parser.add_argument('--no-trackbar', dest='trackbar', action='store_false', help="Don't show HSV trackbars")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video if args.video else args.camera)
    if not cap.isOpened():
        print('ERROR: Cannot open video source')
        return

    trackbar_win = 'HSV Tuner'
    if args.trackbar:
        # Reasonable default for green leaves, but lighting varies
        create_trackbar_window(trackbar_win, initial_low=(25, 40, 40), initial_high=(95, 255, 255))

    save_dir = 'leaf_detections'
    ensure_dir(save_dir)
    frame_count = 0
    show_contours = True

    print("Controls: q=quit, t=toggle trackbar, s=save, c=toggle contours")

    while True:
        ret, frame = cap.read()
        if not ret:
            print('End of stream or cannot fetch frame')
            break
        frame_count += 1

        frame_proc = preprocess_frame(frame, width=args.width)

        if args.trackbar:
            lower, upper = get_trackbar_values(trackbar_win)
        else:
            # Default HSV range for green leaves (may need tuning)
            lower = np.array([25, 40, 40], dtype=np.uint8)
            upper = np.array([95, 255, 255], dtype=np.uint8)

        mask, detections = detect_leaves(frame_proc, lower, upper, min_area=args.min_area)
        out = draw_detections(frame_proc, detections, show_contours=show_contours)

        # show side-by-side
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        combined = np.hstack([out, mask_bgr])

        cv2.imshow('Leaf Detector - Output | Mask', combined)
        if args.trackbar:
            # also show tuner window (trackbars are already visible)
            pass

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fname_frame = os.path.join(save_dir, f'frame_{ts}.jpg')
            fname_mask = os.path.join(save_dir, f'mask_{ts}.png')
            cv2.imwrite(fname_frame, frame_proc)
            cv2.imwrite(fname_mask, mask)
            print('Saved', fname_frame, fname_mask)
        elif key == ord('c'):
            show_contours = not show_contours
            print('Show contours:', show_contours)
        elif key == ord('t'):
            args.trackbar = not args.trackbar
            if args.trackbar:
                create_trackbar_window(trackbar_win)
                print('Trackbar ON')
            else:
                cv2.destroyWindow(trackbar_win)
                print('Trackbar OFF')

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
