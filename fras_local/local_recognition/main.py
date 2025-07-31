# local_recognition/main.py
import sys
import os
import asyncio
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import cv2
from PIL import Image, ImageTk
import requests
import json
from typing import Optional
import logging

from config import Config
from recognition_service import RecognitionService, recognition_service
from database_client import DatabaseClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalRecognitionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FRAS Local Recognition System")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.config = Config()
        self.db_client = DatabaseClient(self.config)
        self.recognition_service = recognition_service  # Use global singleton
        self.is_running = False
        self.current_token = None
        self.current_company = None
        
        # GUI variables
        self.video_label = None
        self.status_label = None
        self.employee_count_label = None
        
        # Video update variables
        self.video_update_thread = None
        self.stop_video_update = threading.Event()
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the main GUI"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Login section
        login_frame = ttk.LabelFrame(main_frame, text="Login", padding="10")
        login_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(login_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.email_entry = ttk.Entry(login_frame, width=30)
        self.email_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(login_frame, text="Password:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.password_entry = ttk.Entry(login_frame, width=30, show="*")
        self.password_entry.grid(row=0, column=3, padx=(0, 10))
        
        self.login_button = ttk.Button(login_frame, text="Login", command=self.login)
        self.login_button.grid(row=0, column=4)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Recognition Control", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Recognition", 
                                     command=self.start_recognition, state="disabled")
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Recognition", 
                                    command=self.stop_recognition, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.refresh_button = ttk.Button(control_frame, text="Refresh Data", 
                                       command=self.refresh_data, state="disabled")
        self.refresh_button.grid(row=0, column=2, padx=(0, 10))
        
        self.debug_button = ttk.Button(control_frame, text="Debug Status", 
                                     command=self.debug_system, state="disabled")
        self.debug_button.grid(row=0, column=3)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N), padx=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Status: Not logged in")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.employee_count_label = ttk.Label(status_frame, text="Employees: 0")
        self.employee_count_label.grid(row=1, column=0, sticky=tk.W)
        
        self.company_label = ttk.Label(status_frame, text="Company: None")
        self.company_label.grid(row=2, column=0, sticky=tk.W)
        
        self.camera_label = ttk.Label(status_frame, text="Camera: Not initialized")
        self.camera_label.grid(row=3, column=0, sticky=tk.W)
        
        self.blink_label = ttk.Label(status_frame, text="Blink Threshold: 5")
        self.blink_label.grid(row=4, column=0, sticky=tk.W)
        
        # Video section
        video_frame = ttk.LabelFrame(main_frame, text="Camera Feed", padding="10")
        video_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.video_label = ttk.Label(video_frame, text="Camera feed will appear here")
        self.video_label.grid(row=0, column=0)
        
        # Activity log section
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
    
    def log_message(self, message: str):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status_display(self):
        """Update the status display with current recognition service status"""
        status = self.recognition_service.get_status()
        
        # Update labels
        if status["is_running"]:
            self.status_label.config(text="Status: Recognition running")
        elif status["authenticated"]:
            self.status_label.config(text="Status: Ready to start")
        else:
            self.status_label.config(text="Status: Not authenticated")
        
        self.employee_count_label.config(text=f"Employees: {status['employees_loaded']}")
        self.company_label.config(text=f"Company: {status.get('company', 'None')}")
        self.camera_label.config(text=f"Camera: {status.get('camera_type', 'Not initialized')} ({status.get('camera_source', 'N/A')})")
        self.blink_label.config(text=f"Blink Threshold: {status.get('blink_threshold', 5)}")
    
    def login(self):
        """Handle admin login"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        self.log_message("Attempting login...")
        self.log_message(f"Using API URL: {self.config.API_BASE_URL}")
        
        # Set database client in recognition service
        self.recognition_service.set_database_client(self.db_client)
        
        # Attempt authentication through recognition service
        result = self.recognition_service.authenticate(email, password)
        
        if result["success"]:
            self.current_token = result["token"]
            self.current_company = result["company"]
            
            # Enable buttons
            self.start_button.config(state="normal")
            self.refresh_button.config(state="normal")
            self.debug_button.config(state="normal")
            self.login_button.config(state="disabled")
            
            self.log_message(f"Successfully logged in to {self.current_company}")
            
            # Update status display
            self.update_status_display()
            
            # Load initial data
            self.refresh_data()
            
        else:
            messagebox.showerror("Login Failed", result["message"])
            self.log_message(f"Login failed: {result['message']}")
    
    def refresh_data(self):
        """Refresh employees and camera settings data"""
        if not self.current_token:
            return
        
        self.log_message("Refreshing data from server...")
        
        try:
            # Get employees data
            employees = self.db_client.get_employees()
            if employees:
                self.log_message(f"Loaded {len(employees)} employees from server")
            
            # Get camera settings
            settings = self.db_client.get_camera_settings()
            if settings:
                self.log_message("Camera settings loaded from server")
            
            # Update status display
            self.update_status_display()
            
        except Exception as e:
            self.log_message(f"Error refreshing data: {str(e)}")
    
    def debug_system(self):
        """Debug system status"""
        if not self.current_token:
            messagebox.showwarning("Warning", "Please login first")
            return
        
        self.log_message("=== SYSTEM DEBUG ===")
        
        # Get recognition service status
        status = self.recognition_service.get_status()
        for key, value in status.items():
            self.log_message(f"{key}: {value}")
        
        # Run attendance debug if available
        if hasattr(self.recognition_service, 'debug_attendance_status'):
            self.recognition_service.debug_attendance_status()
        
        self.log_message("=== DEBUG COMPLETE ===")
    
    def start_recognition(self):
        """Start the recognition system"""
        if self.is_running:
            return
        
        if not self.current_token:
            messagebox.showerror("Error", "Please login first")
            return
        
        self.log_message("Starting recognition system...")
        
        try:
            # Start recognition with preview
            result = self.recognition_service.start_recognition(show_preview=True)
            
            if result.get("error"):
                messagebox.showerror("Error", result["error"])
                self.log_message(f"Error starting recognition: {result['error']}")
                return
            
            self.is_running = True
            
            # Update GUI
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            
            self.log_message("Recognition system started successfully")
            self.log_message("Camera preview window should be visible - Press 'q' in camera window to stop")
            
            # Start video update thread for GUI display
            self.start_video_updates()
            
            # Update status display
            self.update_status_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recognition: {str(e)}")
            self.log_message(f"Error starting recognition: {str(e)}")
    
    def stop_recognition(self):
        """Stop the recognition system"""
        if not self.is_running:
            return
        
        self.log_message("Stopping recognition system...")
        
        # Stop video updates
        self.stop_video_updates()
        
        # Stop recognition service
        result = self.recognition_service.stop_recognition()
        
        if result.get("error"):
            self.log_message(f"Error stopping recognition: {result['error']}")
        else:
            self.log_message("Recognition system stopped successfully")
        
        self.is_running = False
        
        # Update GUI
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        # Clear video feed
        self.video_label.config(image="", text="Camera feed will appear here")
        
        # Update status display
        self.update_status_display()
    
    def start_video_updates(self):
        """Start video update thread for GUI display"""
        self.stop_video_update.clear()
        self.video_update_thread = threading.Thread(target=self.video_update_worker, daemon=True)
        self.video_update_thread.start()
    
    def stop_video_updates(self):
        """Stop video update thread"""
        self.stop_video_update.set()
        if self.video_update_thread and self.video_update_thread.is_alive():
            self.video_update_thread.join(timeout=2)
    
    def video_update_worker(self):
        """Worker thread for updating video display in GUI"""
        try:
            while not self.stop_video_update.is_set() and self.is_running:
                # Get latest frame from recognition service
                frame = self.recognition_service.get_latest_frame()
                
                if frame is not None:
                    # Convert frame for tkinter display
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_pil = Image.fromarray(frame_rgb)
                    
                    # Resize for display
                    display_size = (800, 600)
                    frame_pil.thumbnail(display_size, Image.Resampling.LANCZOS)
                    
                    frame_tk = ImageTk.PhotoImage(frame_pil)
                    
                    # Update GUI (thread-safe)
                    self.root.after(0, self.update_video_display, frame_tk)
                
                # Small delay
                threading.Event().wait(0.1)
                    
        except Exception as e:
            logger.error(f"Video update error: {e}")
    
    def update_video_display(self, frame_tk):
        """Update video display in main thread"""
        if self.is_running:  # Only update if still running
            self.video_label.config(image=frame_tk, text="")
            self.video_label.image = frame_tk  # Keep a reference
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            self.stop_recognition()
        
        # Stop video updates
        self.stop_video_updates()
        
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        # Check configuration
        config_issues = self.config.validate_config()
        if config_issues:
            self.log_message("Configuration issues found:")
            for issue in config_issues:
                self.log_message(f"  - {issue}")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.log_message("Local Recognition System started")
        self.log_message("Please login with your admin credentials")
        self.log_message("After starting recognition, a camera preview window will appear")
        self.root.mainloop()

if __name__ == "__main__":
    app = LocalRecognitionApp()
    app.run()