# 📘 FRAS – Facial Recognition Attendance System

---

## 🔍 Overview

FRAS is a web-based attendance system that uses facial recognition to automate employee check-ins and check-outs. It is designed for companies to efficiently track attendance while offering dashboards, camera setup tools, and support ticketing systems.

The platform consists of two main components:

- 🌐 A **hosted web application** for registration, camera settings, attendance tracking, and analytics.
- 💻 A **local facial recognition module** that detects and records attendance in real-time using a webcam or IP camera.

---

## 🧱 System Overview

| Component         | Description                                  |
|------------------|----------------------------------------------|
| Web Frontend     | Next.js application hosted on Vercel         |
| Backend API      | FastAPI REST API (deployed on Render/Railway)|
| Local Recognition| Python app using OpenCV, dlib, face_recognition |
| Database         | PostgreSQL                                    |

---

## 👤 User Roles

### 🔹 Admin

- Registers the company account
- Adds and manages employees
- Uploads employee passport-style photos
- Configures camera, working hours, and liveness settings
- Runs the local recognition app
- Views analytics and attendance reports
- Handles employee tickets

### 🔹 Employee

- Logs in using admin-provided credentials
- Views personal attendance records
- Submits and tracks support tickets

---

## 🔄 Workflow Summary

1. Admin signs up and logs into the web dashboard.
2. Admin adds employees and configures camera/liveness settings.
3. Admin runs the local Python recognition app.
4. App detects faces and updates attendance via API.
5. Admin and employees use the dashboard to track and manage attendance or tickets.

---

## 🧱 Tech Stack

### 🔧 Backend (FastAPI)

- Authentication: JWT tokens
- Database: PostgreSQL

### 🎨 Frontend (Next.js)

- Server-side rendering
- Admin & Employee dashboards
- Dark/Light mode toggling

### 🧠 Local Recognition

- Face Detection: `face_recognition`, OpenCV, `dlib`
- Liveness Detection: Eye blinking (blink threshold)

---

## 🚀 Getting Started

### 🌐 Hosted Web App

- **Frontend:** [`https://fras-ruby.vercel.app`](https://fras-ruby.vercel.app)
- **Backend:** `https://your-backend.onrender.com`

---

### 👤 1. Admin Registration

**Endpoint:**  
`[Frontend URL]/auth/admin/register`

**Sample Payload:**

```json
{
  "name": "John Doe",
  "email": "admin@example.com",
  "role": "admin",
  "password": "securepassword",
  "company": "ABC Ltd"
}
```
🔐 2. Admin Login
Endpoint:
[Frontend URL]/auth/admin/login

Sample Payload:
```
{
  "email": "admin@example.com",
  "password": "securepassword"
}
```

## 3. Employee Management

. Add employees manually

. Upload front-facing passport-style images

. Export data as CSV

. Edit or delete employee records

📌 Note: Clear facial images are essential for reliable recognition.

## 4. Configure Camera Settings
Camera Type: webcam or ip

Camera Source: 0 for default webcam or IP address

Blinking Threshold: Suggest 3

Arrival/Departure Time: e.g., 08:00, 17:00

Click "Save Settings" when done.

🖥️ 5. Run Local Recognition App
⚠️ Facial recognition does not run on Vercel/Render.
Use the local app for live recognition.

Start Attendance:

Click “Start Recognition”

Employee stands in front of camera for ~4 minutes

Recognition Flow:

Initial attendance is recorded:

json
Copy
Edit
{
  "status": "absent",
  "checkin": null,
  "checkout": null,
  "hours_worked": null
}
Face detected → checkin is set

After 2+ minutes → checkout is set, hours are calculated

📊 6. View Attendance
Filter by date, status, or employee

Track absentees or best performers

Export attendance summaries

🧾 7. Ticket Management
View tickets submitted by employees

Filter: pending, in progress, solved

Update ticket status and respond as needed

⚙️ 8. Admin Settings
Update name, email, or password

Toggle between dark/light themes

Manage general preferences

👨‍💼 Employee Usage
🔐 Login
Endpoint:
POST /api/auth/employee/login

json
Copy
Edit
{
  "id": 1,
  "email": "employee@example.com",
  "company": "ABC Ltd"
}
📌 Note: Employees are registered by the admin and cannot self-register.

📊 Dashboard
View personal check-in/check-out history

Filter by date and status

View total hours worked

🧾 Submit Tickets
Submit new issues (e.g., missed check-in)

View current ticket status

Communicate with admin

🎥 Local Facial Recognition Setup
📎 Detailed guide:
GitHub – fras_local README

▶️ Prerequisites
Python 3.9+

Webcam (or IP camera)

Git

Admin credentials

Internet connection

🧰 Installation Steps
bash
Copy
Edit
# 1. Clone repository
git clone https://github.com/NtwariMike-CK/Facial-Recognition-Attendance-System-v1.git
cd fras_local

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download face landmarks model
# Visit:
http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
# Extract and place in root folder

# 5. Run the app
python main.py
📁 Project Structure (Local App)
bash
Copy
Edit
fras_local/
├── main.py                         # Main GUI app
├── config.py                       # Config values
├── database_client.py              # API integration
├── recognition_service.py          # Face detection logic
├── shape_predictor_68...dat        # Facial landmarks model
├── requirements.txt
└── venv/                           # Virtual environment
🎬 Recognition Flow Summary
Start the app and login with admin credentials.

Start camera recognition.

App captures employee face and sends data to backend.

Attendance is recorded:

First detection → check-in

After delay → check-out

Hours worked = checkout - checkin

🧪 Admin Testing Tips
Ensure good lighting and camera angle

Use high-quality, centered passport images

Test realistic work times (e.g., 08:00–17:00)

Let the app run for at least 4 minutes to test full cycle

📝 Notes
Do not interrupt recognition while running.

Data is securely transmitted to the backend.

Chrome or Edge are recommended browsers.

Liveness detection relies on blinking — avoid static photos.

👨‍💻 Author
Ntwari Mike Chris Kevin
Year 2 Software Engineering Student
Passionate about AI, Automation, and Real-World Applications

📄 License
MIT License – Open for use, contribution, and extension.
