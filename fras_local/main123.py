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

from config import Config
# from recognition_engine import LocalRecognitionEngine
from recognition_service import RecognitionService
from database_client import DatabaseClient

class LocalRecognitionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FRAS Local Recognition System")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.config = Config()
        self.db_client = DatabaseClient(self.config)
        self.recognition_engine = None
        self.is_running = False
        self.current_token = None
        self.current_company = None
        
        # GUI variables
        self.video_label = None
        self.status_label = None
        self.employee_count_label = None
        
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
        self.refresh_button.grid(row=0, column=2)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N), padx=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Status: Not logged in")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.employee_count_label = ttk.Label(status_frame, text="Employees: 0")
        self.employee_count_label.grid(row=1, column=0, sticky=tk.W)
        
        self.company_label = ttk.Label(status_frame, text="Company: None")
        self.company_label.grid(row=2, column=0, sticky=tk.W)
        
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
    
    def login(self):
        """Handle admin login"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        self.log_message("Attempting login...")
        self.log_message(f"Using API URL: {self.config.API_BASE_URL}")
        
        # Attempt login
        result = self.db_client.login(email, password)
        
        if result["success"]:
            self.current_token = result["token"]
            self.current_company = result["company"]
            
            # Update GUI
            self.status_label.config(text="Status: Logged in")
            self.company_label.config(text=f"Company: {self.current_company}")
            
            # Enable buttons
            self.start_button.config(state="normal")
            self.refresh_button.config(state="normal")
            self.login_button.config(state="disabled")
            
            self.log_message(f"Successfully logged in to {self.current_company}")
            
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
        
        # Get employees data
        employees = self.db_client.get_employees()
        if employees:
            self.employee_count_label.config(text=f"Employees: {len(employees)}")
            self.log_message(f"Loaded {len(employees)} employees")
        
        # Get camera settings
        settings = self.db_client.get_camera_settings()
        if settings:
            self.log_message("Camera settings loaded")
    
    def start_recognition(self):
        """Start the recognition system"""
        if self.is_running:
            return
        
        if not self.current_token:
            messagebox.showerror("Error", "Please login first")
            return
        
        self.log_message("Starting recognition system...")
        
        try:
            # Initialize recognition engine
            self.recognition_engine = LocalRecognitionEngine(
                self.db_client, 
                self.current_token, 
                self.current_company
            )
            
            # Load data
            if not self.recognition_engine.initialize():
                messagebox.showerror("Error", "Failed to initialize recognition system")
                return
            
            # Start recognition in separate thread
            self.recognition_thread = threading.Thread(target=self.recognition_worker)
            self.recognition_thread.daemon = True
            self.recognition_thread.start()
            
            self.is_running = True
            
            # Update GUI
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Status: Recognition running")
            
            self.log_message("Recognition system started successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recognition: {str(e)}")
            self.log_message(f"Error starting recognition: {str(e)}")
    
    def stop_recognition(self):
        """Stop the recognition system"""
        if not self.is_running:
            return
        
        self.log_message("Stopping recognition system...")
        
        self.is_running = False
        
        if self.recognition_engine:
            self.recognition_engine.stop()
        
        # Update GUI
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Status: Recognition stopped")
        
        # Clear video feed
        self.video_label.config(image="", text="Camera feed will appear here")
        
        self.log_message("Recognition system stopped")
    
    def recognition_worker(self):
        """Worker thread for recognition processing"""
        try:
            while self.is_running and self.recognition_engine:
                frame, detections = self.recognition_engine.process_frame()
                
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
                
                # Log detections
                for detection in detections:
                    self.root.after(0, self.log_message, detection)
                    
        except Exception as e:
            self.root.after(0, self.log_message, f"Recognition error: {str(e)}")
    
    def update_video_display(self, frame_tk):
        """Update video display in main thread"""
        self.video_label.config(image=frame_tk, text="")
        self.video_label.image = frame_tk  # Keep a reference
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            self.stop_recognition()
        
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
        self.root.mainloop()

if __name__ == "__main__":
    app = LocalRecognitionApp()
    app.run()