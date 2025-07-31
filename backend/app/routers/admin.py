# routers/admin.py
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Response, WebSocket, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, extract, desc, asc, case
from typing import List, Optional
from datetime import datetime, date, time
import io
from PIL import Image
import base64
import subprocess
import os
import csv
from io import StringIO

import cv2
import asyncio
from threading import Lock

import asyncio
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import logging
from datetime import timedelta


logger = logging.getLogger(__name__)


from app.database import get_db
from app.models import Admin, Employee, AttendanceRecord, Ticket, CameraSettings
from app.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeResponseWithImage,
    DashboardSummary, TicketResponse, TicketUpdate,
    CameraSettingsCreate, CameraSettingsUpdate, CameraSettingsResponse,
    AdminProfileUpdate, AdminPasswordUpdate, AdminResponse, AttendanceResponse,
    AttendanceCreate, AttendanceUpdate,
    AttendanceRecord as AttendanceRecordSchema
)
from app.middleware.auth import get_current_admin
from app.utils.auth import verify_password, get_password_hash
from app.services.recognition_service import recognition_service
router = APIRouter()

# Helper data
day_names = {
    0: "Sunday",
    1: "Monday", 
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday"
}



# 1. Enhanced Dashboard with Filters
@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    date_filter: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    employee_id: Optional[str] = Query(None, description="Filter by employee ID")
):
    """Get dashboard summary with optional filters."""
    
    target_date = datetime.strptime(date_filter, "%Y-%m-%d").date() if date_filter else date.today()
    company = current_admin.company
    
    # Base employee query
    employee_query = db.query(Employee).filter(Employee.company == company)
    if department:
        employee_query = employee_query.filter(Employee.department.ilike(f"%{department}%"))
    if employee_id:
        employee_query = employee_query.filter(Employee.id == employee_id)
    
    total_employees = employee_query.count()
    
    # Attendance query with filters
    attendance_query = db.query(AttendanceRecord).join(Employee).filter(
        and_(
            Employee.company == company,
            func.date(AttendanceRecord.date) == target_date
        )
    )
    
    if department:
        attendance_query = attendance_query.filter(Employee.department.ilike(f"%{department}%"))
    if employee_id:
        attendance_query = attendance_query.filter(Employee.id == employee_id)
    
    today_attendance = attendance_query.all()
    
    present_today = len([a for a in today_attendance if a.status == "present"])
    late_today = len([a for a in today_attendance if a.status == "late"])
    absent_today = total_employees - len(today_attendance)
    
    # Department attendance breakdown
    dept_attendance = db.query(
        Employee.department,
        AttendanceRecord.status,
        func.count(AttendanceRecord.id).label('count')
    ).join(AttendanceRecord).filter(
        and_(
            Employee.company == company,
            func.date(AttendanceRecord.date) == target_date
        )
    )
    
    if department:
        dept_attendance = dept_attendance.filter(Employee.department.ilike(f"%{department}%"))
    
    dept_attendance = dept_attendance.group_by(Employee.department, AttendanceRecord.status).all()
    
    # Process department data
    attendance_by_department = {}
    for dept, status, count in dept_attendance:
        if dept not in attendance_by_department:
            attendance_by_department[dept] = {"present": 0, "absent": 0, "late": 0}
        attendance_by_department[dept][status] = count
    
    # Late days analysis (last 30 days)
    late_days = db.query(
        extract('dow', AttendanceRecord.date).label('day_of_week'),
        func.count(AttendanceRecord.id).label('late_count')
    ).join(Employee).filter(
        and_(
            Employee.company == company,
            AttendanceRecord.status == "late",
            AttendanceRecord.date >= target_date - timedelta(days=30)
        )
    ).group_by('day_of_week').all()
    
    late_days_week = {day_names[int(day)]: count for day, count in late_days}
    
    # Arrival time trend (last 7 days)
    arrival_trend = db.query(
        func.date(AttendanceRecord.date).label('date'),
        func.avg(func.extract('hour', AttendanceRecord.arrival_time) + 
                func.extract('minute', AttendanceRecord.arrival_time) / 60.0).label('avg_hour')
    ).join(Employee).filter(
        and_(
            Employee.company == company,
            AttendanceRecord.date >= target_date - timedelta(days=7)
        )
    ).group_by('date').order_by('date').all()
    
    arrival_time_trend = [
        {"date": str(date_val), "avg_arrival_hour": round(float(avg_hour or 9), 2)}
        for date_val, avg_hour in arrival_trend
    ]
    
    return DashboardSummary(
        total_employees=total_employees,
        present_today=present_today,
        absent_today=absent_today,
        late_today=late_today,
        attendance_by_department=attendance_by_department,
        late_days_week=late_days_week,
        arrival_time_trend=arrival_time_trend
    )

