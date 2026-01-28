import cv2
import numpy as np
import tensorflow as tf

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIN_AREA_RATIO = 0.01
MAX_AREA_RATIO = 0.6
ROI_SIZE = 64

interpreter = tf.lite.Interpreter(model_path="trained_model.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def predict_cnn(roi):
    roi_resized = cv2.resize(roi, (ROI_SIZE, ROI_SIZE))
    roi_resized = roi_resized.astype(np.float32) / 255.0
    roi_resized = np.expand_dims(roi_resized, axis=0)
    interpreter.set_tensor(input_details[0]['index'], roi_resized)
    interpreter.invoke()
    return interpreter.get_tensor(output_details[0]['index'])[0][0]

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_blur = cv2.GaussianBlur(frame, (5,5), 0)
    hsv = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    sat_mask = cv2.inRange(s, 0, 60)
    val_mask = cv2.inRange(v, 40, 180)
    hsv_mask = cv2.bitwise_and(sat_mask, val_mask)
    b, g, r = cv2.split(frame_blur)
    rb_index = (r.astype(np.float32) - b.astype(np.float32)) / (r + b + 1)
    rb_mask = cv2.inRange(rb_index, -0.2, 0.2)
    mask = cv2.bitwise_and(hsv_mask, rb_mask)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total_pixels = FRAME_WIDTH * FRAME_HEIGHT

    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        area_ratio = (w*h) / total_pixels
        if area_ratio < MIN_AREA_RATIO or area_ratio > MAX_AREA_RATIO:
            continue
        roi = frame[y:y+h, x:x+w]
        p = predict_cnn(roi)
        if p > 0.5:
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,0,255), 2)
            cv2.putText(frame, "OIL!", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
