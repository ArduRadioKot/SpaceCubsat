import cv2
import numpy as np
import serial
import time
import base64
import io
from PIL import Image

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIN_AREA_RATIO = 0.01 
MAX_AREA_RATIO = 0.6

SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600

class SatelliteController:
    def __init__(self):
        self.serial_conn = None
        self.camera = None
        self.frame_count = 0
        
    def initialize_camera(self):
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        
        if not self.camera.isOpened():
            print("Ошибка камеры")
            return False
        return True
    
    def initialize_serial(self):
        try:
            self.serial_conn = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            print("Serial connection established")
            return True
        except Exception as e:
            print(f"Serial connection failed: {e}")
            return False
    
    def detect_oil_spill(self, frame):
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
        return detected, mask, area_ratio
    
    def frame_to_bytes(self, frame):
        resized = cv2.resize(frame, (320, 240))
        
        _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buffer.tobytes()
    
    def send_image_to_arduino(self, frame):
        try:
            image_bytes = self.frame_to_bytes(frame)
            
            self.serial_conn.write(b"IMAGE_START:\n")
            time.sleep(0.01)
            
            chunk_size = 64
            for i in range(0, len(image_bytes), chunk_size):
                chunk = image_bytes[i:i+chunk_size]
                hex_data = chunk.hex()
                self.serial_conn.write(f"IMAGE_DATA:{hex_data}\n".encode())
                time.sleep(0.005) 

            self.serial_conn.write(b"IMAGE_END\n")
            time.sleep(0.01)
            
            print(f"Image sent: {len(image_bytes)} bytes")
            return True
            
        except Exception as e:
            print(f"Error sending image: {e}")
            return False
    
    def send_zone_alert(self, area_ratio, frame_count):
        try:
            alert_msg = f"ZONE_DETECTED:Oil spill detected, area ratio: {area_ratio:.4f}, frame: {frame_count}\n"
            self.serial_conn.write(alert_msg.encode())
            print(f"Zone alert sent: {alert_msg.strip()}")
        except Exception as e:
            print(f"Error sending zone alert: {e}")
    
    def listen_for_commands(self):
        try:
            if self.serial_conn.in_waiting > 0:
                command = self.serial_conn.readline().decode().strip()
                if command:
                    print(f"Received command: {command}")
                    self.process_command(command)
        except Exception as e:
            print(f"Error reading command: {e}")
    
    def process_command(self, command):
        if command.startswith("ROTATE:"):
            parts = command.split(":")
            if len(parts) == 2:
                coords = parts[1].split(",")
                if len(coords) == 3:
                    x, y, z = map(int, coords)
                    print(f"Rotating satellite: X={x}, Y={y}, Z={z}")
                    
        elif command == "TAKE_PHOTO":
            ret, frame = self.camera.read()
            if ret:
                self.send_image_to_arduino(frame)
                
        elif command == "SYSTEM_RESET":
            print("System reset command received")
    
    def run(self):
        if not self.initialize_camera():
            return
        
        if not self.initialize_serial():
            print("Running without serial connection")
        
        print("SIT-Space Satellite Detection System Ready")
        
        last_detection_time = 0
        detection_cooldown = 5  
        
        try:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                self.frame_count += 1
                detected, mask, area_ratio = self.detect_oil_spill(frame)
                
                if detected:
                    current_time = time.time()
                    if current_time - last_detection_time > detection_cooldown:
                        cv2.putText(frame, "OIL SPILL DETECTED",
                                  (20, 40),
                                  cv2.FONT_HERSHEY_SIMPLEX,
                                  1, (0, 0, 255), 2)
                        
                        if self.serial_conn:
                            self.send_zone_alert(area_ratio, self.frame_count)
                            self.send_image_to_arduino(frame)
                        
                        last_detection_time = current_time
                else:
                    cv2.putText(frame, "Monitoring...",
                              (20, 40),
                              cv2.FONT_HERSHEY_SIMPLEX,
                              0.7, (0, 255, 0), 2)
                
                cv2.putText(frame, f"Frame: {self.frame_count}",
                          (20, FRAME_HEIGHT - 60),
                          cv2.FONT_HERSHEY_SIMPLEX,
                          0.5, (255, 255, 255), 1)
                
                cv2.putText(frame, f"Area Ratio: {area_ratio:.4f}",
                          (20, FRAME_HEIGHT - 40),
                          cv2.FONT_HERSHEY_SIMPLEX,
                          0.5, (255, 255, 255), 1)
                
                cv2.putText(frame, f"Status: {'DETECTED' if detected else 'CLEAR'}",
                          (20, FRAME_HEIGHT - 20),
                          cv2.FONT_HERSHEY_SIMPLEX,
                          0.5, (0, 255, 0) if not detected else (0, 0, 255), 1)
                cv2.imshow("SIT-Space Satellite View", frame)
                cv2.imshow("Detection Mask", mask)
                if self.serial_conn:
                    self.listen_for_commands()
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                if self.frame_count % 900 == 0 and self.serial_conn:  # ~30 seconds at 30fps
                    self.send_image_to_arduino(frame)
        
        except KeyboardInterrupt:
            print("\nShutting down...")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        if self.camera:
            self.camera.release()
        if self.serial_conn:
            self.serial_conn.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    controller = SatelliteController()
    controller.run()