@router.get("/recent-activity")
async def get_recent_activity(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of recent activities to fetch")
):
    """Get recent attendance activities for activity feed."""

    # Query AttendanceRecord and join with Employee
    recent_activities = db.query(AttendanceRecord).join(Employee).filter(
        Employee.company == current_admin.company
    ).order_by(
        desc(AttendanceRecord.date),
        desc(AttendanceRecord.arrival_time)
    ).limit(limit).all()

    return {
        "activities": [
            {
                "id": activity.id,
                "employee_name": activity.employee.name,
                "employee_id": activity.employee.id,
                "department": activity.employee.department,
                "date": str(activity.date),
                "arrival_time": str(activity.arrival_time),
                "status": activity.status,
                "timestamp": f"{activity.date} {activity.arrival_time}"
            }
            for activity in recent_activities
        ]
    }

# 3. Top Performers (Most Punctual)
@router.get("/top-performers")
async def get_top_performers(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to analyze"),
    limit: int = Query(5, description="Number of top performers to return")
):
    """Get employees with best attendance in the specified period."""
    
    start_date = date.today() - timedelta(days=days)
    
    performers = db.query(
        Employee.name,
        Employee.id,
        Employee.department,
        func.count(AttendanceRecord.id).label('total_days'),
        func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present_days'),
        func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late_days'),
        (func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)) * 100.0 / 
         func.count(AttendanceRecord.id)).label('attendance_rate')
    ).join(AttendanceRecord).filter(
        and_(
            Employee.company == current_admin.company,
            AttendanceRecord.date >= start_date
        )
    ).group_by(Employee.id, Employee.name, Employee.id, Employee.department
    ).having(func.count(AttendanceRecord.id) >= days * 0.8  # At least 80% record availability
    ).order_by(desc('attendance_rate')).limit(limit).all()
    
    return {
        "top_performers": [
            {
                "name": p.name,
                "employee_id": p.employee_id,
                "department": p.department,
                "attendance_rate": round(float(p.attendance_rate or 0), 1),
                "present_days": p.present_days or 0,
                "late_days": p.late_days or 0,
                "total_days": p.total_days or 0
            }
            for p in performers
        ]
    }

# 4. Attendance Trends (Weekly/Monthly)
@router.get("/attendance-trends")
async def get_attendance_trends(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    period: str = Query("weekly", description="Trend period: 'weekly' or 'monthly'"),
    weeks: int = Query(4, description="Number of weeks/months to analyze")
):
    """Get attendance trends over time."""
    
    if period == "weekly":
        # Weekly trends
        trends = db.query(
            func.date_trunc('week', AttendanceRecord.date).label('period'),
            func.count(AttendanceRecord.id).label('total_records'),
            func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present_count'),
            func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late_count')
        ).join(Employee).filter(
            and_(
                Employee.company == current_admin.company,
                AttendanceRecord.date >= date.today() - timedelta(weeks=weeks)
            )
        ).group_by('period').order_by('period').all()
    else:
        # Monthly trends
        trends = db.query(
            func.date_trunc('month', AttendanceRecord.date).label('period'),
            func.count(AttendanceRecord.id).label('total_records'),
            func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present_count'),
            func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late_count')
        ).join(Employee).filter(
            and_(
                Employee.company == current_admin.company,
                AttendanceRecord.date >= date.today() - timedelta(days=weeks*30)
            )
        ).group_by('period').order_by('period').all()
    
    return {
        "trends": [
            {
                "period": str(trend.period.date()) if hasattr(trend.period, 'date') else str(trend.period),
                "total_records": trend.total_records or 0,
                "present_count": trend.present_count or 0,
                "late_count": trend.late_count or 0,
                "attendance_rate": round((trend.present_count or 0) * 100.0 / (trend.total_records or 1), 1)
            }
            for trend in trends
        ]
    }

