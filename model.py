import cv2
import time
from ultralytics import YOLO
import numpy as np

# Load the YOLOv8 model with tracking support
model = YOLO('model/031924.pt')

# Dictionary to hold car information
mobil_dict = {}

def update_car_info(mobil_id, elapsed_time):
    mobil_dict[mobil_id] = f"ID: {mobil_id} | Time: {elapsed_time:.2f}s"

def reset_car_info(mobil_id):
    mobil_dict[mobil_id] = f"ID: {mobil_id} | Time: 0s"

def AIDropoff_zone(frame, model, active_cars, timers, zone):
    results = model.track(source=frame, tracker='bytetrack.yaml')
    
    # Extract the tracked objects from the results
    tracked_objects = results[0].boxes.xywh.cpu().numpy()  # Convert results to numpy array
    ids = results[0].boxes.id.cpu().numpy()  # Get the IDs of detected objects

    current_mobil_ids = set()
    current_time = time.time()
    
    # Draw the zone
    cv2.polylines(frame, [np.array(zone, np.int32)], isClosed=True, color=(0, 0, 255), thickness=2)

    for i, (x, y, w, h) in enumerate(tracked_objects):
        mobil_id = int(ids[i])  # Use the tracking ID provided by the tracker
        car_center = (int(x), int(y))
        x1, y1, x2, y2 = int(x - w/2), int(y - h/2), int(x + w/2), int(y + h/2)
        center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)  # Calculate center coordinates
        
        # Check if car is within the zone
        if is_within_zone(car_center, zone):
            if mobil_id not in active_cars:
                timers[mobil_id] = current_time
                active_cars.add(mobil_id)
            elapsed_time = current_time - timers[mobil_id]
            update_car_info(mobil_id, elapsed_time)
        else:
            if mobil_id in active_cars:
                reset_car_info(mobil_id)
                active_cars.remove(mobil_id)
                if mobil_id in timers:
                    del timers[mobil_id]
            else:
                reset_car_info(mobil_id)  # Display time as 0 if not in the zone

        current_mobil_ids.add(mobil_id)

        # Draw bounding box and ID
        if mobil_id in mobil_dict:
            cv2.putText(frame, mobil_dict[mobil_id], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 2)
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)  # Draw a red point at the center

    # Remove cars that are no longer detected
    for mobil_id in list(mobil_dict.keys()):
        if mobil_id not in current_mobil_ids:
            reset_car_info(mobil_id)
            if mobil_id in active_cars:
                active_cars.remove(mobil_id)
            if mobil_id in timers:
                del timers[mobil_id]

    return frame

def is_within_zone(center, zone):
    zone_polygon = np.array(zone, np.int32)
    return cv2.pointPolygonTest(zone_polygon, center, False) >= 0

# Define the dropoff zone coordinates (x1, y1, x2, y2, x3, y3, x4, y4)
zone = [(690, 380), (750, 390), (640, 475), (530, 460)]

# Set of active car IDs that are currently in the zone
active_cars = set()

# Dictionary to hold start time for each car
timers = {}

# Capture video from a file or camera
cap = cv2.VideoCapture('static/video/c2.mp4')  # or use 0 for webcam

# Set window size
window_width, window_height = 800, 600
winname = 'AI Dropoff-zone'
cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
cv2.resizeWindow(winname, window_width, window_height)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = AIDropoff_zone(frame, model, active_cars, timers, zone)

    cv2.imshow(winname, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
