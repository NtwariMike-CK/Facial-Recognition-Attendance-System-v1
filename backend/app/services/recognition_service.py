# the original file
# app/services/recognition_service.py
import threading
import time
import os
import signal
import sys
from datetime import datetime, timedelta, timezone
import zoneinfo
import numpy as np
import cv2
import face_recognition
import dlib
from scipy.spatial import distance as dist
import requests
import base64
import json
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import CameraSettings, Employee, AttendanceRecord
import asyncio
from threading import Lock
import io


KIGALI_TZ = zoneinfo.ZoneInfo("Africa/Kigali")

class RecognitionService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RecognitionService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        
        self.initialized = True
        self.is_running = False
        self.recognition_thread = None
        self.stop_event = threading.Event()
        
        # Database session - will be created per thread
        self.company = None
        
        # Facial recognition setup
        self.detector = None
        self.predictor = None
        
        # Face data
        self.known_face_encodings = []
        self.known_face_names = []
        self.employee_data = {}
        
        # Tracking variables
        self.person_blink_count = {}
        self.eye_closed_frames = {}
        self.last_detection_time = {}
        # Store employee IDs instead of database objects
        self.attendance_employee_ids = {}
        
        # Configuration
        self.BLINK_THRESHOLD = 5
        self.BLINK_DURATION_THRESHOLD = 3
        self.CHECKOUT_DELAY_MINUTES = 2
        
        # Camera
        self.video_capture = None
        self.camera_source = "0"
        self.camera_type = "Webcam"
        
        # Preview window control
        self.show_preview = True

        # streaming
        self.frame_lock = Lock()
        self.latest_frame = None
        self.streaming_clients = set()
    
    def get_current_time(self):
        """Get current time with KIGALI_TZ awareness - consistent across the app"""
        return datetime.now(KIGALI_TZ)
    
    def make_timezone_aware(self, dt):
        """Convert naive datetime to timezone-aware datetime"""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=KIGALI_TZ)
        return dt
    
    def get_db_session(self):
        """Create a new database session for the current thread"""
        return SessionLocal()
    
    def initialize_recognition(self, company: str, db: Session):
        """Initialize the recognition system with company data"""
        try:
            self.company = company
            
            # Initialize dlib components
            self.detector = dlib.get_frontal_face_detector()
            predictor_path = os.path.join(os.path.dirname(__file__), 'shape_predictor_68_face_landmarks.dat')
            if not os.path.exists(predictor_path):
                # Try alternative paths
                predictor_path = 'shape_predictor_68_face_landmarks.dat'
                if not os.path.exists(predictor_path):
                    predictor_path = os.path.join(os.getcwd(), 'shape_predictor_68_face_landmarks.dat')
            
            if os.path.exists(predictor_path):
                self.predictor = dlib.shape_predictor(predictor_path)
            else:
                raise FileNotFoundError("shape_predictor_68_face_landmarks.dat not found. Please download it from dlib website.")
            
            # Load company settings and employee data
            self.load_settings_and_employees(db)
            
            print(f"Recognition system initialized for company: {company}")
            return True
            
        except Exception as e:
            print(f"Error initializing recognition: {e}")
            return False

    def load_settings_and_employees(self, db: Session):
        """Load camera settings and employee data from database"""
        try:
            # Get camera settings
            settings = db.query(CameraSettings).filter(
                CameraSettings.company == self.company
            ).first()
            
            if settings:
                self.BLINK_THRESHOLD = int(settings.blinking_threshold)
                self.camera_source = settings.camera_source
                self.camera_type = settings.camera_type
            
            # Get employees with images
            employees = db.query(Employee).filter(
                Employee.company == self.company,
                Employee.image_path.isnot(None)
            ).all()
            
            # Load face encodings
            self.known_face_encodings = []
            self.known_face_names = []
            self.employee_data = {}
            
            for employee in employees:
                if employee.image_path:
                    try:
                        # Convert binary image data to numpy array
                        image_data = np.frombuffer(employee.image_path, np.uint8)
                        
                        # Decode image using OpenCV
                        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                        
                        if image is not None:
                            # Convert BGR to RGB for face_recognition library
                            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                            
                            # Create face encoding
                            encodings = face_recognition.face_encodings(rgb_image)
                            
                            if encodings:
                                self.known_face_encodings.append(encodings[0])
                                self.known_face_names.append(employee.name)
                                self.employee_data[employee.name] = {
                                    'id': employee.id,
                                    'name': employee.name,
                                    'email': employee.email,
                                    'department': employee.department
                                }
                                print(f"Loaded face encoding for {employee.name}")
                            else:
                                print(f"No face found in image for {employee.name}")
                        else:
                            print(f"Failed to decode image for {employee.name}")
                            
                    except Exception as e:
                        print(f"Error processing image for {employee.name}: {e}")
        
            print(f"Loaded {len(self.known_face_names)} employee face encodings")
            
            # Create initial attendance records
            self.create_initial_attendance_records(db)
        
        except Exception as e:
            print(f"Error loading settings and employees: {e}")

    def create_initial_attendance_records(self, db: Session):
        """Create attendance records for all employees with status 'absent'"""
        try:
            current_date = datetime.now(KIGALI_TZ).date()
            print(f"Creating attendance records for date: {current_date}")
            print(f"Employee data available: {list(self.employee_data.keys())}")
            
            for employee_name, employee_info in self.employee_data.items():
                try:
                    # Check if record already exists for today
                    existing_record = db.query(AttendanceRecord).filter(
                        AttendanceRecord.employee_id == employee_info['id'],
                        AttendanceRecord.date >= current_date,
                        AttendanceRecord.date < current_date + timedelta(days=1)
                    ).first()
                    
                    if not existing_record:
                        # Create new attendance record with only basic info
                        new_record = AttendanceRecord(
                            employee_id=employee_info['id'],
                            name=employee_name,
                            camera_used=self.camera_type,
                            company=self.company,
                            status="absent",
                            date=current_date
                        )
                        
                        db.add(new_record)
                        # Store employee ID instead of database object
                        self.attendance_employee_ids[employee_name] = employee_info['id']
                        print(f"Created new attendance record for {employee_name}")
                    else:
                        self.attendance_employee_ids[employee_name] = employee_info['id']
                        print(f"Found existing attendance record for {employee_name} - Status: {existing_record.status}")
                        
                except Exception as e:
                    print(f"Error creating record for {employee_name}: {e}")
                    continue
            
            # Commit all records at once
            db.commit()
            print(f"Successfully created/loaded attendance records for {len(self.attendance_employee_ids)} employees")
                
        except Exception as e:
            print(f"Error creating attendance records: {e}")
            db.rollback()
            raise

    def debug_attendance_status(self):
        """Debug method to check attendance records status"""
        print("=== ATTENDANCE DEBUG INFO ===")
        print(f"Total employee IDs: {len(self.attendance_employee_ids)}")
        
        # Create a new session to check current status
        db = self.get_db_session()
        try:
            for name, employee_id in self.attendance_employee_ids.items():
                current_date = datetime.now(KIGALI_TZ).date()
                record = db.query(AttendanceRecord).filter(
                    AttendanceRecord.employee_id == employee_id,
                    AttendanceRecord.date >= current_date,
                    AttendanceRecord.date < current_date + timedelta(days=1)
                ).first()
                
                if record:
                    print(f"""
    Employee: {name}
    - ID: {record.employee_id}
    - Status: {record.status}
    - Arrival: {record.arrival_time}
    - Departure: {record.departure_time}
    - Hours: {record.hours_worked}
    - Date: {record.date}
    - Company: {record.company}
                    """)
        finally:
            db.close()
        
        print(f"Blink counts: {self.person_blink_count}")
        print(f"Last detection times: {self.last_detection_time}")
        print("=== END DEBUG INFO ===")
    
    def eye_aspect_ratio(self, eye):
        """Calculate eye aspect ratio for blink detection"""
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink(self, shape, name):
        """Detect blink for liveness verification"""
        left_eye = shape[36:42]
        right_eye = shape[42:48]
        
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0
        
        if name not in self.eye_closed_frames:
            self.eye_closed_frames[name] = 0
        
        if ear < 0.25:  # Eyes closed
            self.eye_closed_frames[name] += 1
        else:  # Eyes open
            if 1 <= self.eye_closed_frames[name] <= self.BLINK_DURATION_THRESHOLD:
                self.person_blink_count[name] = self.person_blink_count.get(name, 0) + 1
            self.eye_closed_frames[name] = 0
        
        return self.person_blink_count.get(name, 0) >= self.BLINK_THRESHOLD
    
    def update_attendance_record(self, employee_name: str, action: str):
        """Update attendance record in database using a new session"""
        db = self.get_db_session()
        try:
            print(f"Attempting to update attendance: {employee_name} - {action}")
            
            employee_id = self.attendance_employee_ids.get(employee_name)
            if not employee_id:
                print(f"No employee ID found for {employee_name}")
                return False
            
            # Get fresh record from database
            current_date = datetime.now(KIGALI_TZ).date()
            record = db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.date >= current_date,
                AttendanceRecord.date < current_date + timedelta(days=1)
            ).first()
            
            if not record:
                print(f"No attendance record found for {employee_name}")
                return False
            
            # Use timezone-aware current time
            current_time = self.get_current_time()
            print(f"Current time: {current_time}")
            print(f"Record current state - Arrival: {record.arrival_time}, Departure: {record.departure_time}, Status: {record.status}")
            
            if action == "checkin" and not record.arrival_time:
                # Update check-in time and status
                record.arrival_time = current_time
                record.status = "present"
                self.last_detection_time[employee_name] = current_time
                
                try:
                    db.commit()
                    print(f"✓ {employee_name} checked in at {current_time.strftime('%H:%M:%S')}")
                    return True
                except Exception as e:
                    print(f"Error committing check-in for {employee_name}: {e}")
                    db.rollback()
                    return False
                    
            elif action == "checkout" and record.arrival_time and not record.departure_time:
                # Check if enough time has passed since last detection
                last_time = self.last_detection_time.get(employee_name)
                print(f"Last detection time for {employee_name}: {last_time}")
                
                if last_time:
                    # Ensure both times are timezone-aware for comparison
                    last_time_aware = self.make_timezone_aware(last_time)
                    time_diff = (current_time - last_time_aware).total_seconds()
                    
                    if time_diff < self.CHECKOUT_DELAY_MINUTES * 60:
                        print(f"Too soon for checkout. Only {int(time_diff)} seconds passed")
                        return False
                
                # Calculate hours worked with timezone-aware times
                arrival_time_aware = self.make_timezone_aware(record.arrival_time)
                hours_worked = (current_time - arrival_time_aware).total_seconds() / 3600
                
                record.departure_time = current_time
                record.hours_worked = round(hours_worked, 2)
                
                try:
                    db.commit()
                    print(f"✓ {employee_name} checked out at {current_time.strftime('%H:%M:%S')} - Hours: {record.hours_worked}")
                    return True
                except Exception as e:
                    print(f"Error committing check-out for {employee_name}: {e}")
                    db.rollback()
                    return False
            
            else:
                if action == "checkin":
                    print(f"Check-in ignored - {employee_name} already has arrival time: {record.arrival_time}")
                elif action == "checkout":
                    if not record.arrival_time:
                        print(f"Check-out ignored - {employee_name} hasn't checked in yet")
                    elif record.departure_time:
                        print(f"Check-out ignored - {employee_name} already checked out at: {record.departure_time}")
                
                return False
                    
        except Exception as e:
            print(f"Error updating attendance for {employee_name}: {e}")
            db.rollback()
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    def enhance_low_light(self, frame):
        """Enhance frame for low-light conditions"""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl,a,b))
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        return enhanced_bgr
    
    def draw_detection_info(self, frame, face_locations, face_names, confidences, blink_counts):
        """Draw detection information on frame"""
        # Create a temporary database session to check attendance status
        db = self.get_db_session()
        try:
            current_date = datetime.now(KIGALI_TZ).date()
            
            for (top, right, bottom, left), name, confidence, blink_count in zip(
                face_locations, face_names, confidences, blink_counts
            ):
                # Scale back up face locations
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Determine colors based on recognition status
                if name != "Unknown":
                    color = (0, 255, 0)
                    employee_id = self.attendance_employee_ids.get(name)
                    if employee_id:
                        record = db.query(AttendanceRecord).filter(
                            AttendanceRecord.employee_id == employee_id,
                            AttendanceRecord.date >= current_date,
                            AttendanceRecord.date < current_date + timedelta(days=1)
                        ).first()
                        
                        if record and record.arrival_time:
                            status = "Checked In"
                            status_color = (0, 255, 0)
                        else:
                            status = f"Blinks: {blink_count}/{self.BLINK_THRESHOLD}"
                            status_color = (0, 165, 255)
                    else:
                        status = f"Blinks: {blink_count}/{self.BLINK_THRESHOLD}"
                        status_color = (0, 165, 255)
                else:
                    color = (0, 0, 255)
                    status = "Unknown Person"
                    status_color = (0, 0, 255)
                
                # Draw face rectangle
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw label background
                label_height = 60
                cv2.rectangle(frame, (left, bottom - label_height), (right, bottom), color, cv2.FILLED)
                
                # Draw name
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 35), font, 0.6, (255, 255, 255), 1)
                
                # Draw confidence or status
                if name != "Unknown":
                    cv2.putText(frame, f"Conf: {confidence:.2f}", (left + 6, bottom - 20), font, 0.4, (255, 255, 255), 1)
                    cv2.putText(frame, status, (left + 6, bottom - 6), font, 0.4, status_color, 1)
                else:
                    cv2.putText(frame, status, (left + 6, bottom - 6), font, 0.4, (255, 255, 255), 1)
        finally:
            db.close()
        
        # Draw system info
        info_text = [
            f"Company: {self.company}",
            f"Employees Loaded: {len(self.known_face_names)}",
            f"Camera: {self.camera_type}",
            f"Blink Threshold: {self.BLINK_THRESHOLD}",
            "Press 'q' to stop recognition"
        ]
        
        y_offset = 30
        for i, text in enumerate(info_text):
            cv2.putText(frame, text, (10, y_offset + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def recognition_loop(self):
        """Updated recognition loop that saves frames for streaming"""
        try:
            # Initialize camera with DirectShow backend
            if self.camera_source.isdigit():
                self.video_capture = cv2.VideoCapture(int(self.camera_source), cv2.CAP_DSHOW)
            else:
                self.video_capture = cv2.VideoCapture(self.camera_source, cv2.CAP_DSHOW)
            
            if not self.video_capture.isOpened():
                print("Error: Cannot open camera")
                return
            
            # Set camera properties
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.video_capture.set(cv2.CAP_PROP_FPS, 30)
            self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            print("Recognition started - Backend handling camera")
            frame_count = 0
            
            while not self.stop_event.is_set():
                ret, frame = self.video_capture.read()
                if not ret:
                    print("Error reading frame")
                    continue
                
                frame_count += 1
                process_frame = frame_count % 2 == 0
                
                if process_frame:
                    # Your existing face recognition logic here
                    enhanced_frame = self.enhance_low_light(frame)
                    small_frame = cv2.resize(enhanced_frame, (0,0), fx=0.25, fy=0.25)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    
                    # Find faces and process recognition
                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
                    # ... your face recognition logic ...
                    face_names = []
                    confidences = []
                    blink_counts = []
                    
                    # Process detected faces
                    for face_encoding in face_encodings:
                        # Compare with known faces
                        matches = face_recognition.compare_faces(
                            self.known_face_encodings, face_encoding, tolerance=0.6
                        )
                        face_distances = face_recognition.face_distance(
                            self.known_face_encodings, face_encoding
                        )
                        
                        name = "Unknown"
                        confidence = 0
                        blink_count = 0
                        
                        if len(face_distances) > 0:
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = self.known_face_names[best_match_index]
                                confidence = 1 - face_distances[best_match_index]
                                blink_count = self.person_blink_count.get(name, 0)
                                
                                # Process recognized face with good confidence
                                if confidence > 0.4:
                                    # Detect blinks for liveness
                                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                    rects = self.detector(gray, 0)
                                    
                                    for rect in rects:
                                        shape = self.predictor(gray, rect)
                                        shape = np.array([[p.x, p.y] for p in shape.parts()])
                                        
                                        # Check if person has blinked enough
                                        if self.detect_blink(shape, name):
                                            # Use thread-safe database access
                                            employee_id = self.attendance_employee_ids.get(name)
                                            if employee_id:
                                                # Check current status to decide action
                                                db = self.get_db_session()
                                                try:
                                                    current_date = datetime.now(KIGALI_TZ).date()
                                                    record = db.query(AttendanceRecord).filter(
                                                        AttendanceRecord.employee_id == employee_id,
                                                        AttendanceRecord.date >= current_date,
                                                        AttendanceRecord.date < current_date + timedelta(days=1)
                                                    ).first()
                                                    
                                                    if record:
                                                        if not record.arrival_time:
                                                            self.update_attendance_record(name, "checkin")
                                                        elif not record.departure_time:
                                                            self.update_attendance_record(name, "checkout")
                                                finally:
                                                    db.close()
                        
                        face_names.append(name)
                        confidences.append(confidence)
                        blink_counts.append(blink_count)

                    # Draw detection info on frame
                    display_frame = self.draw_detection_info(
                        frame.copy(), face_locations, face_names, confidences, blink_counts
                    )
                    
                    # Save frame for streaming (thread-safe)
                    with self.frame_lock:
                        self.latest_frame = display_frame.copy()
                
                time.sleep(0.03)
                
        except Exception as e:
            print(f"Error in recognition loop: {e}")
        finally:
            if self.video_capture:
                self.video_capture.release()
            print("Recognition loop stopped")
    
    def get_latest_frame(self):
        """Get the latest processed frame for streaming"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None
    
    def start_recognition(self, company: str, db: Session, show_preview: bool = True):
        """Start the recognition system"""
        if self.is_running:
            return {"error": "Recognition system is already running"}
        
        try:
            self.show_preview = show_preview
            
            # Initialize the system
            if not self.initialize_recognition(company, db):
                return {"error": "Failed to initialize recognition system"}
            
            # Reset stop event
            self.stop_event.clear()
            
            # Start recognition thread
            self.recognition_thread = threading.Thread(target=self.recognition_loop)
            self.recognition_thread.daemon = True
            self.recognition_thread.start()
            
            self.is_running = True
            return {"message": "Recognition system started successfully", "status": "active"}
            
        except Exception as e:
            return {"error": f"Failed to start recognition: {str(e)}"}
    
    def stop_recognition(self):
        """Stop the recognition system"""
        if not self.is_running:
            return {"error": "Recognition system is not running"}
        
        try:
            # Signal stop
            self.stop_event.set()
            
            # Wait for thread to finish (with timeout)
            if self.recognition_thread and self.recognition_thread.is_alive():
                self.recognition_thread.join(timeout=5)
            
            # Close video capture
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
            
            # Close any OpenCV windows
            cv2.destroyAllWindows()
            
            # Reset state
            self.is_running = False
            self.recognition_thread = None
            
            return {"message": "Recognition system stopped successfully", "status": "inactive"}
            
        except Exception as e:
            return {"error": f"Failed to stop recognition: {str(e)}"}
    
    def get_status(self):
        """Get current status of recognition system"""
        return {
            "is_running": self.is_running,
            "company": self.company,
            "employees_loaded": len(self.known_face_names),
            "camera_source": self.camera_source,
            "camera_type": self.camera_type
        }

# Global instance
recognition_service = RecognitionService()