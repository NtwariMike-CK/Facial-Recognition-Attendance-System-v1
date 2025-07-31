📘 FRAS – Facial Recognition Attendance System
🔍 Overview
FRAS is a web-based application designed for companies to automate employee attendance tracking using facial recognition. Admins can manage employees, monitor attendance, and handle employee queries through tickets, while employees can view their records and communicate issues. It separates attendance management into two components:
A hosted web application for registration, settings, tracking, and analytics.


A local recognition module that detects faces in real-time using a webcam/IP camera and updates the server.



🧱 System Overview
Component
Description
Web Frontend
Next.js frontend hosted on Vercel
Backend API
FastAPI REST API hosted on Render/Railway
Local Recognition
Python script using OpenCV, dlib, face_recognition
Database
PostgreSQL database





👤 User Roles
Admin


Registers company account


Adds/manages employees and uploads passport-style images


Sets camera/liveness/working hour settings


Runs local facial recognition system


Manages attendance dashboard and support tickets


Employee


Logs in using credentials provided by the admin


Views personal attendance


Submits tickets regarding issues




🔄 Workflow Summary
Admin signs up and logs in to the web app


Admin adds employees and configures camera/liveness settings


Admin runs the local recognition app (Python) on a computer with a webcam


Facial recognition detects and records attendance to the backend


Admin/Employee use the web dashboard to monitor attendance or tickets


🧱 Tech Stack
🔧 Backend (FastAPI)
Authentication: JWT Tokens


Database: PostgreSQL



 Frontend (Next.js)
Server-side rendering & routing


UI: Admin and Employee dashboards


Theme toggling (light/dark)

Local Recognition(Locally using tkinter and opencv)
Face Recognition: face_recognition, OpenCV, and dlib
Liveness Detection: Eye blinking threshold



🚀 Getting Started
 Hosted Web App
Frontend URL: https://fras-ruby.vercel.app/ 


Backend URL: https://your-backend.onrender.com

👤 1. Admin Registration
Endpoint:  Frontend URL/auth/admin/register
{
  "name": "John Doe",
  "email": "admin@example.com",
  "role": "admin",
  "password": "securepassword",
  "company": "ABC Ltd"
}

🔐 2. Admin Login
Endpoint:  Frontend URL/auth/admin/login
{
  "email": "admin@example.com",
  "password": "securepassword"
}



👥 3. Employee Management
Add new employees manually


Upload employee profile images (passport-style, front-facing)


Download employee data as CSV


Delete/update employee information


📌 Note: Images are used for facial recognition, so clarity is important.

📸 4. Configure Camera Settings
Add Camera Settings:
Camera Type: webcam or ip (use webcam for now)


Camera Source: Use 0 for webcam (default camera), or IP address for network camera


Blinking Threshold: Liveness detection (suggested: 3)


Arrival/Departure Time: Used to set expected working hours (e.g., 08:00, 17:00)
Save the settings.


5. Track Attendance (Run Local Recognition App)
⚠️ Vercel/Render cannot run facial recognition directly.
 Use the local app for that part. See below.

Start Attendance:
Click "Start Recognition"


Employee should face the camera for ~4 minutes


How It Works:
An initial attendance record is created with:


status: absent


checkin, checkout, hours_worked: null


If face is detected:


checkin is set


After 2 minutes, checkout is set


hours_worked is calculated




6. View Attendance
Use Dashboard:


Filter by date, employee, status


View check-in/out times, hours worked


Track absentees or top performers

🧾 7. Tickets (Employee Support)
View all employee-submitted tickets


Filter by status: pending, in progress, solved


Update ticket status based on progress



⚙️ 8. Settings
Update admin name, email, and password


Toggle between dark and light mode


Manage account preferences



👨‍💼 Employee Usage
🔐 Employee Login
Endpoint: POST /api/auth/employee/login
json
CopyEdit
{
  "id": 1,
  "email": "employee@example.com",
  "company": "ABC Ltd"
}

📝 Note: Employees do not register themselves. The admin provides their credentials.

📊 1. Dashboard
View personal attendance records


Filter by date range and status


See check-in, check-out, hours worked



🧾 2. Tickets
Submit a new ticket (issue with attendance, system, etc.)


View existing tickets and their status


Get feedback/resolution updates from admin





Facial Recognition Setup (Local)
NOTE: For a detailed user guideline, check https://github.com/NtwariMike-CK/Facial-Recognition-Attendance-System-v1/blob/main/fras_local/README.md 
▶️ Prerequisites
Python 3.9+


Webcam (or IP camera)


Git


Admin credentials


Internet access


▶️ Installation Steps
Installation Steps
1. Clone the Repository
https://github.com/NtwariMike-CK/Facial-Recognition-Attendance-System-v1.git 
Facial-Recognition-Attendance-System-v1
2. Navigate to root Directory
cd fras_local
2. Create Virtual Environment
python -m venv venv
# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
3. Install Dependencies
pip install -r requirements.txt
4. Download Face Landmarks Model
Download the face landmarks model file:
Go to: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 
Download and extract the file
Place shape_predictor_68_face_landmarks.dat in the root folder 
5. Configure API URL
File Structure
fras_local/
├── main.py                               # Main application
├── config.py                            # Configuration settings
├── database_client.py                   # API client for backend
├── recognition_service.py                # Face recognition logic
├── requirements.txt                     # Python dependencies
└── shape_predictor_68_face_landmarks.dat # Face landmarks model (download)
└── venv/                                    # Virtual environment
Running the Application
1. Activate Virtual Environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
2. Start the Application
python main.py
3. Login and Use
Login: Enter your admin email and password
Start Recognition: Click "Start Recognition" to begin face detection
Employee should face the camera for ~4 minutes
Monitor: Watch the camera feed and activity log for attendance events


How It Works:
An initial attendance record is created with:


status: absent


checkin, checkout, hours_worked: null


If face is detected:


checkin is set


After 2 minutes, checkout is set


hours_worked is calculated



🧪 Testing Tips for Admins
Use good lighting when using the camera


Ensure passport image and live face match


Use realistic working hours (e.g., 08:00–17:00)


Wait at least 4 minutes to test full recognition flow



📝 Notes
Do not refresh or interrupt camera recognition once started


Face data is stored securely (check backend for encryption/privacy)


The app is optimized for Chrome/Edge browsers



