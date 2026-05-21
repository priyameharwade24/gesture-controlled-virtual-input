import cv2
import mediapipe as mp
import numpy as np
import math
import time
import pyautogui

# ---------------- SETTINGS ----------------
FONT = cv2.FONT_HERSHEY_SIMPLEX
CLICK_THRESHOLD = 40
CLICK_COOLDOWN = 0.4
last_click_time = 0
typed_text = ""

caps_mode = False  # INTERNAL CAPS STATE

# ---------------- MEDIAPIPE ----------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ---------------- FULL KEYBOARD LAYOUT ----------------
layout = [
    ['1','2','3','4','5','6','7','8','9','0','-','=','Backspace'],
    ['Tab','Q','W','E','R','T','Y','U','I','O','P','[',']','\\'],
    ['Caps','A','S','D','F','G','H','J','K','L',';','\'','Enter'],
    ['Shift','Z','X','C','V','B','N','M',',','.','/','Shift'],
    ['Ctrl','Win','Alt','Space','Alt','Fn','Menu','Ctrl']
]

# ---------------- ROW WIDTH CALCULATION ----------------
def get_row_width(row, key_w, gap):
    width = 0
    for key in row:
        w_mult = {
            'Backspace': 1.5,
            'Tab': 1.2,
            'Caps': 1.4,
            'Enter': 1.7,
            'Shift': 1.8,
            'Space': 4.5
        }.get(key, 1)
        width += int(key_w * w_mult) + gap
    return width - gap

# ---------------- DRAW KEYBOARD ----------------
def draw_keyboard(frame):
    global caps_mode
    boxes = []

    h_frame, w_frame, _ = frame.shape
    scale_x = w_frame / 1280
    scale_y = h_frame / 720

    key_w, key_h = int(85 * scale_x), int(70 * scale_y)
    gap = int(8 * scale_x)
    start_y = int(230 * scale_y)

    for r, row in enumerate(layout):
        y = start_y + r * (key_h + gap)

        # ✅ CENTER EACH ROW
        row_width = get_row_width(row, key_w, gap)
        x = (w_frame - row_width) // 2

        for key in row:
            w_mult = {
                'Backspace': 1.5,
                'Tab': 1.2,
                'Caps': 1.4,
                'Enter': 1.7,
                'Shift': 1.8,
                'Space': 4.5
            }.get(key, 1)

            w = int(key_w * w_mult)

            # Highlight Caps when ON
            if key == 'Caps' and caps_mode:
                cv2.rectangle(frame, (x, y), (x + w, y + key_h), (0, 255, 0), -1)

            cv2.rectangle(frame, (x, y), (x + w, y + key_h), (255, 255, 255), 2)

            # Letter display logic
            if len(key) == 1 and key.isalpha():
                text = key.upper() if caps_mode else key.lower()
            else:
                text = ' ' if key == 'Space' else key

            font_scale = 0.7 * scale_x
            font_thickness = max(1, int(2 * scale_x))
            cv2.putText(
                frame, text,
                (x + int(10 * scale_x), y + int(45 * scale_y)),
                FONT, font_scale, (255, 255, 255), font_thickness
            )

            boxes.append((x, y, x + w, y + key_h, key))
            x += w + gap

    return boxes

def get_key(x, y, boxes):
    for (x1, y1, x2, y2, key) in boxes:
        if x1 <= x <= x2 and y1 <= y <= y2:
            return key, (x1, y1, x2, y2)
    return None, None

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

# ---------------- MAIN LOOP ----------------
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    boxes = draw_keyboard(frame)

    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
        h, w, _ = frame.shape
        lm = hand.landmark

        index_tip = (int(lm[8].x * w), int(lm[8].y * h))
        thumb_tip = (int(lm[4].x * w), int(lm[4].y * h))

        cv2.circle(frame, index_tip, 10, (0, 255, 0), -1)
        cv2.circle(frame, thumb_tip, 10, (0, 0, 255), -1)
        cv2.line(frame, index_tip, thumb_tip, (255, 0, 0), 2)

        hovered_key, box = get_key(index_tip[0], index_tip[1], boxes)
        if hovered_key:
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

            d = distance(index_tip, thumb_tip)
            if d < CLICK_THRESHOLD and (time.time() - last_click_time > CLICK_COOLDOWN):
                last_click_time = time.time()

                if hovered_key == 'Backspace':
                    pyautogui.press('backspace')
                    typed_text = typed_text[:-1]

                elif hovered_key == 'Space':
                    pyautogui.press('space')
                    typed_text += ' '

                elif hovered_key == 'Enter':
                    pyautogui.press('enter')
                    typed_text += '\n'

                elif hovered_key == 'Caps':
                    caps_mode = not caps_mode

                elif hovered_key in ['Shift', 'Ctrl', 'Alt', 'Tab', 'Fn', 'Menu', 'Win']:
                    pyautogui.press(hovered_key.lower())

                else:
                    if len(hovered_key) == 1 and hovered_key.isalpha():
                        char = hovered_key.upper() if caps_mode else hovered_key.lower()
                        pyautogui.write(char)
                        typed_text += char
                    else:
                        pyautogui.press(hovered_key.lower())
                        typed_text += hovered_key

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), -1)

    # ---------------- Text Display ----------------
    h_frame, w_frame, _ = frame.shape
    cv2.rectangle(
        frame,
        (int(40 * (w_frame / 1280)), int(50 * (h_frame / 720))),
        (int(1220 * (w_frame / 1280)), int(150 * (h_frame / 720))),
        (0, 0, 0), -1
    )

    font_scale_text = 1.2 * (w_frame / 1280)
    thickness_text = max(1, int(3 * (w_frame / 1280)))
    cv2.putText(
        frame, typed_text[-80:],
        (int(60 * (w_frame / 1280)), int(120 * (h_frame / 720))),
        FONT, font_scale_text, (255, 255, 255), thickness_text
    )

    # ---------------- FULLSCREEN WINDOW ----------------
    frame_resized = cv2.resize(frame, (1920, 1080))
    cv2.namedWindow("Laptop Gesture Keyboard", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(
        "Laptop Gesture Keyboard",
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )
    cv2.imshow("Laptop Gesture Keyboard", frame_resized)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()