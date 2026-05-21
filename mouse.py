import cv2
import numpy as np
import HandTrackingModule as htm
import time
import autopy
import math
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# ================== SETTINGS ==================
screen_width, screen_height = autopy.screen.size()
wCam, hCam = 640,480
frameR = 0
smoothening = 2
pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
last_zoom_time = 0  # cooldown timer

# ================== VIDEO SETUP ==================
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.handDetector(maxHands=1)
wScr, hScr = autopy.screen.size()

# ================== VOLUME CONTROL SETUP ==================
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
minVol, maxVol = volRange[0], volRange[1]

# ================== SCROLL ACTION FUNCTION ==================
def action_func(incoming_data):
    """Performs scroll actions based on detected gestures"""
    print('Gesture Action:', incoming_data)
    if '3' in incoming_data:        # Scroll Down
        pyautogui.scroll(-150)
    if '4' in incoming_data:        # Scroll Up
        pyautogui.scroll(150)

# ================== MAIN LOOP ==================
print(f"Screen size: {wScr}x{hScr}")

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]     # Index finger tip
        x2, y2 = lmList[12][1:]    # Middle finger tip
        x_thumb, y_thumb = lmList[4][1:]  # Thumb tip
        x_ring, y_ring = lmList[16][1:]   # Ring finger tip

        fingers = detector.fingersUp()

        cv2.rectangle(img, (frameR, frameR),
                      (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

        # --------------- MOVE MODE (Index finger only) ---------------
        if fingers[1] == 1 and fingers[2] == 0:
            x3 = np.interp(x1, (0, wCam), (0, screen_width))
            y3 = np.interp(y1, (0, hCam), (0, screen_height))
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening
            autopy.mouse.move(wScr - clocX, clocY)
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        # --------------- LEFT CLICK (Index + Middle) ---------------
        if fingers[1] == 1 and fingers[2] == 1:
            length, img, lineInfo = detector.findDistance(8, 12, img)
            if length < 40:
                cv2.circle(img, (lineInfo[4], lineInfo[5]),
                           15, (0, 255, 0), cv2.FILLED)
                autopy.mouse.click()

        # --------------- RIGHT CLICK (Thumb + Middle) ---------------
        if fingers[0] == 1 and fingers[2] == 1:
            length, img, lineInfo = detector.findDistance(4, 12, img)
            if length < 40:
                cv2.circle(img, (lineInfo[4], lineInfo[5]),
                           15, (0, 0, 255), cv2.FILLED)
                autopy.mouse.click(autopy.mouse.Button.RIGHT)

                cv2.putText(img, "Right Click", (10, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # --------------- VOLUME CONTROL (Thumb + Index) ---------------
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
            length, img, _ = detector.findDistance(4, 8, img)
            vol = np.interp(length, [20, 200], [minVol, maxVol])
            volume.SetMasterVolumeLevel(vol, None)
            vol_percent = int(np.interp(length, [20, 200], [0, 100]))
            cv2.putText(img, f'Volume: {vol_percent}%', (10, 450),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 100, 0), 2)

        # --------------- SCROLL DOWN (Fist) ---------------
        if fingers == [0, 0, 0, 0, 0]:
            action_func('3')  # Scroll down

        # --------------- SCROLL UP (Open Palm) ---------------
        elif fingers == [1, 1, 1, 1, 1]:
            action_func('4')  # Scroll up

        # --------------- ZOOM (Thumbs Up / Down) ---------------
        if fingers == [1, 0, 0, 0, 0]:  # Only thumb up
            thumb_tip_y = lmList[4][2]
            wrist_y = lmList[0][2]
            current_time = time.time()

            # Cooldown: allow zoom only every 0.6 sec
            if current_time - last_zoom_time > 0.6:
                if wrist_y - thumb_tip_y > 60:  # Thumbs Up
                    pyautogui.keyDown('ctrl')
                    pyautogui.scroll(150)  # Zoom in
                    pyautogui.keyUp('ctrl')
                    cv2.putText(img, "Zoom In 👍", (10, 400),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                    last_zoom_time = current_time

                elif thumb_tip_y - wrist_y > 60:  # Thumbs Down
                    pyautogui.keyDown('ctrl')
                    pyautogui.scroll(-150)  # Zoom out
                    pyautogui.keyUp('ctrl')
                    cv2.putText(img, "Zoom Out 👎", (10, 400),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    last_zoom_time = current_time

    # --------------- FRAME RATE ---------------
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) != 0 else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 50),
                cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

    # --------------- DISPLAY WINDOW ---------------
    cv2.imshow('Virtual Mouse', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
