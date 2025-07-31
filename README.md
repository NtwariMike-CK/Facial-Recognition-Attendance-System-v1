# Facial-Recognition-Attendance-System-v1

# FRAS - Facial Recognition Attendance System

A comprehensive attendance tracking system that uses facial recognition technology to monitor employee attendance. Companies can efficiently manage employee attendance through automated facial recognition with liveness detection.

## Features

- **Admin Management**: Complete employee and attendance management
- **Facial Recognition**: Advanced facial recognition with liveness detection
- **Real-time Attendance**: Automated check-in/check-out tracking
- **Analytics Dashboard**: Comprehensive attendance analytics and reports
- **Ticket System**: Employee issue reporting and admin resolution
- **Multi-camera Support**: Webcam and IP camera integration
- **Data Export**: CSV export functionality for attendance records

## Project Structure

```
fras/
├── backend/                           # FastAPI backend
│   ├── app/                          # Main application package
│   │   ├── __pycache__/
│   │   ├── middleware/               # Custom middleware
│   │   ├── routers/                  # API route handlers
│   │   ├── services/                 # Recognition Logic
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
|   |   │   ├── fras_config.json                              # Application configuration
│   │   │   ├── dlib_face_recognition_resnet_model_v1.dat     # Face recognition model
│   │   │   └── recognition_service.py                        # Facial recognition logic
│   │   ├── utils/                    # Utility functions
│   │   │  
│   │   └── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
|   |   ├── database.py                # Database connection
│   │   ├── models.py                  # SQLAlchemy database models
│   │   ├── schemas.py                 # Pydantic schemas
│   ├── requirements.txt               # Python dependencies
│   ├── .env                           # Local environment variables (create this)
│   ├── .env.example                   # Example environment file
│   ├── dlib_face_recognition_resnet_model_v1.dat             # Face recognition model
│   ├── shape_predictor_68_face_landmarks.dat                 # Facial landmarks model
|   |
├── Frontend/                        # Next.js frontend
│   ├── .next/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── node_modules/
│   ├── public/
│   ├── styles/
│   ├── components.json
│   ├── next-env.d.ts
│   ├── next.config.mjs
│   ├── package-lock.json
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── postcss.config.mjs
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── .env.local                   # Local environment variables (create this)
│   ├── .env.example                 # Example environment file
│   └── .gitignore
└── README.md
```

## Prerequisites

Before setting up FRAS, ensure you have the following installed:

- **Python 3.8+**
- **Node.js 16.0+** and npm/yarn
- **PostgreSQL 12+** (locally installed) OR **Docker** (for containerized database)
- **Git**
- **Webcam or IP Camera**

**Note**: You'll be setting up a local PostgreSQL database for development. Do not use any production or deployed database for local development.

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/fras.git
cd fras
```

### 2. Local Database Setup

**Note**: This project uses a local PostgreSQL database for development. Do not use any production/deployed database for local development.

#### Install PostgreSQL Locally
- **Windows**: Download from [PostgreSQL Official Site](https://www.postgresql.org/download/windows/)
- **macOS**: `brew install postgresql && brew services start postgresql`
- **Ubuntu/Debian**: `sudo apt-get install postgresql postgresql-contrib`

#### Create Local Development Database
```bash
# Access PostgreSQL (adjust command based on your OS)
# On macOS/Linux:
sudo -u postgres psql
# On Windows (if using default setup):
psql -U postgres

# Create database and user for local development
CREATE DATABASE fras_local_db;
CREATE USER fras_local_user WITH PASSWORD 'local_dev_password';
GRANT ALL PRIVILEGES ON DATABASE fras_local_db TO fras_local_user;

# Exit PostgreSQL
\q
```

#### Alternative: Using Docker for Database (Recommended)
If you prefer not to install PostgreSQL locally, you can use Docker:

```bash
# Pull and run PostgreSQL in Docker
docker run --name fras-postgres \
  -e POSTGRES_DB=fras_local_db \
  -e POSTGRES_USER=fras_local_user \
  -e POSTGRES_PASSWORD=local_dev_password \
  -p 5432:5432 \
  -d postgres:13

# The database will be available at localhost:5432
```

### 3. Backend Setup

#### Navigate to Backend Directory
```bash
cd backend
```

#### Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```


Note: The requirements.txt includes all necessary dependencies including:

FastAPI and Uvicorn for the web framework
face-recognition and dlib for facial recognition
psycopg2-binary for PostgreSQL connection
SQLAlchemy and Alembic for database ORM and migrations
OpenCV for computer vision
And other essential packages

Important: The face recognition models (dlib_face_recognition_resnet_model_v1.dat and shape_predictor_68_face_landmarks.dat) should already be in your backend directory. If they're missing, the face-recognition library will download them automatically on first use.
Environment Configuration
Create a .env file in the backend directory with your local database settings:
```
env# Local Database Configuration
# Use your local PostgreSQL database (NOT any production/deployed database)
DATABASE_URL=postgresql://fras_local_user:local_dev_password@localhost:5432/fras_local_db

# JWT Configuration (generate a new secret for your local development)
SECRET_KEY=your_local_development_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Facial Recognition Configuration
FACE_RECOGNITION_THRESHOLD=0.6
LIVENESS_DETECTION=True
```

**Important**: 
- Never use production database credentials in local development
- Generate your own JWT secret key for local development
- Keep your `.env` file in `.gitignore` to prevent accidental commits

#### Database Migration
```bash
# Initialize the local database with tables and schema
alembic upgrade head

# Or if using a different migration system:
python manage.py migrate
```

**Note**: This will create all necessary tables in your local database. The local database starts empty, so you'll need to create admin accounts and add employees through the application interface.

#### Start Backend Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
API documentation will be available at `http://localhost:8000/docs`

