import cv2
import numpy as np

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

MIN_AREA_RATIO = 0.01 
MAX_AREA_RATIO = 0.6    

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    print("Ошибка камеры")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_blur = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    sat_mask = cv2.inRange(s, 0, 60)

    val_mask = cv2.inRange(v, 40, 180)

    hsv_mask = cv2.bitwise_and(sat_mask, val_mask)

    b, g, r = cv2.split(frame_blur)
    rb_index = (r.astype(np.float32) - b.astype(np.float32)) / (r + b + 1)

    rb_mask = cv2.inRange(rb_index, -0.2, 0.2)
    mask = cv2.bitwise_and(hsv_mask, rb_mask)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    oil_pixels = cv2.countNonZero(mask)
    total_pixels = FRAME_WIDTH * FRAME_HEIGHT
    area_ratio = oil_pixels / total_pixels

    detected = MIN_AREA_RATIO < area_ratio < MAX_AREA_RATIO

    if detected:
        cv2.putText(frame, "OIL SPILL POSSIBLE",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
