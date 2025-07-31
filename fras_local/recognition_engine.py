# local_recognition/recognition_engine.py
import cv2
import face_recognition
import numpy as np
import dlib
from scipy.spatial import distance as dist
import base64
import io
from PIL import Image
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Tuple, Optional
import logging
import zoneinfo

logger = logging.getLogger(__name__)

KIGALI_TZ = zoneinfo.ZoneInfo("Africa/Kigali")

class LocalRecognitionEngine:
    """Local facial recognition engine that connects to deployed database"""
    
    def __init__(self, db_client, token: str, company: str):
        self.db_client = db_client
        self.token = token
        self.company = company
        
        # Face recognition data
        self.known_face_encodings = []
        self.known_face_names = []
        self.employee_data = {}
        
        # Camera
        self.video_capture = None
        self.camera_source = 0
        self.camera_type = "Webcam"
        
        # Tracking variables (matching backend logic)
        self.person_blink_count = {}
        self.eye_closed_frames = {}
        self.last_detection_time = {}
        self.attendance_employee_ids = {}  # Store employee IDs like backend
        
        # Configuration (loaded from server)
        self.BLINK_THRESHOLD = 5
        self.BLINK_DURATION_THRESHOLD = 3  # Added from backend
        self.CHECKOUT_DELAY_MINUTES = 2
        self.face_tolerance = 0.6
        
        # Dlib components for blink detection
        self.detector = None
        self.predictor = None
        
        # Threading and preview control
        self.is_running = False
        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.recognition_thread = None
        self.stop_event = threading.Event()
        self.show_preview = True
        
    def get_current_time(self):
        """Get current time with KIGALI_TZ awareness - consistent with backend"""
        return datetime.now(KIGALI_TZ)
    
    def make_timezone_aware(self, dt):
        """Convert naive datetime to timezone-aware datetime - from backend"""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=KIGALI_TZ)
        return dt
    
    def initialize(self) -> bool:
        """Initialize the recognition system"""
        try:
            logger.info("Initializing local recognition engine...")
            
            # Initialize dlib components
            self.detector = dlib.get_frontal_face_detector()
            
            try:
                self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
            except Exception as e:
                logger.error(f"Failed to load face landmarks model: {e}")
                logger.error("Please download shape_predictor_68_face_landmarks.dat from dlib website")
                return False
            
            # Load camera settings from server
            settings = self.db_client.get_camera_settings()
            if settings:
                self.BLINK_THRESHOLD = int(settings.get("blinking_threshold", 5))
                camera_source = settings.get("camera_source", "0")
                self.camera_source = int(camera_source) if camera_source.isdigit() else camera_source
                self.camera_type = settings.get("camera_type", "Webcam")
                logger.info(f"Loaded camera settings: source={self.camera_source}, blink_threshold={self.BLINK_THRESHOLD}")
            
            # Load employee data and images
            if not self.load_employee_data():
                return False
            
            # Initialize camera
            if not self.initialize_camera():
                return False
            
            # Create initial attendance records (like backend)
            self.create_initial_attendance_records()
            
            logger.info("Recognition engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize recognition engine: {e}")
            return False
    
    def create_initial_attendance_records(self):
        """Create attendance records for all employees with status 'absent' - matching backend logic"""
        try:
            current_date = datetime.now(KIGALI_TZ).date()
            logger.info(f"Creating attendance records for date: {current_date}")
            logger.info(f"Employee data available: {list(self.employee_data.keys())}")
            
            for employee_name, employee_info in self.employee_data.items():
                try:
                    # Check if record already exists for today via API
                    today_data = self.db_client.get_today_attendance()
                    existing_record = None
                    
                    if today_data and "records" in today_data:
                        for record in today_data["records"]:
                            if record.get("name") == employee_name:
                                existing_record = record
                                break
                    
                    if not existing_record:
                        # Create new attendance record with only basic info
                        attendance_data = {
                            "employee_id": employee_info['id'],
                            "status": "absent",
                            "camera_used": self.camera_type
                        }
                        
                        if self.db_client.create_attendance_record(attendance_data):
                            # Store employee ID instead of database object (like backend)
                            self.attendance_employee_ids[employee_name] = employee_info['id']
                            logger.info(f"Created new attendance record for {employee_name}")
                        else:
                            logger.error(f"Failed to create attendance record for {employee_name}")
                    else:
                        self.attendance_employee_ids[employee_name] = employee_info['id']
                        logger.info(f"Found existing attendance record for {employee_name} - Status: {existing_record.get('status', 'unknown')}")
                        
                except Exception as e:
                    logger.error(f"Error creating record for {employee_name}: {e}")
                    continue
            
            logger.info(f"Successfully created/loaded attendance records for {len(self.attendance_employee_ids)} employees")
                
        except Exception as e:
            logger.error(f"Error creating attendance records: {e}")
            raise
    
    def debug_system_status(self):
        """Debug method to check system status and help troubleshoot issues"""
        logger.info("=== SYSTEM DEBUG INFO ===")
        logger.info(f"Recognition engine initialized: {hasattr(self, 'detector') and self.detector is not None}")
        logger.info(f"Face predictor loaded: {hasattr(self, 'predictor') and self.predictor is not None}")
        logger.info(f"Camera initialized: {self.video_capture is not None and self.video_capture.isOpened() if self.video_capture else False}")
        logger.info(f"Camera source: {self.camera_source}")
        logger.info(f"Camera type: {self.camera_type}")
        logger.info(f"Known employees: {len(self.known_face_names)}")
        logger.info(f"Employee names: {self.known_face_names}")
        logger.info(f"Face encodings loaded: {len(self.known_face_encodings)}")
        logger.info(f"Attendance records: {len(self.attendance_employee_ids)}")
        logger.info(f"Blink threshold: {self.BLINK_THRESHOLD}")
        logger.info(f"Face tolerance: {self.face_tolerance}")
        logger.info(f"Is running: {self.is_running}")
        logger.info(f"Company: {self.company}")
        
        # Test camera frame capture
        if self.video_capture and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                logger.info(f"Camera frame test: SUCCESS - Shape: {frame.shape}")
            else:
                logger.error("Camera frame test: FAILED - Cannot read frame")
        else:
            logger.error("Camera not available for testing")
        
        # Test face recognition on a simple frame
        try:
            if self.video_capture and self.video_capture.isOpened():
                ret, test_frame = self.video_capture.read()
                if ret:
                    rgb_frame = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_frame)
                    logger.info(f"Face detection test: Found {len(face_locations)} faces in current frame")
                else:
                    logger.error("Cannot capture test frame for face detection test")
        except Exception as e:
            logger.error(f"Face detection test failed: {e}")
        
        logger.info("=== END DEBUG INFO ===")

    def debug_attendance_status(self):
        """Debug method to check attendance records status - from backend"""
        logger.info("=== ATTENDANCE DEBUG INFO ===")
        logger.info(f"Total employee IDs: {len(self.attendance_employee_ids)}")
        
        try:
            today_data = self.db_client.get_today_attendance()
            if today_data and "records" in today_data:
                for record in today_data["records"]:
                    name = record.get("name", "Unknown")
                    logger.info(f"""
    Employee: {name}
    - ID: {record.get('employee_id')}
    - Status: {record.get('status')}
    - Arrival: {record.get('arrival_time')}
    - Departure: {record.get('departure_time')}
    - Hours: {record.get('hours_worked')}
    - Company: {record.get('company')}
                    """)
        except Exception as e:
            logger.error(f"Error in debug: {e}")
        
        logger.info(f"Blink counts: {self.person_blink_count}")
        logger.info(f"Last detection times: {self.last_detection_time}")
        logger.info("=== END DEBUG INFO ===")
    
    def eye_aspect_ratio(self, eye):
        """Calculate eye aspect ratio for blink detection"""
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink(self, shape, name):
        """Detect blink for liveness verification - matching backend logic"""
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
            # Use BLINK_DURATION_THRESHOLD like backend
            if 1 <= self.eye_closed_frames[name] <= self.BLINK_DURATION_THRESHOLD:
                self.person_blink_count[name] = self.person_blink_count.get(name, 0) + 1
            self.eye_closed_frames[name] = 0
        
        return self.person_blink_count.get(name, 0) >= self.BLINK_THRESHOLD
    
    def update_attendance_record(self, employee_name: str, action: str) -> bool:
        """Update attendance record via API - matching backend logic"""
        try:
            logger.info(f"Attempting to update attendance: {employee_name} - {action}")
            
            employee_id = self.attendance_employee_ids.get(employee_name)
            if not employee_id:
                logger.error(f"No employee ID found for {employee_name}")
                return False
            
            # Get fresh record from API
            today_data = self.db_client.get_today_attendance()
            record = None
            
            if today_data and "records" in today_data:
                for r in today_data["records"]:
                    if r.get("name") == employee_name:
                        record = r
                        break
            
            if not record:
                logger.error(f"No attendance record found for {employee_name}")
                return False
            
            # Use timezone-aware current time
            current_time = self.get_current_time()
            logger.info(f"Current time: {current_time}")
            logger.info(f"Record current state - Arrival: {record.get('arrival_time')}, Departure: {record.get('departure_time')}, Status: {record.get('status')}")
            
            if action == "checkin" and not record.get("arrival_time"):
                # Update check-in time and status
                attendance_data = {
                    "employee_id": employee_id,
                    "arrival_time": current_time.isoformat(),
                    "status": "present",
                    "camera_used": self.camera_type
                }
                
                if self.db_client.create_attendance_record(attendance_data):
                    self.last_detection_time[employee_name] = current_time
                    logger.info(f"✓ {employee_name} checked in at {current_time.strftime('%H:%M:%S')}")
                    return True
                else:
                    logger.error(f"Failed to create check-in record for {employee_name}")
                    return False
                    
            elif action == "checkout" and record.get("arrival_time") and not record.get("departure_time"):
                # Check if enough time has passed since last detection
                last_time = self.last_detection_time.get(employee_name)
                logger.info(f"Last detection time for {employee_name}: {last_time}")
                
                if last_time:
                    # Ensure both times are timezone-aware for comparison
                    last_time_aware = self.make_timezone_aware(last_time)
                    time_diff = (current_time - last_time_aware).total_seconds()
                    
                    if time_diff < self.CHECKOUT_DELAY_MINUTES * 60:
                        logger.info(f"Too soon for checkout. Only {int(time_diff)} seconds passed")
                        return False
                
                # Calculate hours worked with timezone-aware times
                arrival_time_str = record.get("arrival_time")
                if arrival_time_str:
                    # Parse the arrival time from ISO format
                    arrival_time = datetime.fromisoformat(arrival_time_str.replace('Z', '+00:00'))
                    arrival_time_aware = self.make_timezone_aware(arrival_time)
                    hours_worked = (current_time - arrival_time_aware).total_seconds() / 3600
                    
                    # Create checkout record
                    attendance_data = {
                        "employee_id": employee_id,
                        "arrival_time": arrival_time_str,
                        "departure_time": current_time.isoformat(),
                        "hours_worked": round(hours_worked, 2),
                        "status": "present",
                        "camera_used": self.camera_type
                    }
                    
                    if self.db_client.create_attendance_record(attendance_data):
                        logger.info(f"✓ {employee_name} checked out at {current_time.strftime('%H:%M:%S')} - Hours: {round(hours_worked, 2)}")
                        return True
                    else:
                        logger.error(f"Failed to create check-out record for {employee_name}")
                        return False
            
            else:
                if action == "checkin":
                    logger.info(f"Check-in ignored - {employee_name} already has arrival time: {record.get('arrival_time')}")
                elif action == "checkout":
                    if not record.get("arrival_time"):
                        logger.info(f"Check-out ignored - {employee_name} hasn't checked in yet")
                    elif record.get("departure_time"):
                        logger.info(f"Check-out ignored - {employee_name} already checked out at: {record.get('departure_time')}")
                
                return False
                    
        except Exception as e:
            logger.error(f"Error updating attendance for {employee_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
        """Draw detection information on frame - matching backend logic but optimized for local display"""
        try:
            # Get current attendance status (like backend)
            today_data = self.db_client.get_today_attendance()
            attendance_status = {}
            
            if today_data and "records" in today_data:
                for record in today_data["records"]:
                    name = record.get("name")
                    if name:
                        attendance_status[name] = record
            
            # Draw face detection boxes and info
            for (top, right, bottom, left), name, confidence, blink_count in zip(
                face_locations, face_names, confidences, blink_counts
            ):
                # Scale back up face locations (since we processed on smaller frame)
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Determine colors and status based on recognition
                if name != "Unknown":
                    color = (0, 255, 0)  # Green for recognized faces
                    record = attendance_status.get(name, {})
                    
                    if record.get("arrival_time") and not record.get("departure_time"):
                        status = "Checked In"
                        status_color = (0, 255, 0)  # Green
                    elif record.get("departure_time"):
                        status = "Checked Out"
                        status_color = (255, 165, 0)  # Orange
                    else:
                        status = f"Blinks: {blink_count}/{self.BLINK_THRESHOLD}"
                        status_color = (0, 165, 255)  # Light blue
                else:
                    color = (0, 0, 255)  # Red for unknown faces
                    status = "Unknown Person"
                    status_color = (0, 0, 255)  # Red
                
                # Draw face rectangle with thicker border for better visibility
                cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
                
                # Draw label background with better size
                label_height = 70
                cv2.rectangle(frame, (left, bottom - label_height), (right, bottom), color, cv2.FILLED)
                
                # Draw name with better font size
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 45), font, 0.7, (255, 255, 255), 2)
                
                # Draw confidence and status
                if name != "Unknown":
                    cv2.putText(frame, f"Conf: {confidence:.2f}", (left + 6, bottom - 25), font, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, status, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 2)
                else:
                    cv2.putText(frame, status, (left + 6, bottom - 25), font, 0.5, (255, 255, 255), 2)
        
        except Exception as e:
            logger.error(f"Error getting attendance status for display: {e}")
            # Still draw face boxes even if we can't get attendance status
            for (top, right, bottom, left), name, confidence, blink_count in zip(
                face_locations, face_names, confidences, blink_counts
            ):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
                
                label_height = 50
                cv2.rectangle(frame, (left, bottom - label_height), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 15), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        # Draw system info (like backend but with local-specific info)
        info_text = [
            f"Company: {self.company}",
            f"Employees Loaded: {len(self.known_face_names)}",
            f"Camera: {self.camera_type} ({self.camera_source})",
            f"Blink Threshold: {self.BLINK_THRESHOLD}",
            f"Time: {self.get_current_time().strftime('%H:%M:%S')}",
            "Press 'q' to stop recognition"
        ]
        
        # Draw info with background for better visibility
        info_y_start = 25
        for i, text in enumerate(info_text):
            y_pos = info_y_start + i * 30
            # Draw background rectangle for text
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (5, y_pos - 20), (text_size[0] + 15, y_pos + 5), (0, 0, 0), cv2.FILLED)
            cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def recognition_loop(self):
        """Main recognition loop with camera preview - similar to backend recognition_service.py"""
        try:
            logger.info("Starting recognition loop with camera preview...")
            frame_count = 0
            
            while not self.stop_event.is_set():
                ret, frame = self.video_capture.read()
                if not ret:
                    logger.error("Error reading frame from camera")
                    continue
                
                frame_count += 1
                # Process every other frame for performance (like backend)
                process_frame = frame_count % 2 == 0
                display_frame = frame.copy()
                
                if process_frame:
                    try:
                        # Enhance frame for better recognition
                        enhanced_frame = self.enhance_low_light(frame)
                        
                        # Resize for faster processing (like backend)
                        small_frame = cv2.resize(enhanced_frame, (0, 0), fx=0.25, fy=0.25)
                        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                        
                        # Find faces and process recognition (matching backend logic)
                        face_locations = face_recognition.face_locations(rgb_small_frame)
                        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                        
                        face_names = []
                        confidences = []
                        blink_counts = []
                        
                        # Process detected faces (matching backend)
                        for face_encoding in face_encodings:
                            # Compare with known faces
                            matches = face_recognition.compare_faces(
                                self.known_face_encodings, face_encoding, tolerance=self.face_tolerance
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
                                    
                                    # Process recognized face with good confidence (like backend)
                                    if confidence > 0.4:
                                        # Detect blinks for liveness using original frame
                                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                        rects = self.detector(gray, 0)
                                        
                                        for rect in rects:
                                            shape = self.predictor(gray, rect)
                                            shape = np.array([[p.x, p.y] for p in shape.parts()])
                                            
                                            # Check if person has blinked enough
                                            if self.detect_blink(shape, name):
                                                # Use thread-safe database access (like backend)
                                                employee_id = self.attendance_employee_ids.get(name)
                                                if employee_id:
                                                    # Check current status to decide action (matching backend logic)
                                                    try:
                                                        today_data = self.db_client.get_today_attendance()
                                                        record = None
                                                        
                                                        if today_data and "records" in today_data:
                                                            for r in today_data["records"]:
                                                                if r.get("name") == name:
                                                                    record = r
                                                                    break
                                                        
                                                        if record:
                                                            if not record.get("arrival_time"):
                                                                if self.update_attendance_record(name, "checkin"):
                                                                    logger.info(f"✓ {name} checked in successfully")
                                                                    # Reset blink count after successful check-in
                                                                    self.person_blink_count[name] = 0
                                                            elif not record.get("departure_time"):
                                                                if self.update_attendance_record(name, "checkout"):
                                                                    logger.info(f"✓ {name} checked out successfully")
                                                                    # Reset blink count after successful check-out
                                                                    self.person_blink_count[name] = 0
                                                    except Exception as e:
                                                        logger.error(f"Error accessing attendance data for {name}: {e}")
                            
                            face_names.append(name)
                            confidences.append(confidence)
                            blink_counts.append(blink_count)

                        # Draw detection info on frame (matching backend draw_detection_info)
                        display_frame = self.draw_detection_info(
                            frame.copy(), face_locations, face_names, confidences, blink_counts
                        )
                        
                        # Store frame for other uses (thread-safe like backend)
                        with self.frame_lock:
                            self.latest_frame = display_frame.copy()
                    
                    except Exception as e:
                        logger.error(f"Error processing frame: {e}")
                        import traceback
                        traceback.print_exc()
                        # Use original frame if processing fails
                        with self.frame_lock:
                            self.latest_frame = frame.copy()
                else:
                    # For non-processed frames, use latest processed frame or raw frame
                    with self.frame_lock:
                        if self.latest_frame is not None:
                            display_frame = self.latest_frame.copy()
                        else:
                            display_frame = frame.copy()
                
                # Show camera preview locally (this is what backend doesn't have)
                if self.show_preview:
                    try:
                        cv2.imshow('Face Recognition - Local Preview', display_frame)
                        
                        # Check for 'q' key press to stop
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q'):
                            logger.info("Stop requested by user (pressed 'q')")
                            self.stop_event.set()
                            break
                    except Exception as e:
                        logger.error(f"Error showing preview: {e}")
                
                # Small delay to prevent excessive CPU usage (like backend)
                time.sleep(0.03)
                
        except Exception as e:
            logger.error(f"Error in recognition loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if self.video_capture:
                self.video_capture.release()
            cv2.destroyAllWindows()
            logger.info("Recognition loop stopped and cleanup completed")
    
    def start_recognition(self, show_preview: bool = True):
        """Start the recognition system with camera preview"""
        if self.is_running:
            logger.warning("Recognition system is already running")
            return False
        
        try:
            logger.info("Starting recognition system...")
            self.show_preview = show_preview
            
            # Verify camera is initialized
            if not self.video_capture or not self.video_capture.isOpened():
                logger.error("Camera not initialized or not opened")
                return False
            
            # Test camera by reading a frame
            ret, test_frame = self.video_capture.read()
            if not ret:
                logger.error("Cannot read from camera")
                return False
            logger.info(f"Camera test successful - Frame size: {test_frame.shape}")
            
            # Verify we have employees loaded
            if len(self.known_face_names) == 0:
                logger.error("No employee face encodings loaded")
                return False
            logger.info(f"Ready to recognize {len(self.known_face_names)} employees")
            
            # Reset stop event
            self.stop_event.clear()
            
            # Start recognition thread
            self.recognition_thread = threading.Thread(target=self.recognition_loop, daemon=True)
            self.recognition_thread.start()
            
            self.is_running = True
            logger.info("Recognition system started successfully")
            
            if show_preview:
                logger.info("Camera preview will be shown - Press 'q' in the camera window to stop")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recognition: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_frame(self) -> Tuple[Optional[np.ndarray], List[str]]:
        """Process single frame and return frame with detections and detection messages"""
        if not self.video_capture or not self.video_capture.isOpened():
            return None, []
        
        ret, frame = self.video_capture.read()
        if not ret:
            return None, ["Error: Could not read frame from camera"]
        
        detections = []
        
        try:
            # Enhance frame for better recognition
            enhanced_frame = self.enhance_low_light(frame)
            
            # Resize for faster processing
            small_frame = cv2.resize(enhanced_frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            face_names = []
            confidences = []
            blink_counts = []
            
            # Process each detected face
            for face_encoding in face_encodings:
                # Compare with known faces
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, face_encoding, tolerance=self.face_tolerance
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
                                    # Check current status to decide action (like backend)
                                    employee_id = self.attendance_employee_ids.get(name)
                                    if employee_id:
                                        # Get current attendance status
                                        today_data = self.db_client.get_today_attendance()
                                        record = None
                                        
                                        if today_data and "records" in today_data:
                                            for r in today_data["records"]:
                                                if r.get("name") == name:
                                                    record = r
                                                    break
                                        
                                        if record:
                                            if not record.get("arrival_time"):
                                                if self.update_attendance_record(name, "checkin"):
                                                    detections.append(f"✓ {name} checked in successfully")
                                                    # Reset blink count after successful check-in
                                                    self.person_blink_count[name] = 0
                                            elif not record.get("departure_time"):
                                                if self.update_attendance_record(name, "checkout"):
                                                    detections.append(f"✓ {name} checked out successfully")
                                                    # Reset blink count after successful check-out
                                                    self.person_blink_count[name] = 0
                
                face_names.append(name)
                confidences.append(confidence)
                blink_counts.append(blink_count)
            
            # Draw detection info on frame
            display_frame = self.draw_detection_info(
                frame.copy(), face_locations, face_names, confidences, blink_counts
            )
            
            # Store frame for display
            with self.frame_lock:
                self.latest_frame = display_frame.copy()
            
            return display_frame, detections
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame, [f"Error: {str(e)}"]
    
    def get_latest_frame(self):
        """Get the latest processed frame for streaming"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None
    
    def stop(self):
        """Stop the recognition engine"""
        logger.info("Stopping recognition engine...")
        self.is_running = False
        
        # Signal stop event
        self.stop_event.set()
        
        # Wait for recognition thread to finish
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=5)
        
        # Close camera
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        # Close OpenCV windows
        cv2.destroyAllWindows()
        
        logger.info("Recognition engine stopped")
    
    def load_employee_data(self) -> bool:
        """Load employee data and face encodings from server"""
        try:
            employee_images = self.db_client.get_employee_images()
            if not employee_images:
                logger.error("No employee images found")
                return False
            
            self.known_face_encodings = []
            self.known_face_names = []
            self.employee_data = {}
            
            for emp_data in employee_images:
                try:
                    name = emp_data["employee_name"]
                    employee_id = emp_data["employee_id"]
                    image_base64 = emp_data["image_base64"]
                    
                    if not image_base64:
                        logger.warning(f"No image data for {name}")
                        continue
                    
                    # Decode base64 image
                    image_data = base64.b64decode(image_base64)
                    image = Image.open(io.BytesIO(image_data))
                    image_np = np.array(image)
                    
                    # Convert to RGB if needed
                    if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                        image_rgb = image_np
                    else:
                        image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
                    
                    # Get face encodings
                    encodings = face_recognition.face_encodings(image_rgb)
                    
                    if encodings:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_names.append(name)
                        self.employee_data[name] = {
                            'id': employee_id,
                            'name': name
                        }
                        logger.info(f"Loaded face encoding for {name} (ID: {employee_id})")
                    else:
                        logger.warning(f"No face found in image for {name}")
                        
                except Exception as e:
                    logger.error(f"Error processing employee {emp_data.get('employee_name', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Loaded {len(self.known_face_names)} employee face encodings")
            return len(self.known_face_names) > 0
            
        except Exception as e:
            logger.error(f"Failed to load employee data: {e}")
            return False
    
    def initialize_camera(self) -> bool:
        """Initialize camera capture - matching backend camera setup"""
        try:
            # Use DirectShow backend like backend for Windows
            if isinstance(self.camera_source, int):
                self.video_capture = cv2.VideoCapture(self.camera_source, cv2.CAP_DSHOW)
            else:
                if self.camera_source.isdigit():
                    self.video_capture = cv2.VideoCapture(int(self.camera_source), cv2.CAP_DSHOW)
                else:
                    self.video_capture = cv2.VideoCapture(self.camera_source, cv2.CAP_DSHOW)
            
            if not self.video_capture.isOpened():
                logger.error(f"Cannot open camera: {self.camera_source}")
                # Try without DirectShow backend as fallback
                if isinstance(self.camera_source, int):
                    self.video_capture = cv2.VideoCapture(self.camera_source)
                else:
                    self.video_capture = cv2.VideoCapture(int(self.camera_source) if self.camera_source.isdigit() else self.camera_source)
                
                if not self.video_capture.isOpened():
                    logger.error(f"Cannot open camera even without DirectShow: {self.camera_source}")
                    return False
            
            # Set camera properties (matching backend)
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.video_capture.set(cv2.CAP_PROP_FPS, 30)
            self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test frame capture
            ret, test_frame = self.video_capture.read()
            if not ret:
                logger.error("Cannot read test frame from camera")
                return False
            
            logger.info(f"Camera initialized successfully: {self.camera_source}")
            logger.info(f"Frame size: {test_frame.shape[1]}x{test_frame.shape[0]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def get_status(self):
        """Get current status of recognition system"""
        return {
            "is_running": self.is_running,
            "company": self.company,
            "employees_loaded": len(self.known_face_names),
            "camera_source": self.camera_source,
            "camera_type": self.camera_type,
            "blink_threshold": self.BLINK_THRESHOLD,
            "face_tolerance": self.face_tolerance
        }