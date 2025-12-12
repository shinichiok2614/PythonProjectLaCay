import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog


paused = False
cap = None
current_frame = None
show_tuner = True


# =========================
# HSV TRACKBARS
# =========================
def create_hsv_trackbars():
    cv2.namedWindow("HSV Tuner", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("H_low", "HSV Tuner", 25, 179, lambda x: None)
    cv2.createTrackbar("H_high", "HSV Tuner", 85, 179, lambda x: None)
    cv2.createTrackbar("S_low", "HSV Tuner", 40, 255, lambda x: None)
    cv2.createTrackbar("S_high", "HSV Tuner", 255, 255, lambda x: None)
    cv2.createTrackbar("V_low", "HSV Tuner", 40, 255, lambda x: None)
    cv2.createTrackbar("V_high", "HSV Tuner", 255, 255, lambda x: None)


# =========================
# CLICK TO PICK HSV
# =========================
def on_mouse(event, x, y, flags, frame):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        region = hsv[max(0, y-2):y+3, max(0, x-2):x+3]
        h, s, v = np.mean(region.reshape(-1, 3), axis=0).astype(int)

        cv2.setTrackbarPos("H_low", "HSV Tuner", max(0, h - 15))
        cv2.setTrackbarPos("H_high", "HSV Tuner", min(179, h + 15))
        cv2.setTrackbarPos("S_low", "HSV Tuner", max(0, s - 60))
        cv2.setTrackbarPos("S_high", "HSV Tuner", min(255, s + 60))
        cv2.setTrackbarPos("V_low", "HSV Tuner", max(0, v - 60))
        cv2.setTrackbarPos("V_high", "HSV Tuner", min(255, v + 60))

        print(f"[CLICK HSV] H={h}, S={s}, V={v} – Trackbars updated")


# =========================
# LEAF DETECTION
# =========================
def detect_leaf(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    h_low = cv2.getTrackbarPos("H_low", "HSV Tuner")
    h_high = cv2.getTrackbarPos("H_high", "HSV Tuner")
    s_low = cv2.getTrackbarPos("S_low", "HSV Tuner")
    s_high = cv2.getTrackbarPos("S_high", "HSV Tuner")
    v_low = cv2.getTrackbarPos("V_low", "HSV Tuner")
    v_high = cv2.getTrackbarPos("V_high", "HSV Tuner")

    lower = np.array([h_low, s_low, v_low])
    upper = np.array([h_high, s_high, v_high])

    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(frame, frame, mask=mask)
    return result, mask


# =========================
# BUTTON CALLBACKS
# =========================
def select_video():
    global cap
    path = filedialog.askopenfilename(
        title="Select Video",
        filetypes=[("Video Files", "*.mp4 *.avi *.mkv")]
    )
    if path:
        cap = cv2.VideoCapture(path)
        print("[SOURCE] Using selected video")
    else:
        cap = cv2.VideoCapture(0)
        print("[SOURCE] Using Camera")


def toggle_pause():
    global paused
    paused = not paused
    print("[PAUSED]" if paused else "[RESUMED]")


def manual_detect():
    global current_frame
    if current_frame is None:
        print("No frame available")
        return
    result, mask = detect_leaf(current_frame)
    cv2.imshow("Manual Detection", result)
    cv2.imshow("Mask", mask)
    print("[MANUAL DETECT DONE]")


def quit_app():
    root.destroy()
    cv2.destroyAllWindows()
    exit()


# =========================
# MAIN LOOP (RUNS VIA TKINTER)
# =========================
def update_video():
    global current_frame

    if cap is not None and not paused:
        ret, frame = cap.read()
        if ret:
            current_frame = frame.copy()

            cv2.namedWindow("Leaf Detection", cv2.WINDOW_NORMAL)
            cv2.setMouseCallback("Leaf Detection", on_mouse, frame)
            cv2.imshow("Leaf Detection", frame)
        else:
            print("[END OF VIDEO]")

    root.after(10, update_video)


# =========================
# TKINTER GUI
# =========================
root = tk.Tk()
root.title("Leaf Detector Control Panel")

tk.Button(root, text="Select Video / Camera", command=select_video, width=25).pack(pady=5)
tk.Button(root, text="Pause / Resume", command=toggle_pause, width=25).pack(pady=5)
tk.Button(root, text="Manual Detect", command=manual_detect, width=25).pack(pady=5)
tk.Button(root, text="Quit", command=quit_app, width=25).pack(pady=5)

create_hsv_trackbars()
select_video()
update_video()

root.mainloop()
