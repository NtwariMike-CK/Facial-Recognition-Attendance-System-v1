# schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum
from fastapi import Form, File, UploadFile

class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    hr = "hr"

class RoleEnum(str, Enum):
    admin = "admin"
    employee = "employee"

class AttendanceStatus(str, Enum):
    present = "present"
    late = "late"
    absent = "absent"

class TicketStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    solved = "solved"

# Auth Schemas
class AdminCreate(BaseModel):
    id: str
    full_name: str
    email: str
    password: str
    role: RoleEnum
    department: str
    company_name: str


class AdminRegister(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    password: str
    company: str

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class EmployeeLogin(BaseModel):
    id: int
    email: EmailStr
    company: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_id: int
    company: str

# Employee Schemas
class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    role: str
    department: str

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    department: Optional[str] = None

class EmployeeResponseWithImage(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: str
    image_path: Optional[str]
    company: str
    created_at: datetime

class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: str
    company: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Attendance Schemas
class AttendanceRecord(BaseModel):
    id: int
    employee_id: int
    name: str
    arrival_time: Optional[datetime]
    departure_time: Optional[datetime]
    hours_worked: Optional[float]
    status: AttendanceStatus
    camera_used: Optional[str]
    date: datetime
    
    class Config:
        from_attributes = True

class AttendanceCreate(BaseModel):
    employee_id: int
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    hours_worked: Optional[float] = None
    status: str = "absent"
    camera_used: Optional[str] = None

class AttendanceUpdate(BaseModel):
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    hours_worked: Optional[float] = None
    status: Optional[str] = None

class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    name: str
    arrival_time: Optional[datetime]
    departure_time: Optional[datetime]
    hours_worked: Optional[float]
    status: str
    camera_used: Optional[str]
    date: datetime
    
    class Config:
        from_attributes = True

# Dashboard Schemas
class DashboardSummary(BaseModel):
    total_employees: int
    present_today: int
    absent_today: int
    late_today: int
    attendance_by_department: dict
    late_days_week: dict
    arrival_time_trend: List[dict]

class EmployeeDashboard(BaseModel):
    total_present: int
    total_late: int
    total_absent: int
    average_arrival_time: Optional[str]
    average_departure_time: Optional[str]
    recent_attendance: List[AttendanceRecord]

# Ticket Schemas
class TicketCreate(BaseModel):
    message: str

class TicketUpdate(BaseModel):
    status: TicketStatus

class TicketResponse(BaseModel):
    id: int
    admin_id: int
    employee_id: int
    message: str
    status: TicketStatus
    created_at: datetime
    updated_at: Optional[datetime]
    employee_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Camera Settings Schemas
class CameraSettingsCreate(BaseModel):
    camera_type: str
    camera_source: str
    blinking_threshold: float = 0.3
    arrival_time: str
    departure_time: str

class CameraSettingsUpdate(BaseModel):
    camera_type: Optional[str] = None
    camera_source: Optional[str] = None
    blinking_threshold: Optional[float] = None
    arrival_time: Optional[str] = None
    departure_time: Optional[str] = None

class CameraSettingsResponse(BaseModel):
    id: int
    company: str
    camera_type: str
    camera_source: str
    blinking_threshold: float
    arrival_time: str
    departure_time: str
    recognition_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Admin Profile Schemas
class AdminProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None

class AdminPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class AdminResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    company: str
    created_at: datetime
    
    class Config:
        from_attributes = True