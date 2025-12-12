import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import json
import os

# =============================
# GLOBAL VARIABLES
# =============================
paused = False
cap = None
current_frame = None

preset_path = None
loaded_preset_name = ""
loaded_preset_count = 0


# =============================
# HSV TRACKBARS
# =============================
def create_hsv_trackbars():
    cv2.namedWindow("HSV Tuner", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("H_low", "HSV Tuner", 25, 179, lambda x: None)
    cv2.createTrackbar("H_high", "HSV Tuner", 85, 179, lambda x: None)
    cv2.createTrackbar("S_low", "HSV Tuner", 40, 255, lambda x: None)
    cv2.createTrackbar("S_high", "HSV Tuner", 255, 255, lambda x: None)
    cv2.createTrackbar("V_low", "HSV Tuner", 40, 255, lambda x: None)
    cv2.createTrackbar("V_high", "HSV Tuner", 255, 255, lambda x: None)


# =============================
# CLICK TO PICK HSV
# =============================
def on_mouse(event, x, y, flags, frame):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        region = hsv[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
        h, s, v = np.mean(region.reshape(-1, 3), axis=0).astype(int)

        cv2.setTrackbarPos("H_low", "HSV Tuner", max(0, h - 15))
        cv2.setTrackbarPos("H_high", "HSV Tuner", min(179, h + 15))
        cv2.setTrackbarPos("S_low", "HSV Tuner", max(0, s - 60))
        cv2.setTrackbarPos("S_high", "HSV Tuner", min(255, s + 60))
        cv2.setTrackbarPos("V_low", "HSV Tuner", max(0, v - 60))
        cv2.setTrackbarPos("V_high", "HSV Tuner", min(255, v + 60))

        print(f"[CLICK HSV] H={h} S={s} V={v} — Trackbar updated")


# =============================
# LEAF DETECTION + BOUNDING BOX
# =============================
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
    result = frame.copy()

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 500:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return result, mask


# =============================
# SAVE PRESET (append nhiều detect)
# =============================
def save_preset():
    global preset_path, loaded_preset_name, loaded_preset_count

    if preset_path is None:
        preset_path = filedialog.asksaveasfilename(
            title="Save Preset As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if not preset_path:
            return

    hsv_values = {
        "H_low": cv2.getTrackbarPos("H_low", "HSV Tuner"),
        "H_high": cv2.getTrackbarPos("H_high", "HSV Tuner"),
        "S_low": cv2.getTrackbarPos("S_low", "HSV Tuner"),
        "S_high": cv2.getTrackbarPos("S_high", "HSV Tuner"),
        "V_low": cv2.getTrackbarPos("V_low", "HSV Tuner"),
        "V_high": cv2.getTrackbarPos("V_high", "HSV Tuner")
    }

    if not os.path.exists(preset_path):
        data = {"presets": [hsv_values]}
    else:
        with open(preset_path, "r") as f:
            data = json.load(f)
        data["presets"].append(hsv_values)

    with open(preset_path, "w") as f:
        json.dump(data, f, indent=4)

    loaded_preset_name = os.path.basename(preset_path)
    loaded_preset_count = len(data["presets"])

    update_preset_label()
    print(f"[Preset Saved] Total detects: {loaded_preset_count}")


# =============================
# LOAD PRESET
# =============================
def load_preset():
    global preset_path, loaded_preset_name, loaded_preset_count

    preset_path = filedialog.askopenfilename(
        title="Select Preset",
        filetypes=[("JSON files", "*.json")]
    )

    if not preset_path:
        return

    try:
        with open(preset_path, "r") as f:
            data = json.load(f)

        presets = data.get("presets", [])
        if not presets:
            print("[Preset] File empty")
            return

        latest = presets[-1]

        cv2.setTrackbarPos("H_low", "HSV Tuner", latest["H_low"])
        cv2.setTrackbarPos("H_high", "HSV Tuner", latest["H_high"])
        cv2.setTrackbarPos("S_low", "HSV Tuner", latest["S_low"])
        cv2.setTrackbarPos("S_high", "HSV Tuner", latest["S_high"])
        cv2.setTrackbarPos("V_low", "HSV Tuner", latest["V_low"])
        cv2.setTrackbarPos("V_high", "HSV Tuner", latest["V_high"])

        loaded_preset_name = os.path.basename(preset_path)
        loaded_preset_count = len(presets)

        update_preset_label()
        print(f"[Preset Loaded] {loaded_preset_name} — {loaded_preset_count} detects")

    except:
        print("[Preset Error] Invalid file")


# =============================
# UPDATE LABEL IN TKINTER
# =============================
def update_preset_label():
    if loaded_preset_name:
        preset_info.config(
            text=f"Preset: {loaded_preset_name} | Detects: {loaded_preset_count}",
            fg="green"
        )
    else:
        preset_info.config(text="No preset loaded", fg="red")


# =============================
# VIDEO SOURCE
# =============================
def select_video():
    global cap
    path = filedialog.askopenfilename(
        title="Select Video",
        filetypes=[("Video Files", "*.mp4 *.avi *.mkv")]
    )
    if path:
        cap = cv2.VideoCapture(path)
        print("[SOURCE] Video loaded")
    else:
        cap = cv2.VideoCapture(0)
        print("[SOURCE] Camera loaded")


# =============================
# BUTTON ACTIONS
# =============================
def toggle_pause():
    global paused
    paused = not paused
    print("Paused" if paused else "Resumed")


def manual_detect():
    global current_frame
    if current_frame is None:
        return

    result, mask = detect_leaf(current_frame)
    cv2.imshow("Manual Detection", result)
    cv2.imshow("Mask", mask)

    save_preset()
    print("[Manual Detect + Saved]")


def quit_app():
    root.destroy()
    cv2.destroyAllWindows()
    exit()


# =============================
# MAIN LOOP
# =============================
def update_video():
    global current_frame

    if cap is not None and not paused:
        ret, frame = cap.read()
        if ret:
            current_frame = frame.copy()

            detected, _ = detect_leaf(frame)

            cv2.namedWindow("Leaf Detection", cv2.WINDOW_NORMAL)
            cv2.setMouseCallback("Leaf Detection", on_mouse, frame)
            cv2.imshow("Leaf Detection", detected)

    root.after(10, update_video)


# =============================
# TKINTER GUI
# =============================
root = tk.Tk()
root.title("Leaf Detector Control Panel")

tk.Button(root, text="Select Video / Camera", command=select_video, width=25).pack(pady=5)
tk.Button(root, text="Pause / Resume", command=toggle_pause, width=25).pack(pady=5)
tk.Button(root, text="Manual Detect", command=manual_detect, width=25).pack(pady=5)

tk.Button(root, text="Save Preset", command=save_preset, width=25).pack(pady=5)
tk.Button(root, text="Load Preset", command=load_preset, width=25).pack(pady=5)

preset_info = tk.Label(root, text="No preset loaded", fg="red")
preset_info.pack(pady=5)

tk.Button(root, text="Quit", command=quit_app, width=25).pack(pady=5)

create_hsv_trackbars()
select_video()
update_video()

root.mainloop()