# 5. Department Comparison
@router.get("/department-comparison")
async def get_department_comparison(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to analyze")
):
    """Compare attendance across departments."""
    
    start_date = date.today() - timedelta(days=days)
    
    dept_stats = db.query(
        Employee.department,
        func.count(Employee.id).label('total_employees'),
        func.count(AttendanceRecord.id).label('total_records'),
        func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present_count'),
        func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late_count'),
        func.avg(func.extract('hour', AttendanceRecord.arrival_time) + 
                func.extract('minute', AttendanceRecord.arrival_time) / 60.0).label('avg_arrival_hour')
    ).outerjoin(AttendanceRecord, 
        and_(Employee.id == AttendanceRecord.employee_id,
             AttendanceRecord.date >= start_date)
    ).filter(
        Employee.company == current_admin.company
    ).group_by(Employee.department).all()
    
    return {
        "departments": [
            {
                "department": dept.department or "Unknown",
                "total_employees": dept.total_employees or 0,
                "attendance_rate": round((dept.present_count or 0) * 100.0 / (dept.total_records or 1), 1),
                "late_rate": round((dept.late_count or 0) * 100.0 / (dept.total_records or 1), 1),
                "avg_arrival_time": f"{int(dept.avg_arrival_hour or 9):02d}:{int(((dept.avg_arrival_hour or 9) % 1) * 60):02d}",
                "present_count": dept.present_count or 0,
                "late_count": dept.late_count or 0
            }
            for dept in dept_stats
        ]
    }

# 6. Employee Search/List with Attendance Summary
@router.get("/employees-summary")
async def get_employees_summary(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by name or employee ID"),
    department: Optional[str] = Query(None, description="Filter by department"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(20, description="Items per page")
):
    """Get employees list with their attendance summary."""
    
    # Base query
    query = db.query(Employee).filter(Employee.company == current_admin.company)
    
    # Apply filters
    if search:
        query = query.filter(
            (Employee.name.ilike(f"%{search}%")) | 
            (Employee.id.ilike(f"%{search}%"))
        )
    if department:
        query = query.filter(Employee.department.ilike(f"%{department}%"))
    
    # Pagination
    total = query.count()
    employees = query.offset((page - 1) * limit).limit(limit).all()
    
    # Get attendance summary for each employee (last 30 days)
    start_date = date.today() - timedelta(days=30)
    
    employee_summaries = []
    for emp in employees:
        attendance_stats = db.query(
            func.count(AttendanceRecord.id).label('total_days'),
            func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present_days'),
            func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late_days')
        ).filter(
            and_(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.date >= start_date
            )
        ).first()
        
        employee_summaries.append({
            "id": emp.id,
            "name": emp.name,
            "employee_id": emp.employee_id,
            "department": emp.department,
            "email": emp.email,
            "total_days": attendance_stats.total_days or 0,
            "present_days": attendance_stats.present_days or 0,
            "late_days": attendance_stats.late_days or 0,
            "attendance_rate": round((attendance_stats.present_days or 0) * 100.0 / (attendance_stats.total_days or 1), 1)
        })
    
    return {
        "employees": employee_summaries,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }



@router.get("/quick-stats")
async def get_quick_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get quick stats for dashboard widgets."""

    today = date.today()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)

    # Today vs Yesterday
    today_present = db.query(AttendanceRecord).join(Employee).filter(
        Employee.company == current_admin.company,
        func.date(AttendanceRecord.date) == today,
        AttendanceRecord.status == 'present'
    ).count()

    yesterday_present = db.query(AttendanceRecord).join(Employee).filter(
        Employee.company == current_admin.company,
        func.date(AttendanceRecord.date) == yesterday,
        AttendanceRecord.status == 'present'
    ).count()

    # Weekly average (fixed)
    subquery = (
        db.query(func.count(AttendanceRecord.id).label("daily_count"))
        .join(Employee)
        .filter(
            Employee.company == current_admin.company,
            AttendanceRecord.date >= last_week,
            AttendanceRecord.status == 'present'
        )
        .group_by(func.date(AttendanceRecord.date))
        .subquery()
    )

    weekly_avg = db.query(func.avg(subquery.c.daily_count)).scalar() or 0

    return {
        "today_present": today_present,
        "yesterday_present": yesterday_present,
        "change_from_yesterday": today_present - yesterday_present,
        "weekly_average": round(float(weekly_avg), 1),
        "trend": "up" if today_present > yesterday_present else "down" if today_present < yesterday_present else "stable"
    }


# Employee management endpoints
@router.post("/employees", response_model=EmployeeResponseWithImage)
async def create_employee(
    employee_data: EmployeeCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new employee."""
    
    # Check if employee email already exists in the same company
    existing_employee = db.query(Employee).filter(
        and_(
            Employee.email == employee_data.email,
            Employee.company == current_admin.company
        )
    ).first()
    
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this email already exists in your company"
        )
    
    new_employee = Employee(
        name=employee_data.name,
        email=employee_data.email,
        role=employee_data.role,
        department=employee_data.department,
        company=current_admin.company,
        admin_id=current_admin.id
    )
    
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    
    return new_employee


