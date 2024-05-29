import cv2
import time
import numpy as np
from ultralytics import YOLO
import pygame

# Initialize pygame for playing the alarm sound
pygame.mixer.init()
alarm_sound = 'static/alarm/alarm.mp3'

# Load the YOLOv8 model with tracking support
model = YOLO('model/031924.pt')

# Dictionary to hold car information
car_dict = {}

# Function to play the alarm sound
def Auto_alarm():
    if not pygame.mixer.music.get_busy():  # Check if the alarm is not already playing
        pygame.mixer.music.load(alarm_sound)
        pygame.mixer.music.play()

# Function to update car information with elapsed time
def update_car_info(car_id, elapsed_time):
    car_dict[car_id] = f"ID: {car_id} | Time: {elapsed_time:.2f}s"

# Function to reset car information
def reset_car_info(car_id):
    car_dict[car_id] = f"ID: {car_id} | Time: 0s"

# Function to check if the car is within the zone
def is_within_zone(center, zone):
    zone_polygon = np.array(zone, np.int32)
    return cv2.pointPolygonTest(zone_polygon, center, False) >= 0

# Function to detect and track cars
def detect_and_track_cars(frame, model, zone, active_cars, timers, alarms):
    results = model.track(source=frame, tracker='bytetrack.yaml')
    
    # Extract the tracked objects from the results
    tracked_objects = results[0].boxes.xywh.cpu().numpy()  # Convert results to numpy array
    ids = results[0].boxes.id.cpu().numpy()  # Get the IDs of detected objects

    current_car_ids = set()
    current_time = time.time()

    # Draw the zone
    # cv2.polylines(frame, [np.array(zone, np.int32)], isClosed=True, color=(255, 0, 0, 10), thickness=2)

    for i, (x, y, w, h) in enumerate(tracked_objects):
        car_id = int(ids[i])  # Use the tracking ID provided by the tracker
        car_center = (int(x), int(y))
        x1, y1, x2, y2 = int(x - w/2), int(y - h/2), int(x + w/2), int(y + h/2)
        center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)  # Calculate center coordinates
        
        # Check if car is within the zone
        if is_within_zone(car_center, zone):
            if car_id not in active_cars:
                timers[car_id] = current_time
                active_cars.add(car_id)
                alarms[car_id] = False  # Initialize alarm status

            elapsed_time = current_time - timers[car_id]
            update_car_info(car_id, elapsed_time)

            # Trigger alarm if the car stays in the zone for more than 3 minutes
            if elapsed_time > 30:  # 180 seconds = 3 minutes
                Auto_alarm()
                alarms[car_id] = True  # Mark this alarm as triggered
        else:
            if car_id in active_cars:
                reset_car_info(car_id)
                active_cars.remove(car_id)
                if car_id in timers:
                    del timers[car_id]
                if car_id in alarms:
                    del alarms[car_id]
            else:
                reset_car_info(car_id)  # Display time as 0 if not in the zone

        current_car_ids.add(car_id)

        # Draw bounding box and ID
        if car_id in car_dict:
            cv2.putText(frame, car_dict[car_id], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)  # Draw a red point at the center

    # Remove cars that are no longer detected
    for car_id in list(car_dict.keys()):
        if car_id not in current_car_ids:
            reset_car_info(car_id)
            if car_id in active_cars:
                active_cars.remove(car_id)
            if car_id in timers:
                del timers[car_id]
            if car_id in alarms:
                del alarms[car_id]

    return frame

# Define the dropoff zone coordinates (x1, y1, x2, y2, x3, y3, x4, y4)
zone = [(690, 380), (750, 390), (640, 475), (530, 460)]

# Set of active car IDs that are currently in the zone
active_cars = set()

# Dictionary to hold start time for each car
timers = {}

# Dictionary to track alarm status for each car
alarms = {}

# Capture video from a file or camera
cap = cv2.VideoCapture('static/video/c2.mp4')  # or use 0 for webcam

# Set window size
window_width, window_height = 800, 600
winame = "AI DROPOFF ZONE"
cv2.namedWindow(winame, cv2.WINDOW_NORMAL)
cv2.resizeWindow(winame, window_width, window_height)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = detect_and_track_cars(frame, model, zone, active_cars, timers, alarms)

    cv2.imshow(winame, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
