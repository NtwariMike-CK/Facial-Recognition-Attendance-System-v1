# FRAS Local Recognition System Setup

This local recognition system connects to your deployed FRAS backend to perform facial recognition attendance tracking.

## Prerequisites

1. **Python 3.9 or higher** installed on your system
2. **Webcam or IP camera** connected to your computer
3. **Active internet connection** to connect to your deployed backend
4. **Admin credentials** for your FRAS system

## Installation Steps

### 1. Clone the Repository
```
https://github.com/NtwariMike-CK/Facial-Recognition-Attendance-System-v1.git
Facial-Recognition-Attendance-System-v1
```

### 2. Navigate to root Directory
```bash
cd fras_local
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Face Landmarks Model
Download the face landmarks model file:
- Go to: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
- Download and extract the file
- Place `shape_predictor_68_face_landmarks.dat` in the root folder

### 5. Configure API URL

## File Structure
```
fras_local/
├── main.py                               # Main application
├── config.py                            # Configuration settings
├── database_client.py                   # API client for backend
├── recognition_service.py                # Face recognition logic
├── requirements.txt                     # Python dependencies
└── shape_predictor_68_face_landmarks.dat # Face landmarks model (download)
└── venv/                                    # Virtual environment
```

## Running the Application

### 1. Activate Virtual Environment
```bash
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Start the Application
```bash
python main.py
```

### 3. Login and Use
1. **Login**: Enter your admin email and password
2. **Start Recognition**: Click "Start Recognition" to begin face detection
3. **Monitor**: Watch the camera feed and activity log for attendance events

## Configuration Options

### Camera Settings
- **Default Camera**: Uses webcam (camera index 0)
- **IP Camera**: Update camera_source in server's camera settings
- **Resolution**: Default 1280x720, configurable in config.py

### Recognition Settings
- **Face Tolerance**: Default 0.6 (lower = stricter matching)
- **Blink Threshold**: Number of blinks required for liveness detection
- **Checkout Delay**: Minimum time between check-in and potential check-out

## Troubleshooting

### Common Issues

1. **"Cannot connect to server"**
   - Check your internet connection
   - Verify the API_BASE_URL in config.py
   - Ensure your backend is running and accessible

2. **"Camera cannot be opened"**
   - Check if another application is using the camera
   - Try different camera indices (0, 1, 2, etc.)
   - For IP cameras, verify the RTSP/HTTP URL

3. **"Face landmarks model not found"**
   - Download the landmarks model as described in step 4
   - Ensure the file is in the correct location

4. **"No employees found"**
   - Login to your web dashboard
   - Upload employee photos
   - Click "Refresh Data" in the local app

### Performance Tips

1. **Better Recognition Accuracy**:
   - Ensure good lighting conditions
   - Use high-quality employee photos
   - Position camera at eye level
   - Avoid backlighting

2. **Faster Processing**:
   - Lower camera resolution in config.py
   - Reduce face recognition tolerance
   - Close other camera applications

## Security Notes

- **Credentials**: The app stores login tokens temporarily in memory only
- **Network**: All communication with backend uses HTTPS
- **Local Data**: No employee images are stored locally permanently
- **Camera Access**: Only used for real-time recognition, no recording

## Support

If you encounter issues:
1. Check the activity log in the application
2. Verify your backend is accessible from a web browser
3. Ensure employee photos are uploaded in your web dashboard
4. Try restarting the application

## Features

- ✅ Real-time face recognition
- ✅ Liveness detection (blink verification)
- ✅ Automatic check-in/check-out
- ✅ Live camera preview
- ✅ Activity logging
- ✅ Connection to deployed database
- ✅ Multi-employee recognition
- ✅ Configurable thresholds