### 4. Frontend Setup

#### Navigate to Frontend Directory
```bash
# Open a new terminal and navigate to frontend
cd frontend
```

#### Install Dependencies
```bash
npm install
# or
yarn install
```

#### Environment Configuration
Create a `.env.local` file in the frontend directory:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api

# Application Configuration
NEXT_PUBLIC_APP_NAME=FRAS
NEXT_PUBLIC_APP_VERSION=1.0.0
```

#### Start Frontend Development Server
```bash
npm run dev
# or
yarn dev
```

The frontend application will be available at `http://localhost:3000`

## Usage Guide

### Admin Setup & Usage

#### 1. Admin Registration
Register a new admin account:

**POST** `/api/auth/register`
```json
{
  "name": "John Doe",
  "email": "admin@company.com",
  "role": "admin",
  "password": "securepassword123",
  "company": "Your Company Name"
}
```

#### 2. Admin Login
**POST** `/api/auth/login`
```json
{
  "email": "admin@company.com",
  "password": "securepassword123"
}
```

#### 3. Employee Management
- **Add Employees**: Navigate to Employee Management → Add New Employee
- **Upload Photos**: Add clear passport-style photos for each employee
- **Export Data**: Download employee data as CSV files

#### 4. Camera Configuration
- **Camera Type**: Select Webcam or IP Camera
- **Camera Source**: 
  - Use `0` for default webcam
  - Use IP address for IP cameras (e.g., `192.168.1.100`)
- **Blinking Threshold**: Set to `3` for optimal liveness detection
- **Set Arrival/Departure Times**: Configure work hours
- **Start Recognition**: Click "Start Recognition" and look at camera for 4 minutes

#### 5. Attendance Process
The system automatically:
1. Creates initial attendance record (status: absent)
2. Updates check-in time when employee is detected
3. Waits 2 minutes then records check-out time
4. Calculates total hours worked

#### 6. Dashboard Analytics
- View attendance summaries
- Apply date and employee filters
- Generate reports

#### 7. Ticket Management
- Review employee tickets
- Update status: Pending → In Progress → Solved

### Employee Usage

#### Employee Login
**POST** `/api/auth/employee-login`
```json
{
  "id": 123,
  "email": "employee@company.com",
  "company": "Your Company Name"
}
```

#### Employee Features
- **Dashboard**: View personal attendance records with filters
- **Tickets**: Submit attendance issues and track ticket status

## API Endpoints

### Authentication
- `POST /api/auth/register` - Admin registration
- `POST /api/auth/login` - Admin login
- `POST /api/auth/employee-login` - Employee login

### Employee Management
- `GET /api/employees` - Get all employees
- `POST /api/employees` - Add new employee
- `PUT /api/employees/{id}` - Update employee
- `DELETE /api/employees/{id}` - Delete employee
- `POST /api/employees/{id}/photo` - Upload employee photo

### Attendance
- `GET /api/attendance` - Get attendance records
- `POST /api/attendance/start` - Start attendance tracking
- `GET /api/attendance/analytics` - Get attendance analytics

### Camera
- `POST /api/camera/settings` - Update camera settings
- `GET /api/camera/settings` - Get camera settings

### Tickets
- `GET /api/tickets` - Get all tickets
- `POST /api/tickets` - Create new ticket
- `PUT /api/tickets/{id}` - Update ticket status

## Troubleshooting

### Common Issues

#### Backend Issues
1. **Database Connection Error**
   ```bash
   # Check PostgreSQL service status
   sudo systemctl status postgresql
   
   # Restart if needed
   sudo systemctl restart postgresql
   ```

2. **Facial Recognition Dependencies**
   ```bash
   # Install additional dependencies if needed
   pip install dlib cmake
   ```

3. **Camera Access Issues**
   - Ensure camera permissions are granted
   - Check if camera is being used by another application
   - Verify camera source number (usually 0 for default webcam)

#### Frontend Issues
1. **Port Already in Use**
   ```bash
   # Kill process using port 3000
   lsof -ti:3000 | xargs kill -9
   ```

2. **API Connection Issues**
   - Verify backend server is running on port 8000
   - Check `.env.local` file for correct API URL

### Performance Optimization

1. **Database Performance**
   - Add indexes on frequently queried columns
   - Regular database maintenance

2. **Facial Recognition Performance**
   - Use appropriate image resolution (recommended: 640x480)
   - Ensure good lighting conditions
   - Clean camera lens regularly

## Development Best Practices

### Environment Variables
- Always use local database for development
- Never commit `.env` files to version control
- Create `.env.example` files as templates
- Use different JWT secrets for local vs production

### Database Management
- Use local PostgreSQL or Docker for development
- Keep development data separate from production
- Run migrations on your local database
- Test with sample data, not production data

### Security in Development
- Generate unique JWT secrets for local development
- Use weak passwords only for local development database
- Never expose production credentials in code or documentation

## Production Deployment

### Backend Deployment
1. Set `DEBUG=False` in environment variables
2. Use production WSGI server (e.g., Gunicorn)
3. Configure reverse proxy (Nginx)
4. Set up SSL certificates
5. Configure database connection pooling

### Frontend Deployment
1. Build production bundle: `npm run build`
2. Deploy to hosting service (Vercel, Netlify, etc.)
3. Configure environment variables
4. Set up CDN for static assets

## Security Considerations

- Use strong JWT secret keys
- Implement rate limiting
- Regular security updates
- Secure database credentials
- HTTPS in production
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@fras-system.com
- Documentation: [Project Wiki](https://github.com/yourusername/fras/wiki)

## Changelog

### Version 1.0.0
- Initial release
- Basic facial recognition attendance tracking
- Admin and employee dashboards
- Ticket system
- CSV export functionality
