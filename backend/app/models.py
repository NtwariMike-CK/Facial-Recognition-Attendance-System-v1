# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, LargeBinary, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
from sqlalchemy import LargeBinary


class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employees = relationship("Employee", back_populates="admin", cascade="all, delete")
    tickets = relationship("Ticket", back_populates="admin")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    image_path = Column(LargeBinary, nullable=True)
    company = Column(String(255), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    admin = relationship("Admin", back_populates="employees")
    attendance_records = relationship("AttendanceRecord", back_populates="employee", cascade="all, delete")
    tickets = relationship("Ticket", back_populates="employee", cascade="all, delete")
class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)  # Employee name for quick access
    arrival_time = Column(DateTime(timezone=True), nullable=True)
    departure_time = Column(DateTime(timezone=True), nullable=True)
    hours_worked = Column(Float, nullable=True)
    status = Column(String(50), nullable=False)  # present, late, absent
    camera_used = Column(String(255), nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    company = Column(String(255), nullable=False)
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    message = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, in_progress, solved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    admin = relationship("Admin", back_populates="tickets")
    employee = relationship("Employee", back_populates="tickets")

class CameraSettings(Base):
    __tablename__ = "camera_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(255), nullable=False, unique=True)
    camera_type = Column(String(100), nullable=False)  # webcam, ip_camera
    camera_source = Column(String(255), nullable=False)  # 0 for webcam, IP for IP camera
    blinking_threshold = Column(Float, default=0.3)
    arrival_time = Column(String(10), nullable=False)  # HH:MM format
    departure_time = Column(String(10), nullable=False)  # HH:MM format
    recognition_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())