@router.get("/employees/download", response_class=StreamingResponse)
async def download_employees_csv(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Download all employees for the admin's company as a CSV file (excluding image_path)."""

    employees = db.query(Employee).filter(
        Employee.company == current_admin.company
    ).all()

    if not employees:
        raise HTTPException(status_code=404, detail="No employees found")

    # Prepare CSV in memory
    csv_file = StringIO()
    writer = csv.writer(csv_file)

    # Write header (matching EmployeeResponse)
    writer.writerow(["id", "name", "email", "role", "department", "company", "created_at"])

    for emp in employees:
        writer.writerow([
            emp.id,
            emp.name,
            emp.email,
            emp.role,
            emp.department,
            emp.company,
            emp.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    csv_file.seek(0)
    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"}
    )



@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all employees for the admin's company."""
    
    employees = db.query(Employee).filter(
        Employee.company == current_admin.company
    ).all()
    
    return employees

@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific employee."""
    
    employee = db.query(Employee).filter(
        and_(
            Employee.id == employee_id,
            Employee.company == current_admin.company
        )
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee
 

@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an employee."""
    
    employee = db.query(Employee).filter(
        and_(
            Employee.id == employee_id,
            Employee.company == current_admin.company
        )
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update employee fields
    for field, value in employee_data.dict(exclude_unset=True).items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    return employee

@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete an employee."""
    
    employee = db.query(Employee).filter(
        and_(
            Employee.id == employee_id,
            Employee.company == current_admin.company
        )
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    db.delete(employee)
    db.commit()
    
    return {"message": "Employee deleted successfully"}




@router.post("/employees/{employee_id}/upload-image")
async def upload_employee_image(
    employee_id: int,
    file: UploadFile = File(...),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload employee image for facial recognition."""
    
    employee = db.query(Employee).filter(
        and_(
            Employee.id == employee_id,
            Employee.company == current_admin.company
        )
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Read and validate image
    try:
        image_path = await file.read()
        
        # Optional: Validate image with PIL
        image = Image.open(io.BytesIO(image_path))
        image.verify()  # Verify it's a valid image
        
        # Reset file pointer for re-reading
        await file.seek(0)
        image_path = await file.read()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )
    
    # Check file size (limit to 5MB)
    if len(image_path) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file too large. Maximum size is 5MB."
        )
    
    # Update employee record with image data
    employee.image_path = image_path
    
    db.commit()
    
    return {
        "message": "Image uploaded successfully",
        "employee_id": employee_id,
        "employee_name": employee.name,
        "size": len(image_path)
    }


@router.get("/employees/{employee_id}/image")
async def get_employee_image(
    employee_id: int,
    format: Optional[str] = "stream",  # "stream" or "base64"
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get employee image in different formats."""
    
    employee = db.query(Employee).filter(
        and_(
            Employee.id == employee_id,
            Employee.company == current_admin.company
        )
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    if not employee.image_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee image not found"
        )
    
    if format == "base64":
        # Return base64 encoded image
        image_base64 = base64.b64encode(employee.image_path).decode('utf-8')
        return {
            "employee_id": employee_id,
            "employee_name": employee.name,
            "image_base64": image_base64,
            "size": len(employee.image_path)
        }
    else:
        # Return streaming response (default)
        # Try to determine the actual image format
        try:
            image = Image.open(io.BytesIO(employee.image_path))
            image_format = image.format.lower()
            media_type = f"image/{image_format}"
        except:
            media_type = "image/jpeg"  # fallback
        
        return StreamingResponse(
            io.BytesIO(employee.image_path),
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=employee_{employee_id}_{employee.name.replace(' ', '_')}.jpg"
            }
        )



@router.get("/employees/images/all")
async def get_all_employee_images(
    format: Optional[str] = "base64",  # Only base64 supported for recognition system
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all employee images with their id, name, and base64 encoded image data.
    Designed for facial recognition backend system.
    """
    
    employees = db.query(Employee).filter(
        and_(
            Employee.company == current_admin.company,
            Employee.image_path.isnot(None)  # Only employees with images
        )
    ).all()
    
    if not employees:
        return {
            "message": "No employee images found",
            "total_employees": 0,
            "employees": []
        }
    
    employee_images = []
    
    for employee in employees:
        try:
            # image_base64 = base64.b64encode(employee.image_path).decode('utf-8')
            image_base64 = base64.b64encode(employee.image_path).decode('utf-8')
        except Exception as e:
            # Handle encoding errors gracefully, optionally log them
            image_base64 = None
        
        employee_data = {
            "employee_id": employee.id,
            "employee_name": employee.name,
            "image_base64": image_base64,
        }
        
        employee_images.append(employee_data)
    
    return {
        "total_employees": len(employee_images),
        "format": "base64",
        "employees": employee_images
    }



@router.delete("/employees/{employee_id}/image")
async def delete_employee_image(
    employee_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete employee image."""
    
    employee = db.query(Employee).filter(
        and_(
            Employee.id == employee_id,
            Employee.company == current_admin.company
        )
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    employee.image_path = None
    
    db.commit()
    
    return {"message": "Employee image deleted successfully"}

# Camera settings endpoints
@router.post("/camera-settings", response_model=CameraSettingsResponse)
async def create_camera_settings(
    settings_data: CameraSettingsCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create or update camera settings."""
    
    # Check if settings already exist for this company
    existing_settings = db.query(CameraSettings).filter(
        CameraSettings.company == current_admin.company
    ).first()
    
    if existing_settings:
        # Update existing settings
        for field, value in settings_data.dict().items():
            setattr(existing_settings, field, value)
        db.commit()
        db.refresh(existing_settings)
        return existing_settings
    else:
        # Create new settings
        new_settings = CameraSettings(
            company=current_admin.company,
            **settings_data.dict()
        )
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        return new_settings

@router.get("/camera-settings", response_model=CameraSettingsResponse)
async def get_camera_settings(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get camera settings for the admin's company."""
    
    settings = db.query(CameraSettings).filter(
        CameraSettings.company == current_admin.company
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera settings not found"
        )
    
    return settings


@router.post("/camera-settings/start-recognition")
async def start_recognition(
    show_preview: bool = True,  # Add optional parameter for preview
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Start the facial recognition system with optional camera preview."""
    
    settings = db.query(CameraSettings).filter(
        CameraSettings.company == current_admin.company
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera settings not found. Please configure camera first."
        )

    # Check if employees with images exist
    employees_with_images = db.query(Employee).filter(
        Employee.company == current_admin.company,
        Employee.image_path.isnot(None)
    ).count()
    
    if employees_with_images == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No employees with images found. Please upload employee images first."
        )
    
    # Start the recognition service with preview option
    result = recognition_service.start_recognition(current_admin.company, db, show_preview)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Update DB state
    settings.recognition_active = True
    db.commit()
    
    # Add preview info to response
    result["preview_enabled"] = show_preview
    if show_preview:
        result["preview_note"] = "Camera preview window opened. Press 'q' in the preview window to stop recognition."
    
    return result

@router.post("/camera-settings/stop-recognition")
async def stop_recognition(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Stop the facial recognition system."""
    
    settings = db.query(CameraSettings).filter(
        CameraSettings.company == current_admin.company
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera settings not found"
        )
    
    # Stop the recognition service
    result = recognition_service.stop_recognition()
    
    # Always update DB state, even if stopping failed
    settings.recognition_active = False
    db.commit()
    
    if "error" in result:
        # Log the error but don't raise exception since DB state is updated
        print(f"Warning: {result['error']}")
        return {"message": "Recognition system state updated to inactive", "status": "inactive"}
    
    return result

@router.get("/camera-settings/status")
async def get_recognition_status(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get the current status of the recognition system."""
    
    # Get database state
    settings = db.query(CameraSettings).filter(
        CameraSettings.company == current_admin.company
    ).first()
    
    # Get service status
    service_status = recognition_service.get_status()
    
    return {
        "database_active": settings.recognition_active if settings else False,
        "service_running": service_status["is_running"],
        "company": current_admin.company,
        "employees_loaded": service_status.get("employees_loaded", 0),
        "camera_source": service_status.get("camera_source", "Unknown"),
        "camera_type": service_status.get("camera_type", "Unknown"),
        "last_updated": settings.updated_at if settings else None
    }
@router.post("/attendance", response_model=AttendanceResponse)
async def create_attendance_record(
    attendance_data: AttendanceCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new attendance record (used by recognition system)."""
    
    # Verify employee belongs to admin's company
    employee = db.query(Employee).filter(
        Employee.id == attendance_data.employee_id,
        Employee.company == current_admin.company
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    new_record = AttendanceRecord(
        employee_id=attendance_data.employee_id,
        name=employee.name,
        arrival_time=attendance_data.arrival_time,
        departure_time=attendance_data.departure_time,
        hours_worked=attendance_data.hours_worked,
        status=attendance_data.status,
        camera_used=attendance_data.camera_used,
        company=current_admin.company
    )
    
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    return new_record


# Updated camera settings endpoint to restart recognition if needed
@router.put("/camera-settings")
async def update_camera_settings(
    settings_data: dict,  # Replace with your actual Pydantic model
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update camera settings."""
    
    settings = db.query(CameraSettings).filter(
        CameraSettings.company == current_admin.company
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera settings not found"
        )
    
    # Update settings fields
    for field, value in settings_data.items():
        if hasattr(settings, field):
            setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    
    # If recognition is running, restart it with new settings
    if settings.recognition_active and recognition_service.is_running:
        print("Restarting recognition with new settings...")
        recognition_service.stop_recognition()
        recognition_service.start_recognition(current_admin.company, db)
    
    return settings


@router.put("/attendance/{record_id}", response_model=AttendanceResponse)
async def update_attendance_record(
    record_id: int,
    attendance_data: AttendanceUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an attendance record (used by recognition system)."""
    
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.id == record_id,
        AttendanceRecord.company == current_admin.company
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Update fields
    for field, value in attendance_data.dict(exclude_unset=True).items():
        setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    
    return record




# Attendance endpoints
@router.get("/attendance", response_model=List[AttendanceRecordSchema])
async def get_attendance_records(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    employee_id: Optional[int] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get attendance records with optional filters."""
    
    query = db.query(AttendanceRecord).filter(
        AttendanceRecord.company == current_admin.company
    )
    
    if date_from:
        query = query.filter(AttendanceRecord.date >= date_from)
    if date_to:
        query = query.filter(AttendanceRecord.date <= date_to)
    if employee_id:
        query = query.filter(AttendanceRecord.employee_id == employee_id)
    
    attendance_records = query.order_by(AttendanceRecord.date.desc()).all()
    
    return attendance_records


@router.get("/attendance/today")
async def get_today_attendance(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get today's attendance records."""
    
    today = datetime.now().date()
    
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.company == current_admin.company,
        AttendanceRecord.date >= today
    ).all()
    
    # Summary statistics
    total_employees = len(records)
    present_count = len([r for r in records if r.status == "present"])
    absent_count = len([r for r in records if r.status == "absent"])
    
    return {
        "records": records,
        "summary": {
            "total_employees": total_employees,
            "present": present_count,
            "absent": absent_count,
            "attendance_rate": (present_count / total_employees * 100) if total_employees > 0 else 0
        }
    }




# Ticket management endpoints
@router.get("/tickets", response_model=List[TicketResponse])
async def get_tickets(
    status_filter: Optional[str] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get tickets submitted to the admin."""
    
    query = db.query(Ticket).options(joinedload(Ticket.employee)).filter(
        Ticket.admin_id == current_admin.id
    )
    
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    # Add employee name to response
    ticket_responses = []
    for ticket in tickets:
        ticket_data = TicketResponse.from_orm(ticket)
        ticket_data.employee_name = ticket.employee.name
        ticket_responses.append(ticket_data)
    
    return ticket_responses



@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: int,
    ticket_data: TicketUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update ticket status."""
    
    ticket = db.query(Ticket).filter(
        and_(
            Ticket.id == ticket_id,
            Ticket.admin_id == current_admin.id
        )
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    ticket.status = ticket_data.status
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    
    return ticket

# Admin profile endpoints
@router.get("/profile", response_model=AdminResponse)
async def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin)
):
    """Get admin profile."""
    return current_admin

@router.put("/profile", response_model=AdminResponse)
async def update_admin_profile(
    profile_data: AdminProfileUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update admin profile."""
    
    # Update profile fields
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(current_admin, field, value)
    
    db.commit()
    db.refresh(current_admin)
    
    return current_admin

@router.put("/profile/password")
async def update_admin_password(
    password_data: AdminPasswordUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update admin password."""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_admin.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/admin/camera-stream")
async def video_stream():
    """Stream video feed to frontend with improved error handling"""
    
    if not recognition_service.is_running:
        raise HTTPException(status_code=400, detail="Recognition system not running")
    
    async def generate_frames():
        """Async generator for video frames"""
        frame_count = 0
        consecutive_failures = 0
        max_failures = 30  # Stop after 30 consecutive failures (~1 second at 30fps)
        
        try:
            while recognition_service.is_running and consecutive_failures < max_failures:
                # Get frame data from service
                frame_data = recognition_service.get_latest_frame()
                
                if frame_data is not None and 'frame' in frame_data:
                    frame = frame_data['frame']  # Extract the actual frame
                    
                    try:
                        # Resize frame for streaming efficiency (optional)
                        height, width = frame.shape[:2]
                        if width > 1280:  # Limit max width for streaming
                            scale = 1280 / width
                            new_width = 1280
                            new_height = int(height * scale)
                            frame = cv2.resize(frame, (new_width, new_height))
                        
                        # Encode frame as JPEG with quality control
                        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]  # Slightly higher quality
                        ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                        
                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n'
                                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' + 
                                   frame_bytes + b'\r\n')
                            
                            consecutive_failures = 0  # Reset failure counter
                            frame_count += 1
                        else:
                            consecutive_failures += 1
                            logger.warning(f"Frame encoding failed, attempt {consecutive_failures}")
                    
                    except Exception as e:
                        consecutive_failures += 1
                        logger.error(f"Error processing frame: {e}")
                else:
                    consecutive_failures += 1
                    if consecutive_failures % 10 == 0:  # Log every 10 failures
                        logger.warning(f"No frame available, consecutive failures: {consecutive_failures}")
                
                # Control frame rate - use asyncio.sleep for better async performance
                await asyncio.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
        finally:
            logger.info(f"Stream ended. Total frames: {frame_count}, Final failures: {consecutive_failures}")
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )

@router.get("/admin/camera-preview-frame")
async def get_preview_frame():
    """Get single frame for preview with enhanced error handling"""
    
    if not recognition_service.is_running:
        raise HTTPException(status_code=400, detail="Recognition system not running")
    
    if not recognition_service.frame_ready:
        raise HTTPException(status_code=503, detail="Camera initializing, please wait")
    
    try:
        # Get frame data from service
        frame_data = recognition_service.get_latest_frame()
        if frame_data is None or 'frame' not in frame_data:
            raise HTTPException(status_code=404, detail="No frame available")
        
        frame = frame_data['frame']  # Extract the actual frame
        
        # Optional: Resize frame for preview
        height, width = frame.shape[:2]
        if width > 800:  # Smaller size for single frame preview
            scale = 800 / width
            new_width = 800
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Encode frame with optimized settings
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 90]
        ret, buffer = cv2.imencode('.jpg', frame, encode_params)
        
        if not ret:
            raise HTTPException(status_code=500, detail="Frame encoding failed")
        
        # Convert to base64
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "frame": f"data:image/jpeg;base64,{frame_base64}",
            "timestamp": frame_data.get('timestamp', recognition_service.get_current_time()).isoformat(),
            "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
            "employees_loaded": len(recognition_service.known_face_names),
            "frame_number": frame_data.get('frame_number', 0),
            "fps": frame_data.get('fps', 0)
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error getting preview frame: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/admin/camera-status")
async def get_camera_status():
    """Get detailed camera and recognition status"""
    try:
        status = recognition_service.get_status()
        
        # Add additional status information
        additional_info = {
            "blink_counts": dict(recognition_service.person_blink_count),
            "last_detections": {
                name: time.isoformat() if time else None 
                for name, time in recognition_service.last_detection_time.items()
            },
            "active_employees": len(recognition_service.attendance_employee_ids),
            "blink_threshold": recognition_service.BLINK_THRESHOLD,
            "checkout_delay_minutes": recognition_service.CHECKOUT_DELAY_MINUTES
        }
        
        return {**status, **additional_info}
        
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/admin/camera-settings")
async def update_camera_settings(settings: dict):
    """Update camera settings dynamically"""
    try:
        # Update blink threshold if provided
        if "blink_threshold" in settings:
            threshold = int(settings["blink_threshold"])
            if 1 <= threshold <= 20:
                recognition_service.BLINK_THRESHOLD = threshold
            else:
                raise HTTPException(status_code=400, detail="Blink threshold must be between 1 and 20")
        
        # Update checkout delay if provided
        if "checkout_delay_minutes" in settings:
            delay = int(settings["checkout_delay_minutes"])
            if 1 <= delay <= 60:
                recognition_service.CHECKOUT_DELAY_MINUTES = delay
            else:
                raise HTTPException(status_code=400, detail="Checkout delay must be between 1 and 60 minutes")
        
        return {
            "message": "Settings updated successfully",
            "current_settings": {
                "blink_threshold": recognition_service.BLINK_THRESHOLD,
                "checkout_delay_minutes": recognition_service.CHECKOUT_DELAY_MINUTES
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid setting value: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating camera settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

# Optional: WebSocket endpoint for real-time updates
@router.websocket("/admin/camera-websocket")
async def camera_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time camera feed and status updates"""
    await websocket.accept()
    
    try:
        # Add client to streaming set
        recognition_service.streaming_clients.add(websocket)
        
        while recognition_service.is_running:
            try:
                # Send frame data
                frame_data = recognition_service.get_latest_frame()
                if frame_data is not None and 'frame' in frame_data:
                    frame = frame_data['frame']  # Extract the actual frame
                    
                    # Encode frame
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send frame with status
                        await websocket.send_json({
                            "type": "frame",
                            "data": f"data:image/jpeg;base64,{frame_base64}",
                            "timestamp": frame_data.get('timestamp', recognition_service.get_current_time()).isoformat(),
                            "blink_counts": dict(recognition_service.person_blink_count),
                            "frame_number": frame_data.get('frame_number', 0),
                            "fps": frame_data.get('fps', 0)
                        })
                
                await asyncio.sleep(0.1)  # 10 FPS for WebSocket
                
            except Exception as e:
                logger.error(f"WebSocket frame error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove client from streaming set
        recognition_service.streaming_clients.discard(websocket)
        try:
            await websocket.close()
        except:
            pass