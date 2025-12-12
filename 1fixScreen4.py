import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog


# =========================
# GLOBAL SETTINGS
# =========================
paused = False
show_tuner = True
screen_w = 1366
screen_h = 768


# =========================
# TẠO TRACKBARS
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
# CLICK LẤY HSV
# =========================
def on_mouse(event, x, y, flags, frame):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        region = hsv[max(0, y-2):y+3, max(0, x-2):x+3]
        h, s, v = np.mean(region.reshape(-1, 3), axis=0).astype(int)

        print(f"[CLICK HSV] H={h}, S={s}, V={v}")

        cv2.setTrackbarPos("H_low",  "HSV Tuner", max(0, h - 15))
        cv2.setTrackbarPos("H_high", "HSV Tuner", min(179, h + 15))

        cv2.setTrackbarPos("S_low",  "HSV Tuner", max(0, s - 60))
        cv2.setTrackbarPos("S_high", "HSV Tuner", min(255, s + 60))

        cv2.setTrackbarPos("V_low",  "HSV Tuner", max(0, v - 60))
        cv2.setTrackbarPos("V_high", "HSV Tuner", min(255, v + 60))

        print("[Trackbars Updated]")


# =========================
# NHẬN DIỆN LÁ
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
# HỘP THOẠI CHỌN VIDEO HOẶC CAMERA
# =========================
def choose_video_source():
    root = tk.Tk()
    root.withdraw()

    print("Chọn video file hoặc Cancel để dùng camera...")

    video_path = filedialog.askopenfilename(
        title="Chọn Video",
        filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
    )

    if video_path:
        print("[SOURCE] Video:", video_path)
        return cv2.VideoCapture(video_path)

    print("[SOURCE] Camera (0)")
    return cv2.VideoCapture(0)  # mặc định camera 0


# =========================
# MAIN LOOP
# =========================
def main():
    global paused, show_tuner

    cap = choose_video_source()
    cv2.namedWindow("Leaf Detection", cv2.WINDOW_NORMAL)

    create_hsv_trackbars()

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

        # Scale video không vượt màn hình
        scale = min(screen_w / frame.shape[1], screen_h / frame.shape[0], 1.0)
        display_frame = cv2.resize(frame, None, fx=scale, fy=scale)

        # Click lấy HSV
        cv2.setMouseCallback("Leaf Detection", on_mouse, frame)

        cv2.imshow("Leaf Detection", display_frame)

        if show_tuner:
            cv2.imshow("HSV Tuner", np.zeros((200, 500, 3), dtype=np.uint8))

        # Nhận phím từ bất kỳ cửa sổ nào đang focus
        key = cv2.waitKey(1) & 0xFF

        # ==============================
        # CÁC PHÍM TẮT (trong HSV Tuner)
        # ==============================

        if key == ord('q'):
            break

        if key == ord('p'):
            paused = not paused
            print("[PAUSED]" if paused else "[RESUMED]")

        if key == ord('t'):
            show_tuner = not show_tuner
            if not show_tuner:
                cv2.destroyWindow("HSV Tuner")
            else:
                create_hsv_trackbars()
            print("[TUNER ON]" if show_tuner else "[TUNER OFF]")

        if key == ord('d'):
            print("[MANUAL DETECT]")
            result, mask = detect_leaf(frame)
            cv2.imshow("Manual Detection", result)
            cv2.imshow("Mask", mask)

        if key == ord('s'):
            cv2.imwrite("leaf_frame.jpg", frame)
            _, mask = detect_leaf(frame)
            cv2.imwrite("leaf_mask.jpg", mask)
            print("[Saved leaf_frame.jpg + leaf_mask.jpg]")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
